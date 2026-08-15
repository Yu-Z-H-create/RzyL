import random
from nonebot import require
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from pathlib import Path

from .keywords import (
    Entity,
    load_categories,
    load_entities,
    load_compounds,
    compound_visible,
)
from .random_text import load_random_text as try_load_random_text

require("nonebot_plugin_alconna")

from nonebot_plugin_alconna import Alconna, Args, Match, on_alconna

__plugin_meta__ = PluginMetadata(
    name="彩蛋插件",
    description="迪士尼角色彩蛋查询与随机文本",
    usage="发送 彩蛋 <角色名> 查询图片；发送 彩蛋 ls 查看所有可用彩蛋",
    type="application",
    supported_adapters={"~onebot.v11"},
)

EASTER_EGG_IMAGE_DIR = Path(__file__).parent.parent.parent / "asserts" / "easter_egg"

SUPPORTED_IMAGE_EXTENSIONS = (
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif",
)

_collectors = (".ipynb_checkpoints", "__pycache__")


def _list_images(directory: Path) -> list[Path]:
    """列出目录内受支持的图片文件（跳过隐藏项与缓存目录）。"""
    return [
        f for f in directory.iterdir()
        if f.is_file()
        and f.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
        and not f.name.startswith(".")
        and f.parent.name not in _collectors
    ]


def _resolve_entity_dir(entity: Entity) -> Path:
    """根据个体定位其资源目录：类内个体在 easter_egg/<category>/<key>，顶层个体在 easter_egg/<key>。"""
    if entity.category is not None:
        return EASTER_EGG_IMAGE_DIR / entity.category / entity.key
    return EASTER_EGG_IMAGE_DIR / entity.key


def resolve_entity_image(entity: Entity) -> Path | None:
    """解析个体的图片（个体查询一律只输出一张）。

    mode="file"：单照片个体，返回唯一文件（探测各种扩展名）；
    mode="dir"：多照片个体，在该个体目录内随机挑一张。
    """
    base = _resolve_entity_dir(entity)

    if entity.mode == "dir":
        if base.is_dir():
            images = _list_images(base)
            if images:
                return random.choice(images)
        return None

    # mode == "file"：base 是「目录/key」，探测 base + 各扩展名
    for ext in SUPPORTED_IMAGE_EXTENSIONS:
        path = Path(f"{base}{ext}")
        if path.is_file():
            return path
    return None


def find_entities(text: str, entities: dict[str, Entity]) -> list[Entity]:
    """按别名子串匹配，同一输入可命中多个个体。"""
    found: list[Entity] = []
    for entity in entities.values():
        if any(alias in text for alias in entity.aliases):
            found.append(entity)
    return found


def find_compounds(text: str, compounds: dict[str, "Compound"], entities: dict[str, Entity]) -> list[tuple[str, list[Entity]]]:
    """匹配复合体，返回 (compound_key, [可见的 target 个体])。"""
    found = []
    for key, compound in compounds.items():
        if any(alias in text for alias in compound.aliases):
            if compound_visible(compound, entities):
                targets = [entities[t] for t in compound.targets if t in entities]
                found.append((key, targets))
    return found


caidan = on_alconna(
    Alconna("彩蛋", Args["name", str]),
    priority=1,
    block=True,
)


async def _resolve_image_or_none(entity: Entity) -> Path | None:
    return resolve_entity_image(entity)


@caidan.handle()
async def _(name: Match[str]):
    if not name.available:
        await caidan.finish("请输入名称，例如: 彩蛋 玲娜贝儿")
        return

    raw_text = name.result.strip()

    entities = load_entities()
    compounds = load_compounds()

    # 彩蛋 ls: 按类分组列出所有可见彩蛋
    if raw_text == "ls":
        categories = load_categories()
        output_lines: list[str] = []

        # 顶层个体（无 category）
        top_entities = [e for e in entities.values() if e.category is None]
        if top_entities:
            output_lines.append("[顶层] " + ", ".join(e.aliases[0] for e in top_entities))

        # 各类内个体
        for cat_key, cat in categories.items():
            if not cat.enabled:
                continue
            members = [e for e in entities.values() if e.category == cat_key]
            if members:
                output_lines.append(
                    f"[{cat.display}] " + ", ".join(e.aliases[0] for e in members)
                )

        # 复合体（可见的）
        visible_compounds = [
            c for c in compounds.values() if compound_visible(c, entities)
        ]
        if visible_compounds:
            output_lines.append(
                "[组合] " + ", ".join(c.aliases[0] for c in visible_compounds)
            )

        if not output_lines:
            await caidan.finish("暂无可用彩蛋")
            return
        await caidan.finish("\n".join(output_lines))
        return

    # 复合体匹配（优先，因为复合体别名可能与个体别名重叠）
    compound_matches = find_compounds(raw_text, compounds, entities)
    # 个体匹配
    entity_matches = find_entities(raw_text, entities)

    if not compound_matches and not entity_matches:
        await caidan.finish(f"未找到匹配的彩蛋: {raw_text}")
        return

    messages = []

    for _, targets in compound_matches:
        for target in targets:
            path = await _resolve_image_or_none(target)
            if path:
                messages.append(f"{target.aliases[0]}:")
                messages.append(MessageSegment.image(path))
            else:
                messages.append(f"{target.aliases[0]}: 图片文件不存在")

    for entity in entity_matches:
        path = await _resolve_image_or_none(entity)
        if path:
            messages.append(f"{entity.aliases[0]}:")
            messages.append(MessageSegment.image(path))
        else:
            messages.append(f"{entity.aliases[0]}: 图片文件不存在")

    if random_text := try_load_random_text():
        messages.append(random_text)

    await caidan.finish(Message(messages))