import asyncio
from typing import List, Dict
from loguru import logger
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from novel_bot.agent.provider import LLMProvider
from novel_bot.agent.memory import MemoryStore
from novel_bot.agent.context import ContextBuilder
from novel_bot.agent.tools import ToolRegistry
from novel_bot.agent.recorder import ConversationRecorder
from novel_bot.config.settings import settings

console = Console()

class AgentLoop:
    HISTORY_LIMIT = 50
    
    def __init__(self, workspace_path: str = None):
        actual_workspace_path = workspace_path if workspace_path else settings.workspace_path
        self.memory = MemoryStore(actual_workspace_path)
        self.context = ContextBuilder(self.memory)
        self.provider = LLMProvider()
        self.tools = ToolRegistry(self.memory)
        self.recorder = ConversationRecorder(actual_workspace_path)
        self.history: List[Dict] = []
        
        self._load_persistent_history()

    def _load_persistent_history(self):
        saved_history = self.recorder.get_history_for_llm(limit=self.HISTORY_LIMIT)
        self.history = saved_history
        if saved_history:
            logger.info(f"Loaded {len(saved_history)} messages from persistent history")

    def _display_history_summary(self):
        if not self.history:
            console.print("[dim]没有历史对话记录[/dim]")
            return
        
        console.print(Panel(
            f"[bold green]已加载 {len(self.history)} 条历史消息[/bold green]\n"
            f"[dim]输入 'history' 查看详细记录，'clear' 清除历史[/dim]",
            title="📚 对话历史",
            border_style="blue"
        ))

    def _display_full_history(self, limit: int = 20):
        if not self.history:
            console.print("[yellow]没有历史对话记录[/yellow]")
            return
        
        console.print(f"\n[bold cyan]📜 最近 {min(limit, len(self.history))} 条对话记录[/bold cyan]")
        console.print("[dim]" + "─" * 50 + "[/dim]")
        
        for msg in self.history[-limit:]:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if role == "user":
                console.print(f"\n[bold green]👤 用户:[/bold green]")
                display_content = content[:200] + "..." if len(content) > 200 else content
                console.print(f"  {display_content}")
            elif role == "assistant":
                console.print(f"\n[bold blue]🤖 AI 助手:[/bold blue]")
                display_content = content[:300] + "..." if len(content) > 300 else content
                console.print(f"  {display_content}")
        
        console.print("\n[dim]" + "─" * 50 + "[/dim]")

    async def start(self):
        """Start the interactive loop."""
        self.recorder.start_session("interactive")
        
        console.print("[bold green]Novel Writer Agent Started.[/bold green]")
        console.print(f"Workspace: {self.memory.workspace}")
        
        if not (self.memory.workspace / "SOUL.md").exists():
            console.print("[yellow]Warning: SOUL.md not found. Run 'init' command first.[/yellow]")
        
        self._display_history_summary()

        while True:
            try:
                user_input = await asyncio.to_thread(input, "\nEditor > ")
                
                if user_input.lower() in ["exit", "quit"]:
                    break
                
                if user_input.lower() == "history":
                    self._display_full_history()
                    continue
                
                if user_input.lower() == "clear":
                    self._clear_history()
                    continue
                
                if user_input.lower() == "sessions":
                    self._list_sessions()
                    continue
                
                await self.process_turn(user_input)
            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]Error:[/red] {e}")

        self.recorder.save_and_close()
        console.print("[dim]对话已保存到 conversations/ 目录[/dim]")

    def _clear_history(self):
        self.history = []
        self.recorder.clear_history()
        console.print("[yellow]✓ 历史对话已清除[/yellow]")

    def _list_sessions(self):
        sessions = self.recorder.list_sessions()
        if not sessions:
            console.print("[dim]没有保存的会话[/dim]")
            return
        
        table = Table(title="📁 历史会话列表")
        table.add_column("会话ID", style="cyan")
        table.add_column("消息数", justify="right")
        table.add_column("最后更新", style="dim")
        
        for session in sessions[:10]:
            table.add_row(
                session.get("session_id", "unknown"),
                str(session.get("message_count", 0)),
                session.get("last_updated", "")[:19]
            )
        
        console.print(table)

    async def process_turn(self, user_input: str):
        self.history.append({"role": "user", "content": user_input})
        self.recorder.add_user_message(user_input)
        
        system_prompt = self.context.build_system_prompt()
        messages = [{"role": "system", "content": system_prompt}] + self.history

        console.print("[dim]🤔 思考中...[/dim]")
        
        try:
            current_response = await self.provider.chat(messages, tools=self.tools.schemas)
            
            MAX_LOOPS = 10
            loop_count = 0
            
            while current_response.tool_calls and loop_count < MAX_LOOPS:
                loop_count += 1
                
                self.history.append(current_response)
                messages.append(current_response)
                
                tool_call_info = []
                for tool_call in current_response.tool_calls:
                    tool_name = tool_call.function.name
                    console.print(f"[cyan]🔧 使用工具: {tool_name}[/cyan]")
                    self.recorder.add_thinking(f"调用工具: {tool_name}", step=loop_count)
                    
                    result = await self.tools.execute(tool_call)
                    
                    tool_msg = {
                        "role": "tool", 
                        "tool_call_id": tool_call.id, 
                        "content": result
                    }
                    self.history.append(tool_msg)
                    messages.append(tool_msg)
                    
                    tool_call_info.append({"function": {"name": tool_name}})
                
                console.print("[dim]🤔 继续思考...[/dim]")
                self.recorder.add_thinking(f"完成 {len(tool_call_info)} 个工具调用，继续推理")
                current_response = await self.provider.chat(messages, tools=self.tools.schemas)
            
            await self._handle_final_response(current_response)

        except Exception as e:
            logger.error(f"Loop Error: {e}")
            console.print(f"[red]Error:[/red] {e}")

    async def _handle_final_response(self, response):
        content = response.content
        if content:
            self.history.append({"role": "assistant", "content": content})
            self.recorder.add_assistant_message(content)
            
            console.print("\n[bold blue]🤖 AI 助手:[/bold blue]")
            console.print(Markdown(content))
