from typing import Optional
from novel_bot.agent.memory import MemoryStore
from novel_bot.agent.skills import SkillsLoader
from novel_bot.agent.agents import AgentRole, ROLE_DESCRIPTIONS, ROLE_PERMISSIONS, ROLE_SKILLS
from loguru import logger

class ContextBuilder:
    def __init__(self, memory_store: MemoryStore, role: Optional[AgentRole] = None):
        self.memory = memory_store
        self.role = role or AgentRole.COORDINATOR
        self.skills = SkillsLoader(memory_store.workspace)

    def build_system_prompt(self) -> str:
        prompt_parts = [
            "# IDENTITY",
            f"You are a {self.role.value} agent in a novel writing system.",
            f"Role: {ROLE_DESCRIPTIONS.get(self.role, 'Expert novel writer agent')}",
        ]
        
        prompt_parts.extend(self._build_permissions_section())
        prompt_parts.extend(self._build_context_section())
        prompt_parts.extend(self._build_skills_section())
        prompt_parts.extend(self._build_instructions_section())
        
        return "\n".join(prompt_parts)
    
    def _build_permissions_section(self) -> list:
        permissions = ROLE_PERMISSIONS.get(self.role, {})
        read_perms = permissions.get("read", [])
        write_perms = permissions.get("write", [])
        tool_perms = permissions.get("tools", [])
        
        parts = [
            "",
            "# PERMISSIONS",
            f"## Read Access: {', '.join(read_perms) if read_perms else 'All'}",
            f"## Write Access: {', '.join(write_perms) if write_perms else 'All'}",
            f"## Available Tools: {', '.join(tool_perms) if tool_perms else 'All'}",
        ]
        return parts
    
    def _build_context_section(self) -> list:
        parts = []
        
        soul = self.memory.read("SOUL.md")
        if soul:
            parts.append(f"\n## WRITING STYLE\n{soul}")
        
        tone = self.memory.read("TONE.md")
        if tone:
            parts.append(f"\n## TONE\n{tone}")

        if self._can_read("CHARACTERS.md"):
            chars = self.memory.read("CHARACTERS.md")
            if chars:
                parts.append(f"\n## CHARACTERS\n{chars}")
        
        if self._can_read("WORLD.md"):
            world = self.memory.read("WORLD.md")
            if world:
                parts.append(f"\n## WORLD SETTING\n{world}")

        if self._can_read("memory/"):
            global_mem = self.memory.read_global_memory()
            if global_mem:
                parts.append(f"\n## LONG TERM MEMORY (Important Facts)\n{global_mem}")
            
            recent_chapters = self.memory.get_recent_chapters()
            if recent_chapters:
                parts.append(f"\n## RECENT CHAPTER SUMMARIES (Short Term Memory)\n{recent_chapters}")

        if self._can_read("STORY_SUMMARY.md"):
            summary = self.memory.read("STORY_SUMMARY.md")
            if summary:
                parts.append(f"\n## STORY SO FAR\n{summary}")
        
        return parts
    
    def _build_skills_section(self) -> list:
        parts = []
        
        role_skills = ROLE_SKILLS.get(self.role, [])
        if role_skills:
            skills_content = self.skills.load_skills_for_context(role_skills)
            if skills_content:
                parts.append(f"\n## ROLE SKILLS\n{skills_content}")
        
        always_skills = self.skills.get_always_skills()
        if always_skills:
            always_content = self.skills.load_skills_for_context(always_skills)
            if always_content:
                parts.append(f"\n## ACTIVE SKILLS\n{always_content}")
        
        skills_summary = self.skills.build_skills_summary()
        if skills_summary:
            parts.append(f"""\n## AVAILABLE SKILLS

The following skills extend your capabilities. To use a skill, read its SKILL.md file using the read_file tool.

{skills_summary}""")
        
        return parts
    
    def _build_instructions_section(self) -> list:
        base_instructions = [
            "",
            "# INSTRUCTIONS",
            "1. Stay within your role and permissions",
            "2. Only use tools you have access to",
            "3. Only read/write files in your permitted directories",
            "4. Focus on your specific task",
        ]
        
        role_instructions = {
            AgentRole.PLANNER: [
                "5. Create detailed scene plans before writing",
                "6. Maintain the story bible (bible/) with character and world info",
                "7. Track plot threads, suspense, and foreshadowing",
                "8. Update STORY_SUMMARY.md after each chapter",
            ],
            AgentRole.WRITER: [
                "5. Write chapters based on scene plans",
                "6. Save chapters to drafts/ directory",
                "7. Follow the writing style defined in SOUL.md",
                "8. Maintain character voices and story consistency",
            ],
            AgentRole.REVIEWER: [
                "5. Review chapters using the 10-dimension checklist",
                "6. Score each dimension from 1-5",
                "7. Provide specific, actionable feedback",
                "8. Output verdict: 通过 (≥35), 需修改 (25-34), 需重写 (<25)",
            ],
            AgentRole.POLISHER: [
                "5. Remove AI flavor from text",
                "6. Improve dialogue naturalness",
                "7. Enhance descriptions and pacing",
                "8. Maintain the author's voice",
            ],
            AgentRole.COORDINATOR: [
                "5. Coordinate between specialized agents",
                "6. Ensure quality through the review process",
                "7. Report progress and results to the user",
                "8. Maintain overall story coherence",
            ],
        }
        
        return base_instructions + role_instructions.get(self.role, [])
    
    def _can_read(self, path: str) -> bool:
        permissions = ROLE_PERMISSIONS.get(self.role, {})
        read_perms = permissions.get("read", [])
        if "*" in read_perms:
            return True
        for pattern in read_perms:
            if path.startswith(pattern.rstrip("/")) or path == pattern:
                return True
        return False
