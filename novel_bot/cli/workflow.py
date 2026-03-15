import typer
import asyncio
import os
import sys
from typing import Optional
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from enum import Enum

from novel_bot.agent.agents.workflow import ChapterWorkflow, WorkflowConfig, WorkflowPhase
from novel_bot.agent.agents.reviewer import ReviewVerdict
from novel_bot.agent.checkpoint import (
    CheckpointManager, CheckpointConfig, CheckpointType, Checkpoint
)
from novel_bot.agent.bible import BibleManager
from novel_bot.config.settings import settings

workflow_app = typer.Typer()
console = Console()


class PauseAction(Enum):
    CONTINUE = "continue"
    SKIP = "skip"
    STOP = "stop"
    EDIT = "edit"


class InteractiveWorkflow:
    def __init__(
        self,
        workspace_path: str,
        checkpoint_config: Optional[CheckpointConfig] = None,
        workflow_config: Optional[WorkflowConfig] = None,
    ):
        self.workspace_path = Path(workspace_path)
        self.checkpoint_config = checkpoint_config or CheckpointConfig(
            enabled=True,
            require_confirmation=True,
            auto_continue_after_seconds=0,
        )
        self.workflow_config = workflow_config or WorkflowConfig(
            max_revisions=3,
            min_review_score=35.0,
            auto_rewrite_threshold=25.0,
            enable_polish=True,
            enable_archive=True,
        )
        
        self.checkpoint_manager = CheckpointManager(workspace_path, self.checkpoint_config)
        self.bible_manager = BibleManager(workspace_path)
        self.workflow: Optional[ChapterWorkflow] = None
        
        self._paused = False
        self._stop_requested = False
        self._skip_current_checkpoint = False

    async def run_chapter(self, chapter_num: int) -> bool:
        self.workflow = ChapterWorkflow(str(self.workspace_path), self.workflow_config)
        
        console.print(Panel.fit(
            f"[bold cyan]开始创作第 {chapter_num} 章[/bold cyan]",
            border_style="cyan"
        ))
        
        try:
            await self._run_planning_phase(chapter_num)
            if self._stop_requested:
                return False
            
            await self._run_writing_phase(chapter_num)
            if self._stop_requested:
                return False
            
            while True:
                await self._run_review_phase(chapter_num)
                if self._stop_requested:
                    return False
                
                state = self.workflow.state
                if not state or not state.review_result:
                    break
                
                verdict = state.review_result.verdict
                
                if verdict == ReviewVerdict.PASS:
                    break
                elif verdict == ReviewVerdict.NEEDS_REVISION:
                    if state.revision_count >= self.workflow_config.max_revisions:
                        console.print("[yellow]达到最大修改次数[/yellow]")
                        break
                    await self._run_revision_phase(chapter_num)
                elif verdict == ReviewVerdict.NEEDS_REWRITE:
                    if state.revision_count >= self.workflow_config.max_revisions:
                        console.print("[red]达到最大修改次数，停止创作[/red]")
                        return False
                    await self._run_rewrite_phase(chapter_num)
                
                if self._stop_requested:
                    return False
            
            if self.workflow_config.enable_polish:
                await self._run_polish_phase(chapter_num)
                if self._stop_requested:
                    return False
            
            if self.workflow_config.enable_archive:
                await self._run_archive_phase(chapter_num)
            
            console.print(Panel.fit(
                f"[bold green]第 {chapter_num} 章创作完成！[/bold green]",
                border_style="green"
            ))
            
            return True
            
        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")
            return False

    async def _run_planning_phase(self, chapter_num: int):
        checkpoint = self._create_checkpoint(chapter_num, CheckpointType.BEFORE_PLANNING, "场景规划前")
        
        if await self._handle_checkpoint(checkpoint, "即将开始场景规划"):
            self.workflow.state.phase = WorkflowPhase.PLANNING
            console.print("[dim]Phase: 场景规划 (Planner)[/dim]")
            await self.workflow._phase_planning()
            
            checkpoint = self._create_checkpoint(
                chapter_num, CheckpointType.AFTER_PLANNING,
                "场景规划完成",
                data={"plan_content": self.workflow.state.plan_content[:500]}
            )
            await self._handle_checkpoint(checkpoint, "场景规划已完成，是否继续？")

    async def _run_writing_phase(self, chapter_num: int):
        checkpoint = self._create_checkpoint(chapter_num, CheckpointType.BEFORE_WRITING, "章节写作前")
        
        if await self._handle_checkpoint(checkpoint, "即将开始章节写作"):
            await self.workflow._phase_writing()
            
            checkpoint = self._create_checkpoint(
                chapter_num, CheckpointType.AFTER_WRITING,
                "章节写作完成",
                data={"word_count": len(self.workflow.state.draft_content)}
            )
            await self._handle_checkpoint(checkpoint, "章节写作已完成，是否继续审查？")

    async def _run_review_phase(self, chapter_num: int):
        checkpoint = self._create_checkpoint(chapter_num, CheckpointType.BEFORE_REVIEW, "质量审查前")
        
        if await self._handle_checkpoint(checkpoint, "即将开始质量审查"):
            await self.workflow._phase_reviewing()
            
            result = self.workflow.state.review_result
            checkpoint = self._create_checkpoint(
                chapter_num, CheckpointType.AFTER_REVIEW,
                f"审查完成 - 总分: {result.total_score}/50",
                data={
                    "total_score": result.total_score,
                    "verdict": result.verdict.value,
                    "issues": result.issues[:3],
                }
            )
            await self._handle_checkpoint(checkpoint, f"审查完成，裁决: {result.verdict.value}")

    async def _run_revision_phase(self, chapter_num: int):
        checkpoint = self._create_checkpoint(chapter_num, CheckpointType.BEFORE_REVISION, "修改前")
        
        if await self._handle_checkpoint(checkpoint, "即将根据审查意见修改"):
            await self.workflow._phase_revising()

    async def _run_rewrite_phase(self, chapter_num: int):
        checkpoint = self._create_checkpoint(chapter_num, CheckpointType.BEFORE_REVISION, "重写前")
        
        if await self._handle_checkpoint(checkpoint, "评分过低，需要重写"):
            await self.workflow._phase_rewriting()

    async def _run_polish_phase(self, chapter_num: int):
        checkpoint = self._create_checkpoint(chapter_num, CheckpointType.BEFORE_POLISH, "润色前")
        
        if await self._handle_checkpoint(checkpoint, "即将开始润色"):
            await self.workflow._phase_polishing()

    async def _run_archive_phase(self, chapter_num: int):
        await self.workflow._phase_archiving()

    def _create_checkpoint(
        self,
        chapter_num: int,
        checkpoint_type: CheckpointType,
        description: str,
        data: Optional[dict] = None,
    ) -> Checkpoint:
        return self.checkpoint_manager.create_checkpoint(
            chapter_num=chapter_num,
            checkpoint_type=checkpoint_type,
            data=data or {},
            description=description,
        )

    async def _handle_checkpoint(self, checkpoint: Checkpoint, message: str) -> bool:
        if not self.checkpoint_manager.should_pause(checkpoint.checkpoint_type):
            return True
        
        if self._skip_current_checkpoint:
            return True
        
        self._paused = True
        
        console.print(Panel(
            f"[bold yellow]⏸️ 检查点暂停[/bold yellow]\n\n{message}",
            border_style="yellow"
        ))
        
        while self._paused:
            action = await self._get_user_action(checkpoint)
            
            if action == PauseAction.CONTINUE:
                self.checkpoint_manager.confirm_checkpoint(checkpoint.id)
                self._paused = False
                return True
            elif action == PauseAction.SKIP:
                self._skip_current_checkpoint = True
                self._paused = False
                return True
            elif action == PauseAction.STOP:
                self._stop_requested = True
                self._paused = False
                return False
            elif action == PauseAction.EDIT:
                self._show_edit_options(checkpoint)
        
        return True

    async def _get_user_action(self, checkpoint: Checkpoint) -> PauseAction:
        console.print("\n[bold]请选择操作:[/bold]")
        console.print("  [1] 继续创作")
        console.print("  [2] 跳过此类型检查点")
        console.print("  [3] 查看详情")
        console.print("  [4] 停止创作")
        console.print("  [5] 编辑配置")
        
        choice = Prompt.ask("选择", choices=["1", "2", "3", "4", "5"], default="1")
        
        if choice == "1":
            return PauseAction.CONTINUE
        elif choice == "2":
            return PauseAction.SKIP
        elif choice == "3":
            self._show_checkpoint_details(checkpoint)
            return await self._get_user_action(checkpoint)
        elif choice == "4":
            if Confirm.ask("确定要停止创作吗？"):
                return PauseAction.STOP
            return await self._get_user_action(checkpoint)
        elif choice == "5":
            return PauseAction.EDIT
        
        return PauseAction.CONTINUE

    def _show_checkpoint_details(self, checkpoint: Checkpoint):
        console.print(Panel(
            f"""
[bold]检查点详情[/bold]

ID: {checkpoint.id}
章节: {checkpoint.chapter_num}
类型: {checkpoint.checkpoint_type.value}
时间: {checkpoint.timestamp}
描述: {checkpoint.description}
状态: {'已确认' if checkpoint.confirmed else '待确认'}
""",
            border_style="blue"
        ))
        
        if checkpoint.data:
            console.print("\n[bold]附加数据:[/bold]")
            for key, value in checkpoint.data.items():
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                console.print(f"  {key}: {value}")

    def _show_edit_options(self, checkpoint: Checkpoint):
        console.print(Panel(
            """
[bold]编辑选项[/bold]

[1] 禁用检查点暂停
[2] 启用自动继续 (设置秒数)
[3] 返回
""",
            border_style="green"
        ))
        
        choice = Prompt.ask("选择", choices=["1", "2", "3"], default="3")
        
        if choice == "1":
            self.checkpoint_config.require_confirmation = False
            console.print("[green]已禁用检查点暂停[/green]")
        elif choice == "2":
            seconds = Prompt.ask("输入自动继续秒数", default="30")
            try:
                self.checkpoint_config.auto_continue_after_seconds = int(seconds)
                console.print(f"[green]已设置 {seconds} 秒后自动继续[/green]")
            except ValueError:
                console.print("[red]无效的秒数[/red]")


@workflow_app.command("run")
def run_workflow(
    workspace: str = typer.Option(None, "--workspace", "-w", help="工作目录路径"),
    chapter: int = typer.Option(1, "--chapter", "-c", help="开始章节号"),
    end_chapter: int = typer.Option(1, "--end", "-e", help="结束章节号"),
    auto: bool = typer.Option(False, "--auto", "-a", help="自动模式，不暂停"),
    max_revisions: int = typer.Option(3, "--max-revisions", help="最大修改次数"),
):
    """启动交互式创作工作流"""
    workspace_path = workspace or settings.workspace_path
    
    if not Path(workspace_path).exists():
        console.print(f"[red]工作目录不存在: {workspace_path}[/red]")
        console.print("请先运行 'init' 命令创建工作目录")
        return
    
    checkpoint_config = CheckpointConfig(
        enabled=not auto,
        require_confirmation=not auto,
        auto_continue_after_seconds=0,
    )
    
    workflow_config = WorkflowConfig(
        max_revisions=max_revisions,
        min_review_score=35.0,
        auto_rewrite_threshold=25.0,
        enable_polish=True,
        enable_archive=True,
    )
    
    interactive = InteractiveWorkflow(
        workspace_path,
        checkpoint_config=checkpoint_config,
        workflow_config=workflow_config,
    )
    
    console.print(Panel.fit(
        f"[bold cyan]小说创作工作流[/bold cyan]\n"
        f"工作目录: {workspace_path}\n"
        f"章节范围: {chapter} - {end_chapter}\n"
        f"模式: {'自动' if auto else '交互式'}",
        border_style="cyan"
    ))
    
    for ch in range(chapter, end_chapter + 1):
        success = asyncio.run(interactive.run_chapter(ch))
        if not success:
            console.print(f"[red]第 {ch} 章创作失败或被中断[/red]")
            break
        
        if ch < end_chapter:
            if not Confirm.ask(f"\n是否继续创作第 {ch + 1} 章？"):
                break
    
    console.print("\n[bold green]工作流结束[/bold green]")


@workflow_app.command("checkpoints")
def checkpoints_cmd(
    workspace: str = typer.Option(None, "--workspace", "-w", help="工作目录路径"),
    clear: bool = typer.Option(False, "--clear", help="清除所有检查点"),
):
    """管理检查点"""
    workspace_path = workspace or settings.workspace_path
    
    if not Path(workspace_path).exists():
        console.print(f"[red]工作目录不存在: {workspace_path}[/red]")
        return
    
    manager = CheckpointManager(workspace_path)
    
    if clear:
        if Confirm.ask("确定要清除所有检查点吗？"):
            for cp in manager.list_checkpoints():
                manager.delete_checkpoint(cp["id"])
            console.print("[green]已清除所有检查点[/green]")
        return
    
    checkpoints_list = manager.list_checkpoints()
    
    if not checkpoints_list:
        console.print("[yellow]暂无检查点[/yellow]")
        return
    
    table = Table(title="检查点列表")
    table.add_column("ID", style="cyan")
    table.add_column("章节", style="green")
    table.add_column("类型", style="yellow")
    table.add_column("描述")
    table.add_column("状态", style="magenta")
    
    for cp in checkpoints_list:
        status = "✅ 已确认" if cp["confirmed"] else "⏳ 待确认"
        table.add_row(
            cp["id"],
            str(cp["chapter_num"]),
            cp["type"],
            cp["description"][:30],
            status,
        )
    
    console.print(table)


@workflow_app.command("bible")
def bible_cmd(
    workspace: str = typer.Option(None, "--workspace", "-w", help="工作目录路径"),
    show: str = typer.Option(None, "--show", help="显示内容: suspense/foreshadow/characters"),
):
    """查看故事圣经"""
    workspace_path = workspace or settings.workspace_path
    
    if not Path(workspace_path).exists():
        console.print(f"[red]工作目录不存在: {workspace_path}[/red]")
        return
    
    manager = BibleManager(workspace_path)
    
    if show == "suspense":
        suspenses = manager.get_active_suspenses()
        if suspenses:
            table = Table(title="活跃悬念")
            table.add_column("ID", style="cyan")
            table.add_column("描述")
            table.add_column("紧张度", style="yellow")
            table.add_column("计划回收")
            
            for s in suspenses:
                table.add_row(s.id, s.description[:30], s.tension.value, f"第{s.planned_resolve_chapter}章")
            
            console.print(table)
        else:
            console.print("[yellow]暂无活跃悬念[/yellow]")
    
    elif show == "foreshadow":
        foreshadows = manager.get_active_foreshadows()
        if foreshadows:
            table = Table(title="活跃伏笔")
            table.add_column("ID", style="cyan")
            table.add_column("描述")
            table.add_column("埋设方式", style="yellow")
            table.add_column("计划揭示")
            
            for f in foreshadows:
                table.add_row(f.id, f.description[:30], f.plant_method, f"第{f.planned_reveal_chapter}章")
            
            console.print(table)
        else:
            console.print("[yellow]暂无活跃伏笔[/yellow]")
    
    else:
        summary = manager.get_bible_summary()
        console.print(Panel(
            f"""
[bold]故事圣经摘要[/bold]

活跃悬念: {summary.get('active_suspenses', 0)}
已回收悬念: {summary.get('resolved_suspenses', 0)}
活跃伏笔: {summary.get('active_foreshadows', 0)}
已揭示伏笔: {summary.get('revealed_foreshadows', 0)}
角色数量: {summary.get('characters', 0)}
""",
            border_style="green"
        ))


if __name__ == "__main__":
    app()
