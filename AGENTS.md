# Repository Guidelines

## Project Structure & Module Organization

This repository is a Python 3.11 NoneBot2 QQ bot for querying physics experiment images. The bot entry point is `bot.py`, which loads plugins from `src/plugins/`. The main feature plugin is `src/plugins/dawu/`: `__init__.py` contains command handling, `config.py` handles configuration and image paths, `ai_match.py` contains async AI fuzzy matching, and text resources live in `sentences.txt` and `question.txt`. Static experiment images and keyword data are stored under `src/asserts/dawu/`. The `src/plugins/echo/` directory is a small example plugin.

## Build, Test, and Development Commands

- `uv sync` installs dependencies from `pyproject.toml` and `uv.lock`.
- `uv run bot.py` starts the local bot process.
- `uv run pyright` runs static type checking using `pyrightconfig.json`.

No formal test suite is currently present. When changing behavior, verify with `uv run pyright` and manual command checks through the bot where practical.

## Coding Style & Naming Conventions

Use idiomatic Python with 4-space indentation, type hints where useful, and async APIs for network or bot operations. Keep plugin modules focused: command routing belongs in `__init__.py`, configuration in `config.py`, and external API logic in `ai_match.py`. Use `snake_case` for functions, variables, and module names; use `UPPER_SNAKE_CASE` for constants such as keyword maps or limits. Preserve existing Chinese command text and user-facing messages unless the task specifically changes bot wording.

## Testing Guidelines

Add tests only if a testing framework is introduced or existing tests are added nearby. For plugin changes, manually exercise key paths: exact keyword match, AI fallback, `大雾1 ls`, `大雾1 help`, and group filtering if configuration changes. Keep image/resource names aligned with keyword keys so lookup behavior remains predictable.

## Commit & Pull Request Guidelines

Git history uses Conventional Commit-style messages, often scoped, such as `feat(dawu): 更新关键词` or `fix: 更新API基础URL`. Follow this pattern with concise summaries. Pull requests should describe the behavior change, list verification steps, link related issues when available, and include screenshots or bot output examples for user-visible responses.

## Security & Configuration Tips

Do not commit real secrets. Copy `.env.secret.temple` to `.env.secret` locally and fill `BASE_URL`, `API_KEY`, and model settings. Treat `.env`, `.env.secret`, and API responses as sensitive when sharing logs.
