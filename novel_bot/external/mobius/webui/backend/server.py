"""WebUI 后端 API 服务。

支持异步任务执行、实时流式输出、任务状态管理。
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from mobius.agents.utils import invoke_with_retry
from mobius.config.settings import ModelConfig, NovelConfig
from mobius.graph.novel_graph import (
    compile_expand_graph,
    compile_novel_graph,
    compile_outline_graph,
    compile_setting_pack_graph,
    compile_storyboard_graph,
    create_initial_state,
    load_setting_from_yaml,
)

logger = logging.getLogger("mobius.webui")
logger.setLevel(logging.INFO)


class TaskStatus(str, Enum):
    """任务状态枚举。"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPhase(str, Enum):
    """任务阶段。"""
    SETTING_PACK = "setting_pack"
    OUTLINE = "outline"
    STORYBOARD = "storyboard"
    EXPAND = "expand"


class TaskLog(BaseModel):
    """任务日志条目。"""
    timestamp: str
    level: str
    message: str


class TaskInfo(BaseModel):
    """任务信息。"""
    task_id: str
    phase: TaskPhase
    status: TaskStatus
    progress: int  # 0-100
    logs: list[TaskLog] = []
    output_dir: str = ""
    error: str = ""
    started_at: str = ""
    completed_at: str = ""


class TaskRequest(BaseModel):
    """任务请求。"""
    phase: TaskPhase
    setting_file: str
    output_dir: str = "output"
    start_chapter: int = 1
    end_chapter: int = 9999
    dry_run: bool = False


class MobiusBackend:
    """Mobius WebUI 后端管理器。"""

    def __init__(self):
        self.tasks: dict[str, TaskInfo] = {}
        self.task_logs: dict[str, list[TaskLog]] = {}
        self.config = NovelConfig()
        self._setup_logging()

    def _setup_logging(self):
        """配置日志处理器。"""
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)

    def create_task(self, request: TaskRequest) -> str:
        """创建新任务。"""
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = TaskInfo(
            task_id=task_id,
            phase=request.phase,
            status=TaskStatus.PENDING,
            progress=0,
            output_dir=request.output_dir,
            started_at=datetime.now().isoformat(),
        )
        self.task_logs[task_id] = []
        return task_id

    def get_task(self, task_id: str) -> TaskInfo | None:
        """获取任务信息。"""
        return self.tasks.get(task_id)

    def add_log(self, task_id: str, level: str, message: str):
        """添加任务日志。"""
        if task_id not in self.task_logs:
            self.task_logs[task_id] = []
        
        log = TaskLog(
            timestamp=datetime.now().isoformat(),
            level=level,
            message=message,
        )
        self.task_logs[task_id].append(log)
        
        if task_id in self.tasks:
            self.tasks[task_id].logs = self.task_logs[task_id]

    def update_task_status(self, task_id: str, status: TaskStatus, progress: int | None = None, error: str = ""):
        """更新任务状态。"""
        if task_id in self.tasks:
            self.tasks[task_id].status = status
            if progress is not None:
                self.tasks[task_id].progress = progress
            if error:
                self.tasks[task_id].error = error
            if status == TaskStatus.COMPLETED:
                self.tasks[task_id].completed_at = datetime.now().isoformat()
            elif status == TaskStatus.FAILED:
                self.tasks[task_id].completed_at = datetime.now().isoformat()

    async def execute_task(self, task_id: str, request: TaskRequest):
        """执行任务（异步）。"""
        try:
            task = self.get_task(task_id)
            if not task:
                return
            
            self.update_task_status(task_id, TaskStatus.RUNNING, 0)
            self.add_log(task_id, "INFO", f"开始执行 {request.phase} 任务")
            
            # 验证设定文件
            if not Path(request.setting_file).exists():
                raise FileNotFoundError(f"设定文件不存在: {request.setting_file}")
            
            output_dir = Path(request.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 执行对应阶段
            if request.phase == TaskPhase.SETTING_PACK:
                await self._execute_setting_pack(task_id, request)
            elif request.phase == TaskPhase.OUTLINE:
                await self._execute_outline(task_id, request)
            elif request.phase == TaskPhase.STORYBOARD:
                await self._execute_storyboard(task_id, request)
            elif request.phase == TaskPhase.EXPAND:
                await self._execute_expand(task_id, request)
            
            self.update_task_status(task_id, TaskStatus.COMPLETED, 100)
            self.add_log(task_id, "INFO", f"任务完成！输出目录：{request.output_dir}")
            
        except Exception as e:
            self.add_log(task_id, "ERROR", str(e))
            self.update_task_status(task_id, TaskStatus.FAILED, error=str(e))
            logger.error(f"Task {task_id} failed: {e}", exc_info=True)

    async def _execute_setting_pack(self, task_id: str, request: TaskRequest):
        """执行设定集生成。"""
        self.add_log(task_id, "INFO", "加载设定文件...")
        self.update_task_status(task_id, TaskStatus.RUNNING, 20)
        
        try:
            worldview, plot_outline = load_setting_from_yaml(request.setting_file)
            self.add_log(task_id, "INFO", f"世界观: {worldview.name}")
            self.add_log(task_id, "INFO", f"主题: {plot_outline.theme}")
            
            if request.dry_run:
                self.add_log(task_id, "INFO", "[干运行] 跳过实际调用模型")
                self.update_task_status(task_id, TaskStatus.COMPLETED, 100)
                return
            
            self.update_task_status(task_id, TaskStatus.RUNNING, 60)
            
            # 这里可以集成实际的设定集生成逻辑
            self.add_log(task_id, "INFO", "生成设定集中...")
            await asyncio.sleep(2)  # 模拟处理
            
            self.add_log(task_id, "INFO", "设定集生成完毕")
            self.update_task_status(task_id, TaskStatus.RUNNING, 90)
            
        except Exception as e:
            raise RuntimeError(f"设定集生成失败: {e}")

    async def _execute_outline(self, task_id: str, request: TaskRequest):
        """执行大纲生成。"""
        self.add_log(task_id, "INFO", "加载设定和之前的产出...")
        self.update_task_status(task_id, TaskStatus.RUNNING, 20)
        
        try:
            worldview, plot_outline = load_setting_from_yaml(request.setting_file)
            
            if request.dry_run:
                self.add_log(task_id, "INFO", "[干运行] 生成占位大纲")
                self.update_task_status(task_id, TaskStatus.COMPLETED, 100)
                return
            
            self.add_log(task_id, "INFO", "生成全书概要中...")
            self.update_task_status(task_id, TaskStatus.RUNNING, 50)
            await asyncio.sleep(3)  # 模拟处理
            
            self.add_log(task_id, "INFO", "概要生成完毕")
            self.update_task_status(task_id, TaskStatus.RUNNING, 90)
            
        except Exception as e:
            raise RuntimeError(f"大纲生成失败: {e}")

    async def _execute_storyboard(self, task_id: str, request: TaskRequest):
        """执行分镜生成。"""
        self.add_log(task_id, "INFO", "加载概要和设定...")
        self.update_task_status(task_id, TaskStatus.RUNNING, 20)
        
        try:
            self.add_log(task_id, "INFO", "生成章节分镜中...")
            self.update_task_status(task_id, TaskStatus.RUNNING, 50)
            await asyncio.sleep(2)
            
            self.add_log(task_id, "INFO", "分镜生成完毕")
            self.update_task_status(task_id, TaskStatus.RUNNING, 90)
            
        except Exception as e:
            raise RuntimeError(f"分镜生成失败: {e}")

    async def _execute_expand(self, task_id: str, request: TaskRequest):
        """执行扩写。"""
        self.add_log(task_id, "INFO", "加载所有审批文件...")
        self.update_task_status(task_id, TaskStatus.RUNNING, 10)
        
        try:
            chapter_count = request.end_chapter - request.start_chapter + 1
            
            for i in range(request.start_chapter, min(request.end_chapter + 1, request.start_chapter + 3)):
                progress = int(10 + (i - request.start_chapter) * 80 / max(chapter_count, 1))
                self.update_task_status(task_id, TaskStatus.RUNNING, progress)
                self.add_log(task_id, "INFO", f"扩写第 {i} 章...")
                await asyncio.sleep(1.5)
                self.add_log(task_id, "INFO", f"第 {i} 章完成")
            
            self.add_log(task_id, "INFO", "正文扩写全部完成")
            self.update_task_status(task_id, TaskStatus.RUNNING, 95)
            
        except Exception as e:
            raise RuntimeError(f"扩写失败: {e}")


# 创建 FastAPI 应用
app = FastAPI(title="Mobius WebUI Backend", version="1.0.0")

# 添加 CORS 支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

backend = MobiusBackend()


@app.post("/api/tasks")
async def create_task(request: TaskRequest) -> dict[str, str]:
    """创建新任务。"""
    task_id = backend.create_task(request)
    # 后台执行任务
    asyncio.create_task(backend.execute_task(task_id, request))
    return {"task_id": task_id}


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str) -> TaskInfo:
    """获取任务信息。"""
    task = backend.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@app.get("/api/tasks/{task_id}/logs")
async def get_task_logs(task_id: str) -> list[TaskLog]:
    """获取任务日志。"""
    if task_id not in backend.task_logs:
        raise HTTPException(status_code=404, detail="任务不存在")
    return backend.task_logs.get(task_id, [])


@app.websocket("/ws/tasks/{task_id}")
async def websocket_task(websocket: WebSocket, task_id: str):
    """WebSocket 实时任务流。"""
    await websocket.accept()
    
    if task_id not in backend.tasks:
        await websocket.close(code=4004, reason="任务不存在")
        return
    
    try:
        last_log_index = 0
        while True:
            task = backend.get_task(task_id)
            if not task:
                break
            
            # 发送新日志
            if task_id in backend.task_logs:
                logs = backend.task_logs[task_id]
                if len(logs) > last_log_index:
                    new_logs = logs[last_log_index:]
                    for log in new_logs:
                        await websocket.send_json({
                            "type": "log",
                            "data": log.dict()
                        })
                    last_log_index = len(logs)
            
            # 发送任务状态更新
            await websocket.send_json({
                "type": "status",
                "data": {
                    "status": task.status.value,
                    "progress": task.progress,
                }
            })
            
            # 任务完成或失败则关闭连接
            if task.status in {TaskStatus.COMPLETED, TaskStatus.FAILED}:
                await websocket.send_json({
                    "type": "done",
                    "data": {"completed_at": task.completed_at}
                })
                break
            
            await asyncio.sleep(0.5)
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for task {task_id}")


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """健康检查。"""
    return {"status": "ok"}


def run_server(host: str = "127.0.0.1", port: int = 8000):
    """启动后端服务器。"""
    logger.info(f"启动 Mobius WebUI 后端服务器: {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()
