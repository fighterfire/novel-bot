from __future__ import annotations

import sys
import argparse
from pathlib import Path
from typing import Optional


def _ensure_mobius_on_path() -> None:
    """将 mobius 源目录加入 sys.path，便于 import mobius 模块。"""
    here = Path(__file__).resolve()
    project_root = here.parents[1]
    mobius_src = project_root / "external" / "mobius" / "src"
    if not mobius_src.exists():
        raise FileNotFoundError(f"Mobius 源目录未找到: {mobius_src}")
    mobius_src_str = str(mobius_src)
    if mobius_src_str not in sys.path:
        sys.path.insert(0, mobius_src_str)


def _resolve_path(path: str, workspace: Optional[str] = None, check_exists: bool = True) -> str:
    """解析路径，支持相对路径和绝对路径。
    
    如果 path 是相对路径且 workspace 提供，则将其转换为绝对路径。
    """
    p = Path(path)
    
    if p.is_absolute():
        if check_exists and not p.exists():
            raise FileNotFoundError(f"文件不存在: {path}")
        return str(p)
    
    if workspace:
        workspace_path = Path(workspace)
        full_path = workspace_path / path
        if not check_exists or full_path.exists():
            return str(full_path)
    
    if check_exists and not p.exists():
        available_files = []
        if workspace:
            workspace_path = Path(workspace)
            for pattern in ["*.md", "*.yaml", "*.yml"]:
                available_files.extend([f.name for f in workspace_path.glob(pattern)])
        
        hint = f"可用文件: {', '.join(available_files[:10])}" if available_files else "请检查工作目录"
        raise FileNotFoundError(
            f"文件不存在: {path}\n"
            f"工作目录: {workspace or '未指定'}\n"
            f"{hint}"
        )
    
    return str(p.resolve())


def run_outline(
    setting_path: str,
    output: str = "output",
    dry_run: bool = True,
    end_chapter: Optional[int] = None,
    workspace: Optional[str] = None,
) -> str:
    """以编程方式调用 Mobius 的 `cmd_outline`。

    参数:
    - `setting_path`: 启动文档（Markdown/YAML）路径，支持相对路径
    - `output`: 输出目录
    - `dry_run`: 是否为离线模式（不调用 LLM）
    - `end_chapter`: 可选，生成到第几章
    - `workspace`: 工作目录路径，用于解析相对路径
    """
    _ensure_mobius_on_path()
    
    try:
        resolved_setting = _resolve_path(setting_path, workspace, check_exists=True)
        resolved_output = _resolve_path(output, workspace, check_exists=False)
    except FileNotFoundError as e:
        return f"错误: {e}"
    
    import mobius.main as mobius_main

    ns = argparse.Namespace()
    ns.setting = resolved_setting
    ns.output = resolved_output
    ns.dry_run = bool(dry_run)
    ns.end_chapter = str(end_chapter) if end_chapter is not None else ""

    try:
        mobius_main.cmd_outline(ns)
        return f"大纲生成完成: {resolved_output}"
    except SystemExit:
        pass
    except Exception as e:
        return f"大纲生成失败: {e}"
    
    return f"大纲生成完成: {resolved_output}"


def run_setting_pack(
    setting_path: str,
    output: str = "output",
    dry_run: bool = True,
    workspace: Optional[str] = None,
) -> str:
    """以编程方式调用 Mobius 的 `cmd_setting_pack`。
    
    参数:
    - `setting_path`: 启动文档（Markdown/YAML）路径，支持相对路径
    - `output`: 输出目录
    - `dry_run`: 是否为离线模式（不调用 LLM）
    - `workspace`: 工作目录路径，用于解析相对路径
    """
    _ensure_mobius_on_path()
    
    try:
        resolved_setting = _resolve_path(setting_path, workspace, check_exists=True)
        resolved_output = _resolve_path(output, workspace, check_exists=False)
    except FileNotFoundError as e:
        return f"错误: {e}"
    
    import mobius.main as mobius_main

    ns = argparse.Namespace()
    ns.setting = resolved_setting
    ns.output = resolved_output
    ns.dry_run = bool(dry_run)

    try:
        mobius_main.cmd_setting_pack(ns)
        return f"设定集生成完成: {resolved_output}"
    except SystemExit:
        pass
    except Exception as e:
        return f"设定集生成失败: {e}"
    
    return f"设定集生成完成: {resolved_output}"


def example_usage():
    print("示例: 调用 outline（离线模式）")
    run_outline("workspace/PROJECT_START.md", output="mobius_output", dry_run=True)
