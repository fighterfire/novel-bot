#!/usr/bin/env python
"""Mobius WebUI 启动脚本。

同时启动后端和前端。
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path


def main():
    """主函数。"""
    parser = argparse.ArgumentParser(description="启动 Mobius WebUI")
    parser.add_argument(
        "--backend-host",
        default="127.0.0.1",
        help="后端服务地址（默认: 127.0.0.1）",
    )
    parser.add_argument(
        "--backend-port",
        type=int,
        default=8000,
        help="后端服务端口（默认: 8000）",
    )
    parser.add_argument(
        "--frontend-port",
        type=int,
        default=8501,
        help="前端服务端口（默认: 8501）",
    )
    parser.add_argument(
        "--frontend-only",
        action="store_true",
        help="仅启动前端（假设后端已在运行）",
    )
    parser.add_argument(
        "--backend-only",
        action="store_true",
        help="仅启动后端",
    )
    
    args = parser.parse_args()
    
    webui_dir = Path(__file__).parent
    
    processes = []
    
    try:
        # 启动后端
        if not args.frontend_only:
            print("🔥 启动 Mobius WebUI 后端服务...")
            backend_cmd = [
                sys.executable,
                "-m",
                "webui.backend.server",
                "--host",
                args.backend_host,
                "--port",
                str(args.backend_port),
            ]
            backend_process = subprocess.Popen(
                backend_cmd,
                cwd=webui_dir.parent,
            )
            processes.append(backend_process)
            print(f"✅ 后端正在运行: http://{args.backend_host}:{args.backend_port}")
            
            # 等待后端启动
            if not args.backend_only:
                time.sleep(2)
        
        # 启动前端
        if not args.backend_only:
            print("🎨 启动 Streamlit 前端...")
            frontend_cmd = [
                "streamlit",
                "run",
                str(webui_dir / "app.py"),
                "--logger.level=info",
                f"--server.port={args.frontend_port}",
                "--server.headless=false",
            ]
            frontend_process = subprocess.Popen(
                frontend_cmd,
                cwd=webui_dir.parent,
            )
            processes.append(frontend_process)
            print(f"✅ 前端正在运行: http://localhost:{args.frontend_port}")
        
        print("\n" + "=" * 50)
        print("Mobius WebUI 已启动！")
        print("=" * 50)
        
        if not args.backend_only:
            print(f"📖 打开浏览器访问: http://localhost:{args.frontend_port}")
        
        # 等待进程
        while processes:
            try:
                for i, proc in enumerate(processes):
                    if proc.poll() is not None:
                        # 进程已终止
                        processes.pop(i)
                        break
                time.sleep(1)
            except KeyboardInterrupt:
                print("\n\n关闭服务...")
                for proc in processes:
                    try:
                        proc.terminate()
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                break
    
    except KeyboardInterrupt:
        print("\n\n关闭所有服务...")
        for proc in processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
    
    except Exception as e:
        print(f"❌ 错误: {e}")
        for proc in processes:
            try:
                proc.kill()
            except:
                pass
        sys.exit(1)


if __name__ == "__main__":
    main()
