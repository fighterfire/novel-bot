# Mobius 集成使用指南

本文件说明如何在本项目中使用已复制的 Mobius v2.1 源码。

前提：
- 已把 Mobius 源码放到 `novel_bot/external/mobius`（包含 `src` 目录）
- `novel_bot/agent/mobius_adapter.py` 已存在（用于把 Mobius 源加入 `sys.path` 并调用其 CLI 函数）

快速示例（离线，不调用 LLM）：

```powershell
python -c "from novel_bot.skills.writer_tools.mobius_skill import generate_outline_via_mobius; print(generate_outline_via_mobius('workspace/PROJECT_START.md', output='mobius_output', dry_run=True, end_chapter=3))"
```

把 Mobius 功能作为 agent 工具调用：
- agent 的 `ToolRegistry` 会在运行时尝试注册 `mobius_generate_outline` 与 `mobius_generate_setting_pack`，只要 `novel_bot/agent/mobius_adapter.py` 可导入。

真实调用模型时：
- 设定正确的环境变量（如 `OPENAI_API_KEY` / `MINIMAX_API_KEY`），并将 `dry_run=False`。

如果遇到问题：
- 检查 `novel_bot/external/mobius/src` 是否完整。
- 检查 Python 依赖（Mobius 的 `pyproject.toml` 或 `requirements.txt` 中的依赖）。
