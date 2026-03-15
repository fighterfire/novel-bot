import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
from loguru import logger


class ConversationRecorder:
    PERSISTENT_HISTORY_FILE = "conversation_history.json"
    
    def __init__(self, workspace_path: str):
        self.workspace = Path(workspace_path)
        self.conversations_dir = self.workspace / "conversations"
        self.conversations_dir.mkdir(exist_ok=True, parents=True)
        
        self.persistent_history_file = self.conversations_dir / self.PERSISTENT_HISTORY_FILE
        
        self.current_session_id: Optional[str] = None
        self.current_conversation: List[Dict] = []
        self.thinking_logs: List[Dict] = []
        
        self._persistent_history: List[Dict] = []
        self._load_persistent_history()

    def _load_persistent_history(self):
        if self.persistent_history_file.exists():
            try:
                with open(self.persistent_history_file, "r", encoding="utf-8") as f:
                    self._persistent_history = json.load(f)
                logger.info(f"Loaded {len(self._persistent_history)} messages from persistent history")
            except Exception as e:
                logger.error(f"Failed to load persistent history: {e}")
                self._persistent_history = []
        else:
            self._persistent_history = []

    def _save_persistent_history(self):
        try:
            with open(self.persistent_history_file, "w", encoding="utf-8") as f:
                json.dump(self._persistent_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save persistent history: {e}")

    def get_history(self, limit: int = None) -> List[Dict]:
        if limit:
            return self._persistent_history[-limit:]
        return self._persistent_history.copy()

    def get_history_for_llm(self, limit: int = 50) -> List[Dict]:
        messages = []
        for msg in self._persistent_history[-limit:]:
            role = msg.get("role")
            content = msg.get("content", "")
            if role in ["user", "assistant"]:
                messages.append({"role": role, "content": content})
        return messages

    def clear_history(self):
        self._persistent_history = []
        self._save_persistent_history()
        logger.info("Cleared persistent history")

    def start_session(self, session_name: str = None):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_name = session_name or timestamp
        self.current_session_id = f"{session_name}_{timestamp}"
        self.current_conversation = []
        self.thinking_logs = []
        logger.info(f"Started conversation session: {self.current_session_id}")

    def add_user_message(self, content: str):
        if not self.current_session_id:
            self.start_session()
        
        message = {
            "role": "user",
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "session_id": self.current_session_id
        }
        self.current_conversation.append(message)
        self._persistent_history.append(message)
        self._save_incremental()
        self._save_persistent_history()

    def add_assistant_message(self, content: str, tool_calls: List[Dict] = None):
        if not self.current_session_id:
            self.start_session()
        
        message = {
            "role": "assistant",
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "session_id": self.current_session_id
        }
        if tool_calls:
            message["tool_calls"] = tool_calls
        
        self.current_conversation.append(message)
        self._persistent_history.append(message)
        self._save_incremental()
        self._save_persistent_history()

    def add_tool_message(self, tool_call_id: str, content: str):
        message = {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "session_id": self.current_session_id
        }
        self.current_conversation.append(message)
        self._persistent_history.append(message)
        self._save_incremental()
        self._save_persistent_history()

    def add_thinking(self, thought: str, step: int = None):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "thought": thought
        }
        if step is not None:
            log_entry["step"] = step
        
        self.thinking_logs.append(log_entry)

    def _save_incremental(self):
        if not self.current_session_id:
            return
        
        conversation_file = self.conversations_dir / f"{self.current_session_id}.json"
        
        data = {
            "session_id": self.current_session_id,
            "started_at": self.thinking_logs[0]["timestamp"] if self.thinking_logs else datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "conversation": self.current_conversation,
            "thinking_logs": self.thinking_logs
        }
        
        try:
            with open(conversation_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")

    def save_and_close(self):
        self._save_incremental()
        self._save_persistent_history()
        
        conversation_file = self.conversations_dir / f"{self.current_session_id}.json"
        markdown_file = self.conversations_dir / f"{self.current_session_id}.md"
        
        self._export_to_markdown(markdown_file)
        
        logger.info(f"Saved conversation: {self.current_session_id}")
        return str(conversation_file)

    def _export_to_markdown(self, markdown_file: Path):
        lines = [
            f"# 对话记录 - {self.current_session_id}",
            "",
            f"**开始时间**: {self.thinking_logs[0]['timestamp'] if self.thinking_logs else 'N/A'}",
            f"**最后更新**: {datetime.now().isoformat()}",
            "",
            "---",
            ""
        ]
        
        if self.thinking_logs:
            lines.append("## 思考过程")
            lines.append("")
            for i, log in enumerate(self.thinking_logs, 1):
                step = log.get("step", i)
                lines.append(f"**步骤 {step}**: {log['thought']}")
            lines.append("")
            lines.append("---")
            lines.append("")
        
        lines.append("## 对话内容")
        lines.append("")
        
        for msg in self.current_conversation:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            
            if role == "user":
                lines.append(f"### 👤 用户")
                lines.append(f"_{timestamp}_")
                lines.append(content)
            elif role == "assistant":
                lines.append(f"### 🤖 AI 助手")
                lines.append(f"_{timestamp}_")
                lines.append(content)
                if "tool_calls" in msg:
                    lines.append("")
                    lines.append("**Tool Calls:**")
                    for tc in msg["tool_calls"]:
                        lines.append(f"- {tc.get('function', {}).get('name', 'unknown')}")
            elif role == "tool":
                lines.append(f"### 🔧 工具结果")
                lines.append(f"_{timestamp}_")
                lines.append(f"```\n{content[:500]}...\n```" if len(content) > 500 else f"```\n{content}\n```")
            
            lines.append("")
        
        try:
            markdown_file.write_text("\n".join(lines), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to export markdown: {e}")

    def get_conversation_summary(self) -> Dict[str, Any]:
        if not self.current_conversation:
            return {"message_count": 0, "user_messages": 0, "assistant_messages": 0}
        
        user_count = sum(1 for m in self.current_conversation if m.get("role") == "user")
        assistant_count = sum(1 for m in self.current_conversation if m.get("role") == "assistant")
        
        return {
            "session_id": self.current_session_id,
            "message_count": len(self.current_conversation),
            "user_messages": user_count,
            "assistant_messages": assistant_count,
            "thinking_steps": len(self.thinking_logs),
            "total_persistent_messages": len(self._persistent_history)
        }

    def list_sessions(self) -> List[Dict[str, Any]]:
        sessions = []
        for f in sorted(self.conversations_dir.glob("*.json"), reverse=True):
            if f.name == self.PERSISTENT_HISTORY_FILE:
                continue
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                sessions.append({
                    "session_id": data.get("session_id", f.stem),
                    "started_at": data.get("started_at", ""),
                    "last_updated": data.get("last_updated", ""),
                    "message_count": len(data.get("conversation", [])),
                    "file": str(f)
                })
            except Exception as e:
                logger.error(f"Failed to read session {f}: {e}")
        return sessions
