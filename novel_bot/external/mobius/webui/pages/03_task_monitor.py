"""任务监控页面。"""

import asyncio
import json
import logging
from datetime import datetime

import streamlit as st

logger = logging.getLogger("mobius.webui")

st.set_page_config(
    page_title="任务监控 - Mobius",
    page_icon="🔍",
    layout="wide",
)

st.markdown("# 🔍 任务实时监控")


def init_client():
    """初始化客户端。"""
    if "client" not in st.session_state:
        try:
            from webui.backend.client import MobiusClient
        except ImportError:
            import sys
            sys.path.insert(0, str(__file__).parent.parent.parent)
            from webui.backend.client import MobiusClient
        
        st.session_state.client = MobiusClient(
            base_url=st.secrets.get("BACKEND_URL", "http://127.0.0.1:8000")
        )


def main():
    """主函数。"""
    init_client()
    
    # 任务ID选择
    col1, col2 = st.columns([3, 1])
    
    with col1:
        task_id = st.text_input(
            "输入任务ID",
            value=st.session_state.get("current_task_id", ""),
            placeholder="粘贴任务ID以监控进度",
        )
    
    with col2:
        if st.button("刷新", use_container_width=True):
            st.rerun()
    
    if not task_id:
        st.info("💡 输入任务ID开始监控")
        return
    
    # 创建占位符用于实时更新
    status_placeholder = st.empty()
    progress_placeholder = st.empty()
    logs_placeholder = st.empty()
    
    try:
        with status_placeholder.container():
            st.spinner("加载任务信息...")
        
        # 获取初始任务信息
        try:
            task = st.session_state.client.get_task(task_id)
        except Exception as e:
            st.error(f"❌ 获取任务失败: {e}")
            return
        
        # 显示任务信息
        with status_placeholder.container():
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("状态", task.get("status", "unknown").upper())
            
            with col2:
                st.metric("进度", f"{task.get('progress', 0)}%")
            
            with col3:
                st.metric("阶段", task.get("phase", "unknown"))
            
            with col4:
                if task.get("started_at"):
                    start_time = datetime.fromisoformat(task["started_at"])
                    elapsed = (datetime.now() - start_time).total_seconds() / 60
                    st.metric("已耗时", f"{elapsed:.1f} 分钟")
        
        # 进度条
        with progress_placeholder.container():
            progress_percent = task.get("progress", 0) / 100.0
            st.progress(progress_percent)
            st.caption(f"进度: {task.get('progress', 0)}%")
        
        # 日志显示
        with logs_placeholder.container():
            st.subheader("📋 任务日志")
            
            logs = task.get("logs", [])
            if logs:
                # 使用可展开的日志列表
                with st.expander(f"查看完整日志（共 {len(logs)} 条）", expanded=True):
                    log_content = ""
                    for log in logs:
                        timestamp = log.get("timestamp", "")[:19]  # 只显示日期和时间
                        level = log.get("level", "INFO")
                        message = log.get("message", "")
                        
                        # 按日志级别着色
                        if level == "ERROR":
                            log_line = f"[{timestamp}] ❌ {message}"
                        elif level == "WARNING":
                            log_line = f"[{timestamp}] ⚠️ {message}"
                        else:
                            log_line = f"[{timestamp}] ℹ️ {message}"
                        
                        log_content += log_line + "\n"
                    
                    st.code(log_content, language="log")
            else:
                st.caption("还没有日志信息")
        
        # 任务完成/失败处理
        status = task.get("status", "")
        
        if status == "completed":
            st.success("✅ 任务完成！")
            
            if task.get("output_dir"):
                st.markdown(f"**输出目录**: `{task['output_dir']}`")
                
                # 查看输出文件
                output_path = task["output_dir"]
                try:
                    from pathlib import Path
                    output_files = list(Path(output_path).rglob("*.md"))
                    if output_files:
                        st.markdown("**生成文件**:")
                        for file in output_files[:10]:
                            rel_path = file.relative_to(output_path)
                            st.markdown(f"- `{rel_path}`")
                except:
                    pass
        
        elif status == "failed":
            st.error("❌ 任务失败！")
            if task.get("error"):
                st.markdown(f"**错误信息**: {task['error']}")
        
        elif status == "running":
            st.info("⏳ 任务运行中...")
            
            # 自动刷新
            import time
            time.sleep(2)
            st.rerun()
        
        elif status == "pending":
            st.warning("⏱️ 任务等待中...")
            import time
            time.sleep(1)
            st.rerun()
    
    except Exception as e:
        st.error(f"❌ 错误: {e}")
        logger.exception("Error in task monitor")


if __name__ == "__main__":
    main()
