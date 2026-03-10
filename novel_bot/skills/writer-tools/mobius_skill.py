from __future__ import annotations

from typing import Optional
from loguru import logger

try:
    from novel_bot.agent.mobius_adapter import run_outline, run_setting_pack
except Exception as e:
    # Delay import errors until function call
    run_outline = None  # type: ignore
    run_setting_pack = None  # type: ignore
    logger = logger


def generate_outline_via_mobius(setting_path: str, output: str = "mobius_output", dry_run: bool = True, end_chapter: Optional[int] = None) -> dict:
    """通过 Mobius 生成全书概要（outline）。

    返回 dict: {"ok": bool, "message": str}
    """
    if run_outline is None:
        return {"ok": False, "message": "Mobius adapter 未就绪（请确保 novel_bot/agent/mobius_adapter.py 存在且可导入）。"}
    try:
        run_outline(setting_path, output=output, dry_run=dry_run, end_chapter=end_chapter)
        return {"ok": True, "message": f"Outline written to {output}"}
    except Exception as e:
        return {"ok": False, "message": str(e)}


def generate_setting_pack_via_mobius(setting_path: str, output: str = "mobius_output", dry_run: bool = True) -> dict:
    if run_setting_pack is None:
        return {"ok": False, "message": "Mobius adapter 未就绪（请确保 novel_bot/agent/mobius_adapter.py 存在且可导入）。"}
    try:
        run_setting_pack(setting_path, output=output, dry_run=dry_run)
        return {"ok": True, "message": f"Setting pack written to {output}"}
    except Exception as e:
        return {"ok": False, "message": str(e)}


if __name__ == "__main__":
    print(generate_outline_via_mobius("workspace/PROJECT_START.md", output="mobius_output", dry_run=True, end_chapter=3))
