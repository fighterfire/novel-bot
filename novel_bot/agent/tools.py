from typing import Callable, Any, Dict, List, Optional
import json
import inspect
from loguru import logger
from novel_bot.agent.memory import MemoryStore


class ToolRegistry:
    def __init__(self, memory: MemoryStore, allowed_tools: Optional[List[str]] = None):
        self.memory = memory
        self.workspace = str(memory.workspace)
        self.tools: Dict[str, Callable] = {}
        self.schemas: List[Dict] = []
        self.allowed_tools = allowed_tools
        self._register_defaults()

    def register(self, func: Callable):
        self.tools[func.__name__] = func
        return func

    def _is_tool_allowed(self, tool_name: str) -> bool:
        if self.allowed_tools is None or len(self.allowed_tools) == 0:
            return True
        return tool_name in self.allowed_tools

    def _register_defaults(self):
        if self._is_tool_allowed("read_file"):
            self.tools["read_file"] = self.memory.read
            self.schemas.append({
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read the content of a file from the workspace.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string", "description": "The path to the file (e.g. 'MEMO.md', 'drafts/ch1.md')"}
                        },
                        "required": ["filename"]
                    }
                }
            })

        if self._is_tool_allowed("write_file"):
            self.tools["write_file"] = self.memory.write
            self.schemas.append({
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write content to a file. Overwrites if exists.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string", "description": "File path"},
                            "content": {"type": "string", "description": "Full content to write"}
                        },
                        "required": ["filename", "content"]
                    }
                }
            })

        if self._is_tool_allowed("list_files"):
            self.tools["list_files"] = self.memory.list_files
            self.schemas.append({
                "type": "function",
                "function": {
                    "name": "list_files",
                    "description": "List markdown files in the workspace.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {"type": "string", "description": "Glob pattern (default *.md)"}
                        }
                    }
                }
            })
        
        if self._is_tool_allowed("append_file"):
            self.tools["append_file"] = self.memory.append
            self.schemas.append({
                "type": "function",
                "function": {
                    "name": "append_file",
                    "description": "Append text to a file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string"},
                            "content": {"type": "string"}
                        },
                        "required": ["filename", "content"]
                    }
                }
            })
        
        if self._is_tool_allowed("memorize_chapter_event"):
            self.tools["memorize_chapter_event"] = self.memory.save_chapter_memory
            self.schemas.append({
                "type": "function",
                "function": {
                    "name": "memorize_chapter_event",
                    "description": "Save a DETAILED SUMMARY of a chapter to memory. Do NOT save full text.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "chapter_title": {"type": "string", "description": "e.g. 'Chapter 03'"},
                            "content": {"type": "string", "description": "Detailed bullet points of plot events, item acquisition, and character status changes."}
                        },
                        "required": ["chapter_title", "content"]
                    }
                }
            })
        
        if self._is_tool_allowed("memorize_important_fact"):
            self.tools["memorize_important_fact"] = self.memory.update_global_memory
            self.schemas.append({
                "type": "function",
                "function": {
                    "name": "memorize_important_fact",
                    "description": "Add an important fact to long-term memory (MEMORY.md).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string", "description": "The fact to remember."}
                        },
                        "required": ["content"]
                    }
                }
            })

        if self._is_tool_allowed("mobius_generate_outline") or self._is_tool_allowed("mobius_generate_setting_pack"):
            try:
                from novel_bot.agent.mobius_adapter import run_outline, run_setting_pack

                if self._is_tool_allowed("mobius_generate_outline"):
                    def _run_outline_wrapper(setting_path: str, output: str = "output", dry_run: bool = True, end_chapter: Optional[int] = None) -> str:
                        return run_outline(
                            setting_path=setting_path,
                            output=output,
                            dry_run=dry_run,
                            end_chapter=end_chapter,
                            workspace=self.workspace,
                        )
                    
                    self.tools["mobius_generate_outline"] = _run_outline_wrapper
                    self.schemas.append({
                        "type": "function",
                        "function": {
                            "name": "mobius_generate_outline",
                            "description": "Generate full novel outline using external Mobius integration. The setting_path should be a file in the workspace (e.g., 'STORY_SUMMARY.md', 'WORLD.md', or any markdown file containing novel settings).",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "setting_path": {"type": "string", "description": "Path to the startup markdown/yaml file in workspace (e.g. 'STORY_SUMMARY.md', 'WORLD.md')"},
                                    "output": {"type": "string", "description": "Output directory (default: 'output')"},
                                    "dry_run": {"type": "boolean", "description": "If true, do not call remote model (default: true)"},
                                    "end_chapter": {"type": "integer", "description": "Optional: generate up to this chapter"}
                                },
                                "required": ["setting_path"]
                            }
                        }
                    })

                if self._is_tool_allowed("mobius_generate_setting_pack"):
                    def _run_setting_pack_wrapper(setting_path: str, output: str = "output", dry_run: bool = True) -> str:
                        return run_setting_pack(
                            setting_path=setting_path,
                            output=output,
                            dry_run=dry_run,
                            workspace=self.workspace,
                        )
                    
                    self.tools["mobius_generate_setting_pack"] = _run_setting_pack_wrapper
                    self.schemas.append({
                        "type": "function",
                        "function": {
                            "name": "mobius_generate_setting_pack",
                            "description": "Generate a structured setting pack using Mobius. The setting_path should be a file in the workspace containing novel settings.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "setting_path": {"type": "string", "description": "Path to the startup markdown/yaml file in workspace (e.g. 'STORY_SUMMARY.md', 'WORLD.md')"},
                                    "output": {"type": "string", "description": "Output directory (default: 'output')"},
                                    "dry_run": {"type": "boolean", "description": "If true, do not call remote model (default: true)"}
                                },
                                "required": ["setting_path"]
                            }
                        }
                    })
            except Exception as e:
                logger.warning(f"Failed to register mobius tools: {e}")

    async def execute(self, tool_call: Any) -> str:
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        
        if name in self.tools:
            logger.info(f"Executing tool: {name} with args: {args}")
            try:
                result = self.tools[name](**args)
                return str(result)
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                return f"Error: {e}"
        return f"Error: Tool {name} not found."
