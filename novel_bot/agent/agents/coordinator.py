import asyncio
from typing import List, Dict, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field
from loguru import logger
from rich.console import Console
from rich.markdown import Markdown

from novel_bot.agent.agents import AgentRole
from novel_bot.agent.agents.base import SubAgent, AgentResponse
from novel_bot.agent.memory import MemoryStore
from novel_bot.agent.provider import LLMProvider

console = Console()


@dataclass
class WorkflowState:
    current_chapter: int = 0
    total_chapters: int = 0
    phase: str = "init"
    confirmed: bool = False
    milestone_confirmed: bool = False


@dataclass
class ChapterResult:
    chapter_num: int
    success: bool
    content: str
    review_score: float = 0.0
    review_verdict: str = ""


class CoordinatorAgent:
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.memory = MemoryStore(workspace_path)
        self.provider = LLMProvider()
        
        self.planner = SubAgent(AgentRole.PLANNER, self.workspace_path, self.provider)
        self.writer = SubAgent(AgentRole.WRITER, self.workspace_path, self.provider)
        self.reviewer = SubAgent(AgentRole.REVIEWER, self.workspace_path, self.provider)
        self.polisher = SubAgent(AgentRole.POLISHER, self.workspace_path, self.provider)
        
        self.state = WorkflowState()
        self.history: List[Dict] = []

    async def start(self):
        console.print("[bold green]Novel Writer Multi-Agent System Started.[/bold green]")
        console.print(f"Workspace: {self.workspace_path}")
        
        if not (self.workspace_path / "SOUL.md").exists():
            console.print("[yellow]Warning: SOUL.md not found. Run 'init' command first.[/yellow]")

        while True:
            try:
                user_input = await asyncio.to_thread(input, "\nEditor > ")
                if user_input.lower() in ["exit", "quit"]:
                    break
                
                await self.process_turn(user_input)
            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]Error:[/red] {e}")

    async def process_turn(self, user_input: str):
        self.history.append({"role": "user", "content": user_input})
        
        if self._is_workflow_command(user_input):
            await self._handle_workflow_command(user_input)
        else:
            await self._handle_general_command(user_input)

    def _is_workflow_command(self, user_input: str) -> bool:
        keywords = ["写第", "审查第", "润色第", "规划第", "开始创作", "继续创作"]
        return any(kw in user_input for kw in keywords)

    async def _handle_workflow_command(self, user_input: str):
        if "写第" in user_input or "开始创作" in user_input:
            chapter_num = self._extract_chapter_num(user_input)
            if chapter_num:
                result = await self.create_chapter(chapter_num)
                if result.success:
                    console.print(f"[green]第 {result.chapter_num} 章创作完成！[/green]")
                    console.print(f"审查评分: {result.review_score}, 结论: {result.review_verdict}")
                else:
                    console.print(f"[red]第 {chapter_num} 章创作失败[/red]")
        
        elif "审查第" in user_input:
            chapter_num = self._extract_chapter_num(user_input)
            if chapter_num:
                response = await self.reviewer.process(f"审查第 {chapter_num} 章的质量")
                console.print(Markdown(response.content))
        
        elif "润色第" in user_input:
            chapter_num = self._extract_chapter_num(user_input)
            if chapter_num:
                response = await self.polisher.process(f"润色第 {chapter_num} 章")
                console.print(Markdown(response.content))
        
        elif "规划第" in user_input:
            chapter_num = self._extract_chapter_num(user_input)
            if chapter_num:
                response = await self.planner.process(f"规划第 {chapter_num} 章的场景")
                console.print(Markdown(response.content))

    async def _handle_general_command(self, user_input: str):
        system_prompt = self._build_coordinator_prompt()
        messages = [{"role": "system", "content": system_prompt}] + self.history
        
        console.print("[dim]Thinking...[/dim]")
        
        try:
            response = await self.provider.chat(messages)
            if response.content:
                self.history.append({"role": "assistant", "content": response.content})
                console.print("\n[bold blue]Coordinator:[/bold blue]")
                console.print(Markdown(response.content))
        except Exception as e:
            logger.error(f"Coordinator error: {e}")
            console.print(f"[red]Error:[/red] {e}")

    def _build_coordinator_prompt(self) -> str:
        prompt_parts = [
            "# IDENTITY",
            "You are the Coordinator Agent in a multi-agent novel writing system.",
            "Your role is to coordinate between specialized agents: Planner, Writer, Reviewer, and Polisher.",
            "",
            "# AVAILABLE AGENTS",
            "- **Planner**: Creates outlines, character designs, world-building, and scene plans",
            "- **Writer**: Writes chapter content based on scene plans",
            "- **Reviewer**: Reviews chapter quality with a 10-dimension checklist",
            "- **Polisher**: Polishes content to remove AI flavor and improve style",
            "",
            "# WORKFLOW",
            "1. Planner creates scene plan → 2. Writer writes chapter → 3. Reviewer checks quality → 4. Polisher refines",
            "",
            "# INSTRUCTIONS",
            "1. Understand user requests and delegate to appropriate agents",
            "2. Maintain overall story coherence",
            "3. Ensure quality through the review process",
            "4. Report progress and results to the user",
        ]
        
        story_summary = self.memory.read("STORY_SUMMARY.md")
        if story_summary:
            prompt_parts.append("")
            prompt_parts.append("# STORY SUMMARY")
            prompt_parts.append(story_summary)
        
        return "\n".join(prompt_parts)

    async def create_chapter(self, chapter_num: int) -> ChapterResult:
        console.print(f"[cyan]开始创作第 {chapter_num} 章...[/cyan]")
        
        console.print("[dim]Step 1: 场景规划 (Planner)[/dim]")
        plan_response = await self.planner.process(f"为第 {chapter_num} 章创建详细的场景规划")
        if not plan_response.success:
            return ChapterResult(chapter_num=chapter_num, success=False, content="规划失败")
        
        console.print("[dim]Step 2: 章节写作 (Writer)[/dim]")
        write_response = await self.writer.process(
            f"根据场景规划写作第 {chapter_num} 章",
            context=f"场景规划:\n{plan_response.content}"
        )
        if not write_response.success:
            return ChapterResult(chapter_num=chapter_num, success=False, content="写作失败")
        
        console.print("[dim]Step 3: 质量审查 (Reviewer)[/dim]")
        review_response = await self.reviewer.process(
            f"审查第 {chapter_num} 章的质量，输出评分和改进建议",
            context=f"章节内容:\n{write_response.content}"
        )
        
        review_score, review_verdict = self._parse_review(review_response.content)
        
        if review_score < 25:
            console.print("[yellow]评分过低，需要重写...[/yellow]")
            return await self.create_chapter(chapter_num)
        
        if review_score < 35:
            console.print("[dim]Step 3.5: 根据审查意见修改 (Writer)[/dim]")
            write_response = await self.writer.process(
                f"根据审查意见修改第 {chapter_num} 章",
                context=f"原内容:\n{write_response.content}\n\n审查意见:\n{review_response.content}"
            )
        
        console.print("[dim]Step 4: 润色优化 (Polisher)[/dim]")
        polish_response = await self.polisher.process(
            f"润色第 {chapter_num} 章，去除AI味，优化语言",
            context=f"章节内容:\n{write_response.content}"
        )
        
        console.print("[dim]Step 5: 归档更新 (Planner)[/dim]")
        await self.planner.process(
            f"更新故事圣经，记录第 {chapter_num} 章的重要信息",
            context=f"章节内容:\n{polish_response.content}"
        )
        
        final_content = polish_response.content if polish_response.success else write_response.content
        
        return ChapterResult(
            chapter_num=chapter_num,
            success=True,
            content=final_content,
            review_score=review_score,
            review_verdict=review_verdict
        )

    def _parse_review(self, review_content: str) -> tuple:
        import re
        score_match = re.search(r"总分[：:]\s*(\d+(?:\.\d+)?)", review_content)
        score = float(score_match.group(1)) if score_match else 35.0
        
        if "通过" in review_content:
            verdict = "通过"
        elif "需修改" in review_content:
            verdict = "需修改"
        elif "需重写" in review_content:
            verdict = "需重写"
        else:
            verdict = "通过" if score >= 35 else "需修改"
        
        return score, verdict

    def _extract_chapter_num(self, text: str) -> Optional[int]:
        import re
        match = re.search(r"第\s*(\d+)\s*章", text)
        if match:
            return int(match.group(1))
        
        numbers = re.findall(r"\d+", text)
        if numbers:
            return int(numbers[0])
        
        return None

    def get_agent_status(self) -> Dict[str, Any]:
        return {
            "workspace": str(self.workspace_path),
            "state": {
                "current_chapter": self.state.current_chapter,
                "phase": self.state.phase,
            },
            "agents": {
                "planner": len(self.planner.history),
                "writer": len(self.writer.history),
                "reviewer": len(self.reviewer.history),
                "polisher": len(self.polisher.history),
            }
        }
