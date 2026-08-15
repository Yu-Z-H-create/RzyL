import aiohttp
import asyncio
import logging
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
logger = logging.getLogger(__name__)


async def ai_match(message: str, keywords: dict[str, list[str]]) -> list[str]:
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
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    response_json = await response.json()
                    if response_json["choices"][0]["finish_reason"] == "stop":
                        result = response_json["choices"][0]["message"]["content"].strip()
                    else:
                        result = "NONE"
    except Exception as e:
        logger.error(f"AI匹配请求失败: {e}")
        return []

    if result == "NONE":
        return []

    keywords_found = [k.strip() for k in result.split(",")]
    return keywords_found