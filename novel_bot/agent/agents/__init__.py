from enum import Enum

class AgentRole(Enum):
    COORDINATOR = "coordinator"
    PLANNER = "planner"
    WRITER = "writer"
    REVIEWER = "reviewer"
    POLISHER = "polisher"

ROLE_DESCRIPTIONS = {
    AgentRole.COORDINATOR: "主控制器，负责全局协调和任务分配",
    AgentRole.PLANNER: "规划师，负责大纲、人物、世界观规划和归档维护",
    AgentRole.WRITER: "写作者，负责根据场景规划撰写章节正文",
    AgentRole.REVIEWER: "审查者，负责质量检查，输出审查报告",
    AgentRole.POLISHER: "润色者，负责去AI味、语言精修、节奏微调",
}

ROLE_PERMISSIONS = {
    AgentRole.COORDINATOR: {
        "read": ["*"],
        "write": ["*"],
        "tools": ["*"],
    },
    AgentRole.PLANNER: {
        "read": ["*"],
        "write": ["bible/", "plans/", "STORY_SUMMARY.md", "CHARACTERS.md", "WORLD.md"],
        "tools": ["read_file", "write_file", "append_file", "memorize_important_fact", "memorize_chapter_event"],
    },
    AgentRole.WRITER: {
        "read": ["bible/", "plans/", "SOUL.md", "TONE.md", "CHARACTERS.md", "WORLD.md", "STORY_SUMMARY.md"],
        "write": ["drafts/"],
        "tools": ["read_file", "write_file", "append_file"],
    },
    AgentRole.REVIEWER: {
        "read": ["*"],
        "write": ["reviews/"],
        "tools": ["read_file", "write_file"],
    },
    AgentRole.POLISHER: {
        "read": ["drafts/", "reviews/", "bible/"],
        "write": ["drafts/"],
        "tools": ["read_file", "write_file"],
    },
}

ROLE_SKILLS = {
    AgentRole.COORDINATOR: [],
    AgentRole.PLANNER: ["planner-skill"],
    AgentRole.WRITER: ["writer-skill"],
    AgentRole.REVIEWER: ["reviewer-skill"],
    AgentRole.POLISHER: ["polisher-skill"],
}
