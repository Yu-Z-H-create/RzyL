import nonebot
from pathlib import Path
from .keywords import KEYWORDS

config = nonebot.get_driver().config

# 允许使用本插件的群聊列表，留空表示所有群聊都可以使用
_raw = getattr(config, 'dawu2_allowed_groups', None)
if isinstance(_raw, str) and _raw.strip():
    ALLOWED_GROUPS = [int(g.strip()) for g in _raw.split(",") if g.strip().isdigit()]
else:
    ALLOWED_GROUPS = []

def get_image_path(keyword: str) -> Path:
    return Path.cwd() / "src" / "asserts" / "dawu2" / f"{keyword}.jpg"