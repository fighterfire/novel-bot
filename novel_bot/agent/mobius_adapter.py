from __future__ import annotations

import sys
import argparse
from pathlib import Path
from typing import Optional


def _ensure_mobius_on_path() -> None:
    """将 mobius 源目录加入 sys.path，便于 import mobius 模块。"""
    # 计算路径：项目根/novel_bot/external/mobius/src
    here = Path(__file__).resolve()
    project_root = here.parents[1]
    mobius_src = project_root / "external" / "mobius" / "src"
    if not mobius_src.exists():
        raise FileNotFoundError(f"Mobius 源目录未找到: {mobius_src}")
    mobius_src_str = str(mobius_src)
    if mobius_src_str not in sys.path:
        sys.path.insert(0, mobius_src_str)


def run_outline(setting_path: str, output: str = "output", dry_run: bool = True, end_chapter: Optional[int] = None) -> None:
    """以编程方式调用 Mobius 的 `cmd_outline`。

    参数:
    - `setting_path`: 启动文档（Markdown/YAML）路径
    - `output`: 输出目录
    - `dry_run`: 是否为离线模式（不调用 LLM）
    - `end_chapter`: 可选，生成到第几章
    """
    _ensure_mobius_on_path()
    import mobius.main as mobius_main

    ns = argparse.Namespace()
    ns.setting = str(setting_path)
    ns.output = str(output)
    ns.dry_run = bool(dry_run)
    ns.end_chapter = str(end_chapter) if end_chapter is not None else ""

    return mobius_main.cmd_outline(ns)


def run_setting_pack(setting_path: str, output: str = "output", dry_run: bool = True) -> None:
    """以编程方式调用 Mobius 的 `cmd_setting_pack`。"""
    _ensure_mobius_on_path()
    import mobius.main as mobius_main

    ns = argparse.Namespace()
    ns.setting = str(setting_path)
    ns.output = str(output)
    ns.dry_run = bool(dry_run)

    return mobius_main.cmd_setting_pack(ns)


def example_usage():
    print("示例: 调用 outline（离线模式）")
    run_outline("workspace/PROJECT_START.md", output="mobius_output", dry_run=True)
