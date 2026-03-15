import asyncio
from typing import List, Dict, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field
from loguru import logger

from novel_bot.agent.agents import AgentRole, ROLE_DESCRIPTIONS, ROLE_PERMISSIONS, ROLE_SKILLS
from novel_bot.agent.memory import MemoryStore
from novel_bot.agent.provider import LLMProvider
from novel_bot.agent.tools import ToolRegistry
from novel_bot.agent.skills import SkillsLoader


@dataclass
class AgentResponse:
    success: bool
    content: str
    tool_calls: List[Any] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


class SubAgent:
    def __init__(
        self,
        role: AgentRole,
        workspace_path: Path,
        provider: Optional[LLMProvider] = None,
    ):
        self.role = role
        self.workspace_path = Path(workspace_path)
        self.memory = MemoryStore(str(workspace_path))
        self.provider = provider or LLMProvider()
        self.permissions = ROLE_PERMISSIONS.get(role, {})
        self.skills_loader = SkillsLoader(self.workspace_path)
        self.history: List[Dict] = []
        self._tools: Optional[ToolRegistry] = None
    
    @property
    def tools(self) -> ToolRegistry:
        if self._tools is None:
            self._tools = ToolRegistry(self.memory, allowed_tools=self._get_allowed_tools())
        return self._tools
    
    def _get_allowed_tools(self) -> List[str]:
        allowed = self.permissions.get("tools", [])
        if "*" in allowed:
            return []
        return allowed
    
    def _get_allowed_skills(self) -> List[str]:
        return ROLE_SKILLS.get(self.role, [])
    
    def build_system_prompt(self) -> str:
        prompt_parts = [
            f"# IDENTITY",
            f"You are a {self.role.value} agent in a novel writing system.",
            f"Role: {ROLE_DESCRIPTIONS.get(self.role, '')}",
            "",
            "# PERMISSIONS",
        ]
        
        read_perms = self.permissions.get("read", [])
        write_perms = self.permissions.get("write", [])
        tool_perms = self.permissions.get("tools", [])
        
        prompt_parts.append(f"## Read Access: {', '.join(read_perms)}")
        prompt_parts.append(f"## Write Access: {', '.join(write_perms)}")
        prompt_parts.append(f"## Available Tools: {', '.join(tool_perms)}")
        
        prompt_parts.append("")
        prompt_parts.append("# INSTRUCTIONS")
        prompt_parts.append("1. Stay within your role and permissions")
        prompt_parts.append("2. Only use tools you have access to")
        prompt_parts.append("3. Only read/write files in your permitted directories")
        prompt_parts.append("4. Focus on your specific task")
        
        skill_names = self._get_allowed_skills()
        if skill_names:
            skills_content = self.skills_loader.load_skills_for_context(skill_names)
            if skills_content:
                prompt_parts.append("")
                prompt_parts.append("# SKILLS")
                prompt_parts.append(skills_content)
        
        soul = self.memory.read("SOUL.md")
        if soul:
            prompt_parts.append("")
            prompt_parts.append("# WRITING STYLE")
            prompt_parts.append(soul)
        
        tone = self.memory.read("TONE.md")
        if tone:
            prompt_parts.append("")
            prompt_parts.append("# TONE")
            prompt_parts.append(tone)
        
        return "\n".join(prompt_parts)
    
    async def process(self, instruction: str, context: Optional[str] = None) -> AgentResponse:
        messages = [{"role": "system", "content": self.build_system_prompt()}]
        
        user_content = instruction
        if context:
            user_content = f"{instruction}\n\nContext:\n{context}"
        
        self.history.append({"role": "user", "content": user_content})
        messages.extend(self.history)
        
        try:
            response = await self.provider.chat(messages, tools=self.tools.schemas)
            
            MAX_LOOPS = 10
            loop_count = 0
            
            while response.tool_calls and loop_count < MAX_LOOPS:
                loop_count += 1
                self.history.append(response)
                messages.append(response)
                
                for tool_call in response.tool_calls:
                    if self._can_use_tool(tool_call.function.name):
                        result = await self.tools.execute(tool_call)
                        tool_msg = {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result,
                        }
                        self.history.append(tool_msg)
                        messages.append(tool_msg)
                    else:
                        error_msg = f"Permission denied: Tool '{tool_call.function.name}' not available for role '{self.role.value}'"
                        tool_msg = {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": error_msg,
                        }
                        self.history.append(tool_msg)
                        messages.append(tool_msg)
                
                response = await self.provider.chat(messages, tools=self.tools.schemas)
            
            if response.content:
                self.history.append({"role": "assistant", "content": response.content})
            
            return AgentResponse(
                success=True,
                content=response.content or "",
                tool_calls=response.tool_calls or [],
            )
        
        except Exception as e:
            logger.error(f"SubAgent {self.role.value} error: {e}")
            return AgentResponse(
                success=False,
                content=f"Error: {str(e)}",
            )
    
    def _can_use_tool(self, tool_name: str) -> bool:
        allowed = self.permissions.get("tools", [])
        return "*" in allowed or tool_name in allowed
    
    def _can_read_file(self, filename: str) -> bool:
        allowed = self.permissions.get("read", [])
        if "*" in allowed:
            return True
        for pattern in allowed:
            if filename.startswith(pattern.rstrip("/")) or filename == pattern:
                return True
        return False
    
    def _can_write_file(self, filename: str) -> bool:
        allowed = self.permissions.get("write", [])
        if "*" in allowed:
            return True
        for pattern in allowed:
            if filename.startswith(pattern.rstrip("/")) or filename == pattern:
                return True
        return False
    
    def clear_history(self):
        self.history = []
    
    def get_last_response(self) -> Optional[str]:
        for msg in reversed(self.history):
            if msg.get("role") == "assistant" and msg.get("content"):
                return msg["content"]
        return None
