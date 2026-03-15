import asyncio
from typing import List, Dict, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
from rich.console import Console
from rich.markdown import Markdown

from novel_bot.agent.agents import AgentRole
from novel_bot.agent.agents.base import SubAgent, AgentResponse
from novel_bot.agent.agents.reviewer import ReviewResult, ReviewVerdict
from novel_bot.agent.memory import MemoryStore
from novel_bot.agent.provider import LLMProvider
from novel_bot.agent.checkpoint import CheckpointManager, CheckpointType, CheckpointConfig

console = Console()


class WorkflowPhase(Enum):
    INIT = "init"
    PLANNING = "planning"
    WRITING = "writing"
    REVIEWING = "reviewing"
    REVISING = "revising"
    POLISHING = "polishing"
    ARCHIVING = "archiving"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ChapterState:
    chapter_num: int
    phase: WorkflowPhase = WorkflowPhase.INIT
    plan_content: str = ""
    draft_content: str = ""
    review_result: Optional[ReviewResult] = None
    revision_count: int = 0
    polish_content: str = ""
    error_message: str = ""


@dataclass
class WorkflowConfig:
    max_revisions: int = 3
    min_review_score: float = 35.0
    auto_rewrite_threshold: float = 25.0
    enable_polish: bool = True
    enable_archive: bool = True
    enable_checkpoints: bool = True
    checkpoint_config: Optional[CheckpointConfig] = None


class ChapterWorkflow:
    def __init__(
        self,
        workspace_path: str,
        config: Optional[WorkflowConfig] = None,
    ):
        self.workspace_path = Path(workspace_path)
        self.config = config or WorkflowConfig()
        self.memory = MemoryStore(workspace_path)
        self.provider = LLMProvider()
        
        if self.config.enable_checkpoints:
            checkpoint_cfg = self.config.checkpoint_config or CheckpointConfig()
            self.checkpoint_manager = CheckpointManager(workspace_path, checkpoint_cfg)
        
        self.planner = SubAgent(AgentRole.PLANNER, self.workspace_path, self.provider)
        self.writer = SubAgent(AgentRole.WRITER, self.workspace_path, self.provider)
        self.reviewer = SubAgent(AgentRole.REVIEWER, self.workspace_path, self.provider)
        self.polisher = SubAgent(AgentRole.POLISHER, self.workspace_path, self.provider)
        
        self.state: Optional[ChapterState] = None
        self.history: List[Dict] = []

    def _create_checkpoint(self, checkpoint_type: CheckpointType, description: str = "", data: Optional[Dict] = None):
        if not self.config.enable_checkpoints or not hasattr(self, 'checkpoint_manager'):
            return None
        
        checkpoint = self.checkpoint_manager.create_checkpoint(
            chapter_num=self.state.chapter_num,
            checkpoint_type=checkpoint_type,
            description=description,
            data=data or {}
        )
        
        if self.checkpoint_manager.should_pause(checkpoint_type):
            console.print(f"[yellow]⏸ 检查点等待确认: {checkpoint_type.value}[/yellow]")
            self.checkpoint_manager.wait_for_confirmation(checkpoint)
        
        return checkpoint

    async def run(self, chapter_num: int) -> ChapterState:
        self.state = ChapterState(chapter_num=chapter_num)
        
        console.print(f"[bold cyan]开始第 {chapter_num} 章创作工作流[/bold cyan]")
        
        try:
            await self._phase_planning()
            await self._phase_writing()
            
            while True:
                await self._phase_reviewing()
                
                if self.state.review_result:
                    verdict = self.state.review_result.verdict
                    
                    if verdict == ReviewVerdict.PASS:
                        break
                    elif verdict == ReviewVerdict.NEEDS_REVISION:
                        if self.state.revision_count >= self.config.max_revisions:
                            console.print("[yellow]达到最大修改次数，继续下一阶段[/yellow]")
                            break
                        await self._phase_revising()
                    elif verdict == ReviewVerdict.NEEDS_REWRITE:
                        if self.state.revision_count >= self.config.max_revisions:
                            console.print("[red]达到最大修改次数，标记为失败[/red]")
                            self.state.phase = WorkflowPhase.FAILED
                            return self.state
                        await self._phase_rewriting()
            
            if self.config.enable_polish:
                await self._phase_polishing()
            
            if self.config.enable_archive:
                await self._phase_archiving()
            
            self.state.phase = WorkflowPhase.COMPLETED
            console.print(f"[bold green]第 {chapter_num} 章创作完成！[/bold green]")
            
        except Exception as e:
            logger.error(f"Workflow error: {e}")
            self.state.phase = WorkflowPhase.FAILED
            self.state.error_message = str(e)
        
        return self.state

    async def _phase_planning(self):
        self.state.phase = WorkflowPhase.PLANNING
        console.print(f"[dim]Phase: 场景规划 (Planner)[/dim]")
        
        instruction = f"为第 {self.state.chapter_num} 章创建详细的场景规划"
        
        context_parts = []
        
        outline = self.memory.read("bible/plot/outline.md")
        if outline:
            context_parts.append(f"大纲:\n{outline}")
        
        prev_chapter = self.state.chapter_num - 1
        if prev_chapter > 0:
            prev_content = self.memory.read(f"drafts/chapter_{prev_chapter:02d}.md")
            if prev_content:
                context_parts.append(f"前一章内容:\n{prev_content[:2000]}...")
        
        context = "\n\n".join(context_parts) if context_parts else None
        
        response = await self.planner.process(instruction, context)
        
        if response.success:
            self.state.plan_content = response.content
            console.print("[green]✓ 场景规划完成[/green]")
            self._create_checkpoint(
                CheckpointType.AFTER_PLANNING,
                description="规划阶段完成",
                data={"plan_content": self.state.plan_content[:500]}
            )
        else:
            raise Exception(f"场景规划失败: {response.content}")

    async def _phase_writing(self):
        self.state.phase = WorkflowPhase.WRITING
        console.print(f"[dim]Phase: 章节写作 (Writer)[/dim]")
        
        instruction = f"根据场景规划写作第 {self.state.chapter_num} 章"
        
        response = await self.writer.process(
            instruction,
            context=f"场景规划:\n{self.state.plan_content}"
        )
        
        if response.success:
            self.state.draft_content = response.content
            console.print("[green]✓ 章节写作完成[/green]")
            self._create_checkpoint(
                CheckpointType.AFTER_WRITING,
                description="写作阶段完成",
                data={"draft_content": self.state.draft_content[:500], "word_count": len(self.state.draft_content)}
            )
        else:
            raise Exception(f"章节写作失败: {response.content}")

    async def _phase_reviewing(self):
        self.state.phase = WorkflowPhase.REVIEWING
        console.print(f"[dim]Phase: 质量审查 (Reviewer)[/dim]")
        
        instruction = f"审查第 {self.state.chapter_num} 章的质量，使用10维度检查清单评分"
        
        response = await self.reviewer.process(
            instruction,
            context=f"章节内容:\n{self.state.draft_content}"
        )
        
        if response.success:
            self.state.review_result = self._parse_review_response(response.content)
            console.print(f"[green]✓ 审查完成 - 总分: {self.state.review_result.total_score}/50[/green]")
            console.print(f"  裁决: {self.state.review_result.verdict.value}")
            self._create_checkpoint(
                CheckpointType.AFTER_REVIEW,
                description=f"审查阶段完成 - 得分: {self.state.review_result.total_score}/50",
                data={
                    "total_score": self.state.review_result.total_score,
                    "verdict": self.state.review_result.verdict.value,
                    "dimension_scores": self.state.review_result.dimension_scores
                }
            )
        else:
            raise Exception(f"审查失败: {response.content}")

    async def _phase_revising(self):
        self.state.phase = WorkflowPhase.REVISING
        self.state.revision_count += 1
        console.print(f"[dim]Phase: 根据审查意见修改 (Writer) - 第 {self.state.revision_count} 次[/dim]")
        
        instruction = f"根据审查意见修改第 {self.state.chapter_num} 章"
        
        review_feedback = self._format_review_feedback(self.state.review_result)
        
        response = await self.writer.process(
            instruction,
            context=f"原内容:\n{self.state.draft_content}\n\n审查意见:\n{review_feedback}"
        )
        
        if response.success:
            self.state.draft_content = response.content
            console.print("[green]✓ 修改完成[/green]")
            self._create_checkpoint(
                CheckpointType.AFTER_REVISION,
                description=f"修改阶段完成 - 第 {self.state.revision_count} 次修改",
                data={"revision_count": self.state.revision_count}
            )
        else:
            raise Exception(f"修改失败: {response.content}")

    async def _phase_rewriting(self):
        self.state.phase = WorkflowPhase.WRITING
        self.state.revision_count += 1
        console.print(f"[dim]Phase: 重新写作 (Writer) - 第 {self.state.revision_count} 次[/dim]")
        
        instruction = f"重新写作第 {self.state.chapter_num} 章，避免之前的问题"
        
        review_feedback = self._format_review_feedback(self.state.review_result)
        
        response = await self.writer.process(
            instruction,
            context=f"场景规划:\n{self.state.plan_content}\n\n之前的问题:\n{review_feedback}"
        )
        
        if response.success:
            self.state.draft_content = response.content
            console.print("[green]✓ 重写完成[/green]")
        else:
            raise Exception(f"重写失败: {response.content}")

    async def _phase_polishing(self):
        self.state.phase = WorkflowPhase.POLISHING
        console.print(f"[dim]Phase: 润色优化 (Polisher)[/dim]")
        
        instruction = f"润色第 {self.state.chapter_num} 章，去除AI味，优化语言"
        
        response = await self.polisher.process(
            instruction,
            context=f"章节内容:\n{self.state.draft_content}"
        )
        
        if response.success:
            self.state.polish_content = response.content
            console.print("[green]✓ 润色完成[/green]")
            self._create_checkpoint(
                CheckpointType.AFTER_POLISH,
                description="润色阶段完成",
                data={"word_count": len(self.state.polish_content)}
            )
        else:
            console.print("[yellow]润色失败，使用原稿[/yellow]")
            self.state.polish_content = self.state.draft_content

    async def _phase_archiving(self):
        self.state.phase = WorkflowPhase.ARCHIVING
        console.print(f"[dim]Phase: 归档更新 (Planner)[/dim]")
        
        final_content = self.state.polish_content or self.state.draft_content
        
        instruction = f"更新故事圣经，记录第 {self.state.chapter_num} 章的重要信息"
        
        response = await self.planner.process(
            instruction,
            context=f"章节内容:\n{final_content}"
        )
        
        if response.success:
            console.print("[green]✓ 归档完成[/green]")
        else:
            console.print("[yellow]归档失败[/yellow]")

    def _parse_review_response(self, content: str) -> ReviewResult:
        import re
        
        scores = {}
        dimensions = [
            "情节连贯性", "角色一致性", "对话质量", "叙事节奏",
            "描写技巧", "情感表达", "悬念设置", "信息揭示",
            "语言风格", "整体质量"
        ]
        
        for dim in dimensions:
            pattern = rf"{dim}[：:]\s*(\d+)/?\d*"
            match = re.search(pattern, content)
            if match:
                scores[dim] = int(match.group(1))
        
        total_pattern = r"总分[：:]\s*(\d+(?:\.\d+)?)"
        total_match = re.search(total_pattern, content)
        total_score = float(total_match.group(1)) if total_match else sum(scores.values()) if scores else 35.0
        
        if "通过" in content and "需修改" not in content and "需重写" not in content:
            verdict = ReviewVerdict.PASS
        elif "需重写" in content or total_score < self.config.auto_rewrite_threshold:
            verdict = ReviewVerdict.NEEDS_REWRITE
        elif "需修改" in content or total_score < self.config.min_review_score:
            verdict = ReviewVerdict.NEEDS_REVISION
        else:
            verdict = ReviewVerdict.PASS if total_score >= self.config.min_review_score else ReviewVerdict.NEEDS_REVISION
        
        issues = re.findall(r"主要问题[^\n]*\n((?:\d+\.[^\n]+\n?)+)", content)
        issue_list = []
        if issues:
            for issue_block in issues:
                issue_list.extend(re.findall(r"\d+\.\s*([^\n]+)", issue_block))
        
        return ReviewResult(
            total_score=total_score,
            verdict=verdict,
            dimension_scores=scores,
            issues=issue_list,
            raw_content=content,
        )

    def _format_review_feedback(self, result: ReviewResult) -> str:
        parts = [f"总分: {result.total_score}/50"]
        
        if result.dimension_scores:
            parts.append("\n维度评分:")
            for dim, score in result.dimension_scores.items():
                parts.append(f"  - {dim}: {score}/5")
        
        if result.issues:
            parts.append("\n主要问题:")
            for i, issue in enumerate(result.issues, 1):
                parts.append(f"  {i}. {issue}")
        
        return "\n".join(parts)

    def get_final_content(self) -> str:
        if not self.state:
            return ""
        return self.state.polish_content or self.state.draft_content

    def get_workflow_summary(self) -> Dict[str, Any]:
        if not self.state:
            return {}
        
        return {
            "chapter_num": self.state.chapter_num,
            "phase": self.state.phase.value,
            "revision_count": self.state.revision_count,
            "review_score": self.state.review_result.total_score if self.state.review_result else 0,
            "verdict": self.state.review_result.verdict.value if self.state.review_result else None,
            "final_word_count": len(self.get_final_content()),
        }
