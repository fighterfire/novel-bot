import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from loguru import logger


class CheckpointType(Enum):
    BEFORE_PLANNING = "before_planning"
    AFTER_PLANNING = "after_planning"
    BEFORE_WRITING = "before_writing"
    AFTER_WRITING = "after_writing"
    BEFORE_REVIEW = "before_review"
    AFTER_REVIEW = "after_review"
    BEFORE_REVISION = "before_revision"
    AFTER_REVISION = "after_revision"
    BEFORE_POLISH = "before_polish"
    AFTER_POLISH = "after_polish"
    MILESTONE = "milestone"


@dataclass
class Checkpoint:
    id: str
    chapter_num: int
    checkpoint_type: CheckpointType
    timestamp: str
    data: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    confirmed: bool = False
    auto_continue: bool = False

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "chapter_num": self.chapter_num,
            "checkpoint_type": self.checkpoint_type.value,
            "timestamp": self.timestamp,
            "data": self.data,
            "description": self.description,
            "confirmed": self.confirmed,
            "auto_continue": self.auto_continue,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Checkpoint":
        return cls(
            id=data["id"],
            chapter_num=data["chapter_num"],
            checkpoint_type=CheckpointType(data["checkpoint_type"]),
            timestamp=data["timestamp"],
            data=data.get("data", {}),
            description=data.get("description", ""),
            confirmed=data.get("confirmed", False),
            auto_continue=data.get("auto_continue", False),
        )


@dataclass
class CheckpointConfig:
    enabled: bool = True
    auto_continue_after_seconds: int = 0
    require_confirmation: bool = True
    checkpoint_types: List[CheckpointType] = field(default_factory=lambda: [
        CheckpointType.AFTER_PLANNING,
        CheckpointType.AFTER_REVIEW,
        CheckpointType.MILESTONE,
    ])
    save_to_file: bool = True


class CheckpointManager:
    def __init__(
        self,
        workspace_path: str,
        config: Optional[CheckpointConfig] = None,
    ):
        self.workspace_path = Path(workspace_path)
        self.config = config or CheckpointConfig()
        self.checkpoints_dir = self.workspace_path / "checkpoints"
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        
        self._checkpoints: Dict[str, Checkpoint] = {}
        self._pending_checkpoint: Optional[Checkpoint] = None
        self._confirmation_callback: Optional[Callable] = None
        self._auto_continue_task: Optional[asyncio.Task] = None
        
        self._load_checkpoints()

    def _load_checkpoints(self):
        checkpoint_file = self.checkpoints_dir / "checkpoints.json"
        if checkpoint_file.exists():
            try:
                with open(checkpoint_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for cp_data in data.get("checkpoints", []):
                        cp = Checkpoint.from_dict(cp_data)
                        self._checkpoints[cp.id] = cp
            except Exception as e:
                logger.error(f"Failed to load checkpoints: {e}")

    def _save_checkpoints(self):
        if not self.config.save_to_file:
            return
        
        checkpoint_file = self.checkpoints_dir / "checkpoints.json"
        try:
            data = {
                "checkpoints": [cp.to_dict() for cp in self._checkpoints.values()],
                "last_updated": datetime.now().isoformat(),
            }
            with open(checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save checkpoints: {e}")

    def create_checkpoint(
        self,
        chapter_num: int,
        checkpoint_type: CheckpointType,
        data: Optional[Dict[str, Any]] = None,
        description: str = "",
    ) -> Checkpoint:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cp_id = f"cp_{chapter_num:02d}_{checkpoint_type.value}_{timestamp}"
        
        checkpoint = Checkpoint(
            id=cp_id,
            chapter_num=chapter_num,
            checkpoint_type=checkpoint_type,
            timestamp=timestamp,
            data=data or {},
            description=description,
        )
        
        self._checkpoints[cp_id] = checkpoint
        self._save_checkpoints()
        
        logger.info(f"Created checkpoint: {cp_id}")
        return checkpoint

    def should_pause(self, checkpoint_type: CheckpointType) -> bool:
        if not self.config.enabled:
            return False
        
        if not self.config.require_confirmation:
            return False
        
        return checkpoint_type in self.config.checkpoint_types

    async def wait_for_confirmation(
        self,
        checkpoint: Checkpoint,
        timeout: Optional[int] = None,
    ) -> bool:
        if not self.should_pause(checkpoint.checkpoint_type):
            return True
        
        self._pending_checkpoint = checkpoint
        
        if timeout is None:
            timeout = self.config.auto_continue_after_seconds
        
        if timeout > 0:
            self._auto_continue_task = asyncio.create_task(
                self._auto_continue_after_timeout(timeout)
            )
        
        while self._pending_checkpoint and not self._pending_checkpoint.confirmed:
            await asyncio.sleep(0.1)
        
        if self._auto_continue_task:
            self._auto_continue_task.cancel()
            self._auto_continue_task = None
        
        result = self._pending_checkpoint.confirmed if self._pending_checkpoint else True
        self._pending_checkpoint = None
        
        return result

    async def _auto_continue_after_timeout(self, seconds: int):
        try:
            await asyncio.sleep(seconds)
            if self._pending_checkpoint:
                logger.info(f"Auto-continuing after {seconds} seconds")
                self._pending_checkpoint.confirmed = True
                self._pending_checkpoint.auto_continue = True
        except asyncio.CancelledError:
            pass

    def confirm_checkpoint(self, checkpoint_id: Optional[str] = None):
        if checkpoint_id:
            if checkpoint_id in self._checkpoints:
                self._checkpoints[checkpoint_id].confirmed = True
                self._save_checkpoints()
        elif self._pending_checkpoint:
            self._pending_checkpoint.confirmed = True
            self._save_checkpoints()

    def reject_checkpoint(self):
        if self._pending_checkpoint:
            self._pending_checkpoint.confirmed = False
            self._pending_checkpoint = None

    def get_pending_checkpoint(self) -> Optional[Checkpoint]:
        return self._pending_checkpoint

    def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        return self._checkpoints.get(checkpoint_id)

    def get_chapter_checkpoints(self, chapter_num: int) -> List[Checkpoint]:
        return [
            cp for cp in self._checkpoints.values()
            if cp.chapter_num == chapter_num
        ]

    def get_latest_checkpoint(self, chapter_num: int) -> Optional[Checkpoint]:
        chapter_cps = self.get_chapter_checkpoints(chapter_num)
        if not chapter_cps:
            return None
        return max(chapter_cps, key=lambda cp: cp.timestamp)

    def save_state(
        self,
        chapter_num: int,
        phase: str,
        content: str,
        metadata: Optional[Dict] = None,
    ) -> Checkpoint:
        return self.create_checkpoint(
            chapter_num=chapter_num,
            checkpoint_type=CheckpointType.MILESTONE,
            data={
                "phase": phase,
                "content": content,
                "metadata": metadata or {},
            },
            description=f"Milestone: {phase}",
        )

    def restore_state(self, checkpoint_id: str) -> Optional[Dict]:
        checkpoint = self.get_checkpoint(checkpoint_id)
        if not checkpoint:
            return None
        
        return {
            "chapter_num": checkpoint.chapter_num,
            "phase": checkpoint.data.get("phase"),
            "content": checkpoint.data.get("content"),
            "metadata": checkpoint.data.get("metadata", {}),
        }

    def list_checkpoints(self) -> List[Dict]:
        return [
            {
                "id": cp.id,
                "chapter_num": cp.chapter_num,
                "type": cp.checkpoint_type.value,
                "timestamp": cp.timestamp,
                "description": cp.description,
                "confirmed": cp.confirmed,
            }
            for cp in sorted(
                self._checkpoints.values(),
                key=lambda x: x.timestamp,
                reverse=True,
            )
        ]

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        if checkpoint_id in self._checkpoints:
            del self._checkpoints[checkpoint_id]
            self._save_checkpoints()
            return True
        return False

    def clear_chapter_checkpoints(self, chapter_num: int):
        to_delete = [
            cp_id for cp_id, cp in self._checkpoints.items()
            if cp.chapter_num == chapter_num
        ]
        for cp_id in to_delete:
            del self._checkpoints[cp_id]
        self._save_checkpoints()

    def set_confirmation_callback(self, callback: Optional[Callable]):
        self._confirmation_callback = callback

    async def request_user_confirmation(
        self,
        checkpoint: Checkpoint,
        message: str,
    ) -> bool:
        if self._confirmation_callback:
            return await self._confirmation_callback(checkpoint, message)
        return await self.wait_for_confirmation(checkpoint)
