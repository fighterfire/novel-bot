"""Mobius WebUI - Streamlit 主应用。

提供完整的小说创作工作流UI。
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
try:
    from streamlit_option_menu import option_menu
except ImportError:
    # 如果 streamlit_option_menu 不可用，定义一个简单的替代
    def option_menu(*args, **kwargs):
        return st.selectbox("菜单", kwargs.get("options", []))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mobius.webui")

# 页面配置
st.set_page_config(
    page_title="Mobius - 失控型叙事引擎",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 自定义样式
st.markdown("""
    <style>
    .main {
        padding-top: 0rem;
    }
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 1.2em;
    }
    </style>
""", unsafe_allow_html=True)


def init_session_state():
    """初始化 session 状态。"""
    if "client" not in st.session_state:
        try:
            from webui.backend.client import MobiusClient
        except ImportError:
            from backend.client import MobiusClient
        
        st.session_state.client = MobiusClient(
            base_url=st.secrets.get("BACKEND_URL", "http://127.0.0.1:8000")
        )
    
    if "backend_available" not in st.session_state:
        st.session_state.backend_available = True
    
    if "current_task_id" not in st.session_state:
        st.session_state.current_task_id = None
    
    if "task_history" not in st.session_state:
        st.session_state.task_history = []


def check_backend():
    """检查后端是否可用。"""
    try:
        # 使用同步检查（简化）
        import requests
        backend_url = st.secrets.get("BACKEND_URL", "http://127.0.0.1:8000")
        response = requests.get(f"{backend_url}/api/health", timeout=2)
        return response.status_code == 200
    except Exception as e:
        logger.warning(f"Backend check failed: {e}")
        return False


def sidebar():
    """侧边栏导航。"""
    with st.sidebar:
        st.markdown("# 🔥 Mobius v2.1")
        st.markdown("### 失控型叙事引擎")
        st.divider()
        
        # 后端状态指示器
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.session_state.backend_available:
                st.markdown("✅ 后端服务就绪")
            else:
                st.markdown("❌ 后端离线")
        
        with col2:
            if st.button("🔄", help="刷新状态", key="refresh_btn"):
                st.session_state.backend_available = check_backend()
                st.rerun()
        
        st.divider()
        
        # 帮助和文档
        st.markdown("### 📚 帮助")
        with st.expander("工作流说明"):
            st.markdown("""
            **三层创作架构：**
            
            1. **设定补完** - 反向补全世界观设定
            2. **章节概要** - 生成全书主线和思想推进
            3. **章节分镜** - 按场景分解章节结构
            4. **正文扩写** - 按分镜严格扩写成文
            
            每层都需人工审批后方可推进。
            """)
        
        with st.expander("关键概念"):
            st.markdown("""
            - **不可逆变化**: 每章的永久性推进
            - **线索账本**: 承诺与回收的追踪
            - **失控引擎**: 自动应用认知偏差
            - **信念畸变**: 角色的非线性成长
            """)
        
        st.divider()
        st.markdown("v2.1 | 基于 LangGraph")


def header():
    """页面头部。"""
    st.markdown("# 🔥 Mobius - 失控型叙事引擎")
    st.markdown("> 角色不是执行主题。角色是带着偏见在做错事。")


def main():
    """主应用入口。"""
    init_session_state()
    
    # 检查后端
    if not st.session_state.backend_available:
        st.session_state.backend_available = check_backend()
    
    sidebar()
    
    # 标签页导航
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 快速生成",
        "📋 工作流",
        "🔍 任务状态",
        "⚙️ 设置",
        "📖 帮助",
    ])
    
    with tab1:
        st.markdown("## 快速生成小说")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            preset_file = st.text_input(
                "预设文件路径",
                value="presets/ai_love_story.yaml",
                help="YAML 预设文件的相对或绝对路径"
            )
            
            output_dir = st.text_input(
                "输出目录",
                value="output/my_novel",
                help="生成结果保存目录"
            )
        
        with col2:
            st.markdown("### 选项")
            dry_run = st.checkbox("干运行（不调用模型）", value=False)
            interactive = st.checkbox("交互式模式", value=False)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 一键生成", use_container_width=True):
                if not st.session_state.backend_available:
                    st.error("❌ 后端服务不可用，请先启动服务器")
                else:
                    with st.spinner("启动生成任务..."):
                        try:
                            task_id = st.session_state.client.create_task(
                                phase="generate_full",
                                setting_file=preset_file,
                                output_dir=output_dir,
                                dry_run=dry_run,
                            )
                            st.session_state.current_task_id = task_id
                            st.session_state.task_history.append({
                                "task_id": task_id,
                                "phase": "generate_full",
                                "created_at": datetime.now(),
                            })
                            st.success(f"✅ 任务已创建: {task_id}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ 创建任务失败: {e}")
        
        with col2:
            if st.button("📊 查看进度", use_container_width=True):
                if st.session_state.current_task_id:
                    st.switch_page("pages/03_task_monitor.py")
    
    with tab2:
        st.markdown("## 工作流操作")
        st.info("""
        通过分步骤的工作流精细控制小说创作过程。
        每个阶段需要人工审批后方可进行下一步。
        """)
        
        workflow_steps = [
            ("📦 设定补完", "setting_pack", "反向补完世界观设定"),
            ("📝 章节概要", "outline", "生成全书主线和思想推进"),
            ("🎬 章节分镜", "storyboard", "按场景分解章节结构"),
            ("✍️ 正文扩写", "expand", "按分镜扩写成文"),
        ]
        
        cols = st.columns(2)
        for idx, (label, phase, description) in enumerate(workflow_steps):
            with cols[idx % 2]:
                with st.container(border=True):
                    st.markdown(f"### {label}")
                    st.caption(description)
                    
                    with st.expander("参数配置"):
                        setting_file = st.text_input(
                            "设定文件",
                            value="presets/ai_love_story.yaml",
                            key=f"setting_{phase}"
                        )
                        output_dir = st.text_input(
                            "输出目录",
                            value="output",
                            key=f"output_{phase}"
                        )
                        dry_run = st.checkbox(
                            "干运行",
                            value=False,
                            key=f"dry_{phase}"
                        )
                    
                    if st.button("执行", key=f"run_{phase}", use_container_width=True):
                        if not st.session_state.backend_available:
                            st.error("❌ 后端服务不可用")
                        else:
                            try:
                                task_id = st.session_state.client.create_task(
                                    phase=phase,
                                    setting_file=setting_file,
                                    output_dir=output_dir,
                                    dry_run=dry_run,
                                )
                                st.session_state.current_task_id = task_id
                                st.success(f"✅ 任务已创建: {task_id[:8]}...")
                            except Exception as e:
                                st.error(f"❌ 错误: {e}")
    
    with tab3:
        st.markdown("## 任务状态")
        
        if st.session_state.task_history:
            st.subheader("最近任务")
            
            for task in reversed(st.session_state.task_history[-5:]):
                with st.container(border=True):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{task['phase']}**")
                        st.caption(f"ID: {task['task_id'][:16]}...")
                    
                    with col2:
                        st.caption(task['created_at'].strftime("%H:%M:%S"))
                    
                    with col3:
                        if st.button("查看详情", key=f"details_{task['task_id'][:8]}"):
                            st.session_state.current_task_id = task['task_id']
                            st.switch_page("pages/03_task_monitor.py")
        else:
            st.info("💡 还没有任务，开始创建一个吧！")
    
    with tab4:
        st.markdown("## 设置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("后端配置")
            backend_url = st.text_input(
                "后端服务地址",
                value=st.secrets.get("BACKEND_URL", "http://127.0.0.1:8000"),
                help="WebUI 后端服务器地址"
            )
            
            if st.button("测试连接"):
                try:
                    import requests
                    resp = requests.get(f"{backend_url}/api/health", timeout=2)
                    if resp.status_code == 200:
                        st.success("✅ 连接成功！")
                    else:
                        st.error(f"❌ 状态码: {resp.status_code}")
                except Exception as e:
                    st.error(f"❌ 连接失败: {e}")
        
        with col2:
            st.subheader("模型配置")
            provider = st.selectbox(
                "LLM 提供商",
                ["google", "openai", "anthropic", "minimax"],
                help="选择使用的大模型提供商"
            )
            
            model_name = st.text_input(
                "模型名称",
                value="gemini-3-flash-preview" if provider == "google" else "gpt-4o",
                help="具体的模型名称"
            )
            
            temperature = st.slider(
                "生成温度",
                min_value=0.0,
                max_value=1.0,
                value=0.8,
                step=0.1,
                help="越高越创意，越低越保守"
            )
    
    with tab5:
        st.markdown("## 📖 使用帮助")
        
        st.markdown("""
        ### 快速开始
        
        1. **安装** - `pip install -e .`
        2. **启动后端** - `python -m webui.backend.server`
        3. **运行 WebUI** - `streamlit run webui/app.py`
        
        ### 工作流说明
        
        **三层创作架构：**
        
        ```
        预设YAML 
           ↓
        📦 设定补完 → 人工审批
           ↓
        📝 章节概要 → 人工审批
           ↓
        🎬 章节分镜 → 人工审批
           ↓
        ✍️ 正文扩写 → 质量评审
           ↓
        📕 完整小说
        ```
        
        ### 名词解释
        
        - **设定补完**: 基于预设反向补完世界观、人物设定、时间线等
        - **概要**: 全书主线、思想推进、不可逆变化、线索回收
        - **分镜**: 每章4-8个场景，包含降密场景和因果链
        - **扩写**: 严格按分镜扩写正文，不允许临时改编
        
        """)
        
        st.divider()
        
        st.markdown("### 环境变量")
        st.code("""
# 必需：LLM API Key
export GOOGLE_API_KEY=your_key
# 或
export OPENAI_API_KEY=your_key

# 可选：自定义后端地址
export MOBIUS_BACKEND_URL=http://127.0.0.1:8000
        """)
        
        st.divider()
        
        st.markdown("### 故障排除")
        
        with st.expander("后端服务无法连接"):
            st.markdown("""
            1. 确保后端服务已启动：
               ```
               python -m webui.backend.server
               ```
            2. 检查地址和端口是否正确
            3. 查看后端日志了解详细错误
            """)
        
        with st.expander("生成速度很慢"):
            st.markdown("""
            1. 检查网络连接
            2. 确认 API Key 配额充足
            3. 尝试使用更小的 temperature 值
            4. 考虑使用 --dry-run 测试流程
            """)


if __name__ == "__main__":
    main()
