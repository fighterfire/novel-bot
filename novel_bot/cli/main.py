import typer
import asyncio
import os
from typing import Optional
from pathlib import Path
from rich.console import Console

from novel_bot.agent.loop import AgentLoop
from novel_bot.agent.provider import LLMProvider
from novel_bot.config.settings import settings

app = typer.Typer()
console = Console()

def find_available_workspace(base_path: Path) -> Path:
    """查找可用的workspace名称，如果已存在则自动递增"""
    if not base_path.exists():
        return base_path
    
    base_name = base_path.name
    parent = base_path.parent
    
    counter = 1
    while True:
        new_name = f"{base_name}_{counter}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        counter += 1

async def generate_settings_from_prompt(prompt: str) -> dict:
    """使用AI根据写作需求生成设定文件内容"""
    provider = LLMProvider()
    
    system_prompt = """你是一个专业的小说设定专家。请深入思考用户的写作需求，然后生成最符合需求的小说核心设定文件。

思考过程：
1. 首先理解用户的核心创作需求和风格偏好
2. 分析适合的题材类型和叙事风格
3. 设计有深度的角色和世界观
4. 确保所有设定文件内容详细且实用

请严格按照以下JSON格式返回，不要添加任何其他文字说明：
{
  "soul": "AI的人设和写作风格（Markdown格式，2-3段，描述AI应该如何写作，强调'展示而非讲述'，避免陈词滥调）",
  "user": "用户的写作目标（Markdown格式，详细描述用户的创作目标和期望）",
  "tone": "小说的基调和风格（Markdown格式，3-5点，描述叙事特点、语言风格、情感基调等）",
  "characters": "主要角色设定（Markdown格式，包含至少2个主要角色，每个角色有姓名、年龄、身份、性格特点、背景故事）",
  "world": "世界观设定（Markdown格式，描述故事发生的世界背景、规则、社会结构等）",
  "story_summary": "故事梗概（Markdown格式，3-5段，描述故事的核心冲突、主要情节走向和主题）"
}

每个字段必须是详细的Markdown格式内容。请确保返回的是纯JSON格式，不要有任何额外的文字。"""
    
    user_message = f"写作需求：{prompt}\n\n请深入思考这个需求，然后生成最符合要求的小说设定文件。"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    try:
        console.print("[cyan]AI正在思考并生成设定文件...[/cyan]")
        response = await provider.chat(messages)
        content = response.content
        
        console.print(f"[dim]AI完整响应: {content}[/dim]")
        
        import json
        import re
        
        # 移除可能的markdown代码块标记
        content = content.replace('```json', '').replace('```', '').strip()
        
        # 尝试直接解析
        try:
            result = json.loads(content)
            console.print(f"[green]✅ 成功解析JSON，包含字段: {list(result.keys())}[/green]")
            
            # 验证必要字段
            required_fields = ["soul", "user", "tone", "characters", "world", "story_summary"]
            missing_fields = [f for f in required_fields if f not in result]
            if missing_fields:
                console.print(f"[yellow]⚠️ 缺少字段: {missing_fields}，将使用默认值[/yellow]")
            
            return result
        except json.JSONDecodeError as e:
            console.print(f"[yellow]⚠️ 直接JSON解析失败: {e}[/yellow]")
            # 如果直接解析失败，尝试查找JSON块
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                json_str = json_match.group()
                try:
                    result = json.loads(json_str)
                    console.print(f"[green]✅ 通过正则匹配成功解析JSON，包含字段: {list(result.keys())}[/green]")
                    return result
                except json.JSONDecodeError as e2:
                    console.print(f"[red]❌ 正则匹配的JSON也解析失败: {e2}[/red]")
            
            console.print("[red]❌ 无法解析AI响应，使用默认设定[/red]")
            console.print(f"[dim]AI响应内容: {content}[/dim]")
            return None
    except Exception as e:
        console.print(f"[red]❌ AI生成失败: {e}[/red]")
        import traceback
        console.print(f"[dim]错误详情: {traceback.format_exc()}[/dim]")
        return None

@app.command()
def init(
    path: str = typer.Option("workspace", help="Path to create workspace"),
    prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="Writing prompt to auto-generate settings"),
    overwrite: bool = typer.Option(False, "--overwrite", "-o", help="Overwrite existing settings files"),
    auto: bool = typer.Option(False, "--auto", "-a", help="Automatically create new workspace if path exists (e.g., workspace_1, workspace_2)")
):
    """Initialize a new Novel Writer workspace."""
    target = Path(path)
    
    if target.exists():
        if auto:
            new_target = find_available_workspace(target)
            console.print(f"[yellow]Workspace {target} already exists.[/yellow]")
            console.print(f"[cyan]Creating new workspace: {new_target}[/cyan]")
            target = new_target
            overwrite = True
        else:
            console.print(f"[yellow]Workspace {target} already exists.[/yellow]")
            if not overwrite and not typer.confirm("Do you want to keep existing files and only add missing ones?"):
                return

    target.mkdir(parents=True, exist_ok=True)
    (target / "memory").mkdir(exist_ok=True)
    (target / "memory" / "chapters").mkdir(exist_ok=True)
    (target / "drafts").mkdir(exist_ok=True)
    
    defaults = {
        "SOUL.md": "You are a pragmatic, detail-oriented novelist. You value 'Show, Don't Tell'.\nYou avoid clichés and purple prose.",
        "USER.md": "User wants to write a fantasy novel about a mage who can't cast spells but can enchant items.",
        "TONE.md": "- Serious but with dark humor.\n- High fantasy setting.\n- Focus on the mechanics of magic.",
        "CHARACTERS.md": "# Main Character\nName: Kael\nAge: 24\nRole: Enchanter\n\n# Antagonist\nName: Voren\nRole: Archmage",
        "WORLD.md": "The world of Aethelgard. Magic is fading.",
        "STORY_SUMMARY.md": "No chapters written yet.",
    }
    
    generated_settings = None
    if prompt:
        console.print(f"[cyan]Generating settings from prompt: {prompt}[/cyan]")
        console.print("[dim]This may take a moment...[/dim]")
        generated_settings = asyncio.run(generate_settings_from_prompt(prompt))
        if generated_settings:
            defaults["SOUL.md"] = generated_settings.get("soul", defaults["SOUL.md"])
            defaults["USER.md"] = generated_settings.get("user", defaults["USER.md"])
            defaults["TONE.md"] = generated_settings.get("tone", defaults["TONE.md"])
            defaults["CHARACTERS.md"] = generated_settings.get("characters", defaults["CHARACTERS.md"])
            defaults["WORLD.md"] = generated_settings.get("world", defaults["WORLD.md"])
            defaults["STORY_SUMMARY.md"] = generated_settings.get("story_summary", defaults["STORY_SUMMARY.md"])
            console.print("[green]Settings generated successfully![/green]")

    for filename, content in defaults.items():
        file_path = target / filename
        if not file_path.exists():
            file_path.write_text(content, encoding="utf-8")
            console.print(f"Created [green]{filename}[/green]")
        elif overwrite:
            file_path.write_text(content, encoding="utf-8")
            console.print(f"Overwritten [yellow]{filename}[/yellow]")
        else:
            console.print(f"Skipped [dim]{filename}[/dim] (exists)")
            
    console.print(f"\n[bold green]Workspace initialized at {target}[/bold green]")
    console.print("Run 'start' to begin.")

@app.command()
def start(
    workspace: str = typer.Option(None, "--workspace", "-w", help="Path to workspace directory (default: workspace)")
):
    """Start the Novel Writer Agent."""
    if not settings.NVIDIA_API_KEY and not os.environ.get("NVIDIA_API_KEY"):
         console.print("[bold red]Error:[/bold red] NVIDIA_API_KEY not found in environment or .env file.")
         return

    workspace_path = workspace if workspace else settings.workspace_path
    loop = AgentLoop(workspace_path)
    asyncio.run(loop.start())

if __name__ == "__main__":
    app()
