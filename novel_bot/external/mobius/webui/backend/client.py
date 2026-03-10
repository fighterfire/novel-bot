"""WebUI 客户端工具。

与后端 API 通信。
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import AsyncGenerator, Callable

import httpx

logger = logging.getLogger("mobius.webui.client")


class MobiusClient:
    """Mobius WebUI 客户端。"""

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def create_task(
        self,
        phase: str,
        setting_file: str,
        output_dir: str = "output",
        start_chapter: int = 1,
        end_chapter: int = 9999,
        dry_run: bool = False,
    ) -> str:
        """创建任务并返回 task_id。"""
        response = await self.client.post(
            f"{self.base_url}/api/tasks",
            json={
                "phase": phase,
                "setting_file": setting_file,
                "output_dir": output_dir,
                "start_chapter": start_chapter,
                "end_chapter": end_chapter,
                "dry_run": dry_run,
            },
        )
        response.raise_for_status()
        return response.json()["task_id"]

    async def get_task(self, task_id: str) -> dict:
        """获取任务信息。"""
        response = await self.client.get(f"{self.base_url}/api/tasks/{task_id}")
        response.raise_for_status()
        return response.json()

    async def get_task_logs(self, task_id: str) -> list[dict]:
        """获取任务日志。"""
        response = await self.client.get(f"{self.base_url}/api/tasks/{task_id}/logs")
        response.raise_for_status()
        return response.json()

    async def watch_task(
        self,
        task_id: str,
        on_log: Callable[[dict], None] | None = None,
        on_status: Callable[[dict], None] | None = None,
    ) -> AsyncGenerator[dict, None]:
        """监听任务进度（WebSocket）。"""
        ws_url = f"{self.base_url.replace('http', 'ws')}/ws/tasks/{task_id}"
        
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream("GET", ws_url) as response:
                    # 使用 SSE 替代 WebSocket（更兼容）
                    async for line in response.aiter_lines():
                        if line.startswith("data:"):
                            try:
                                data = json.loads(line[5:])
                                yield data
                                
                                if on_log and data.get("type") == "log":
                                    on_log(data.get("data", {}))
                                elif on_status and data.get("type") == "status":
                                    on_status(data.get("data", {}))
                            except json.JSONDecodeError:
                                pass
        except Exception as e:
            logger.error(f"Error watching task {task_id}: {e}")
            # 回退到轮询
            await self._poll_task(task_id, on_log, on_status)

    async def _poll_task(
        self,
        task_id: str,
        on_log: Callable[[dict], None] | None = None,
        on_status: Callable[[dict], None] | None = None,
    ):
        """使用轮询方式监听任务（回退方案）。"""
        last_log_index = 0
        
        while True:
            try:
                task = await self.get_task(task_id)
                
                # 发送日志
                logs = task.get("logs", [])
                if len(logs) > last_log_index:
                    for log in logs[last_log_index:]:
                        if on_log:
                            on_log(log)
                        yield {"type": "log", "data": log}
                    last_log_index = len(logs)
                
                # 发送状态
                if on_status:
                    on_status({
                        "status": task.get("status"),
                        "progress": task.get("progress"),
                    })
                
                yield {
                    "type": "status",
                    "data": {
                        "status": task.get("status"),
                        "progress": task.get("progress"),
                    }
                }
                
                # 任务完成则退出
                if task.get("status") in {"completed", "failed"}:
                    yield {
                        "type": "done",
                        "data": {"completed_at": task.get("completed_at")}
                    }
                    break
                
                await asyncio.sleep(1)
            
            except Exception as e:
                logger.error(f"Error polling task {task_id}: {e}")
                break

    async def check_health(self) -> bool:
        """检查后端服务器是否可用。"""
        try:
            response = await self.client.get(f"{self.base_url}/api/health")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self):
        """关闭客户端连接。"""
        await self.client.aclose()


async def test_client():
    """测试客户端。"""
    client = MobiusClient()
    
    try:
        # 测试健康检查
        is_healthy = await client.check_health()
        print(f"Backend healthy: {is_healthy}")
        
        if not is_healthy:
            print("Backend unavailable, skipping task test")
            return
        
        # 创建模拟任务
        task_id = await client.create_task(
            phase="outline",
            setting_file="test.yaml",
            dry_run=True,
        )
        print(f"Created task: {task_id}")
        
        # 监听任务
        async for event in client.watch_task(task_id):
            print(f"Event: {event}")
    
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_client())
