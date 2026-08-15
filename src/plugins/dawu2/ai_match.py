import asyncio
import json
import logging

import aiohttp
import nonebot

from .keywords import KEYWORDS

config = nonebot.get_driver().config

# 配置默认值
BASE_URL = getattr(config, 'base_url', "")
API_KEY = getattr(config, 'api_key', "")
MODEL_THINK = getattr(config, 'model_think', "")

url = f"{BASE_URL}/chat/completions"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

AI_SEMAPHORE = asyncio.Semaphore(8)
REQUEST_TIMEOUT = 60  # 秒

logger = logging.getLogger(__name__)

# 启动期配置校验：配置缺失尽早暴露，而不是每次查询失败才报
if not BASE_URL:
    logger.warning("AI 匹配配置缺失：BASE_URL 为空，AI 模糊匹配将不可用")
if not API_KEY:
    logger.warning("AI 匹配配置缺失：API_KEY 为空，AI 模糊匹配将不可用")
if not MODEL_THINK:
    logger.warning("AI 匹配配置缺失：MODEL_THINK 为空，AI 模糊匹配将不可用")


async def ai_match(message: str, keywords: dict[str, list[str]]) -> tuple[list[str], str | None]:
    """AI 模糊匹配，返回 (关键词列表, 错误原因)。

    错误原因为 None 表示流程正常完成（此时关键词列表可能为空，表示无匹配）；
    非 None 表示发生错误，值为机器可读原因标识：
      config / timeout / network / parse / http_<status> / unknown
    """
    # 配置不完整时快速失败，不发起请求
    if not BASE_URL or not API_KEY or not MODEL_THINK:
        logger.error("AI 匹配配置不完整，跳过请求（BASE_URL/API_KEY/MODEL_THINK 存在空值）")
        return [], "config"

    keywords_list = []
    for keyword, aliases in keywords.items():
        aliases_str = ", ".join(aliases)
        keywords_list.append(f"{keyword}: {aliases_str}")

    keywords_info = "\n".join(keywords_list)

    system_prompt = f"""你是一个关键词匹配助手。
任务：根据用户输入快速返回所有可能匹配的英文关键词，不要返回任何别名，如果用户的输入与物理实验毫无关系则直接返回NONE
方法：在第一次浏览关键词的过程中对每个关键词进行匹配，例如：'Introduction_and_Simple_Pendulum: 绪论, 单摆 - 不相关，...'，不要思考太多，不需要重新检查，浏览过后直接输出结果。规则：用户的输入与关键词的任意一个别名相关即认为匹配，多个用逗号分隔，无匹配返回NONE

关键词及其别名的列表如下：
{keywords_info}"""

    data = {
        "model": MODEL_THINK,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        "max_tokens": 4500,
        "temperature": 0.3
    }

    try:
        async with AI_SEMAPHORE:
            timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status != 200:
                        body = (await response.text())[:200]
                        logger.error(f"AI 匹配 API 返回 HTTP {response.status}: {body}")
                        return [], f"http_{response.status}"

                    response_json = await response.json()
                    choice = response_json["choices"][0]

                    if choice["finish_reason"] != "stop":
                        logger.warning(f"AI 匹配 finish_reason={choice['finish_reason']!r}，视为无匹配")
                        return [], None

                    result = choice["message"]["content"].strip()
    except asyncio.TimeoutError:
        logger.error(f"AI 匹配请求超时（>{REQUEST_TIMEOUT}s）")
        return [], "timeout"
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError, aiohttp.ContentTypeError) as e:
        logger.error(f"AI 匹配响应解析失败: {type(e).__name__}: {e}")
        return [], "parse"
    except aiohttp.ClientError as e:
        logger.error(f"AI 匹配网络错误: {e!r}")
        return [], "network"
    except Exception as e:
        logger.error(f"AI 匹配未预期错误: {type(e).__name__}: {e}")
        return [], "unknown"

    if result == "NONE":
        return [], None

    keywords_found = [k.strip() for k in result.split(",")]
    return keywords_found, None
