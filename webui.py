import streamlit as st
import os
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
import sys
sys.path.insert(0, str(Path(__file__).parent))

from novel_bot.cli.main import init as cli_init, find_available_workspace, generate_settings_from_prompt

# 设置页面配置
st.set_page_config(
    page_title="小说写作助手 网页界面",
    page_icon="📚",
    layout="wide"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #333;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #555;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .project-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .project-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    .btn-primary {
        background-color: #4CAF50;
        color: white;
        padding: 0.75rem 1.5rem;
        border: none;
        border-radius: 4px;
        font-size: 1rem;
        cursor: pointer;
    }
    .btn-primary:hover {
        background-color: #45a049;
    }
    .btn-secondary {
        background-color: #2196F3;
        color: white;
        padding: 0.75rem 1.5rem;
        border: none;
        border-radius: 4px;
        font-size: 1rem;
        cursor: pointer;
    }
    .btn-secondary:hover {
        background-color: #0b7dda;
    }
    .input-text {
        width: 100%;
        padding: 0.75rem;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 1rem;
    }
    .success-message {
        color: green;
        font-weight: bold;
        margin-top: 1rem;
    }
    .error-message {
        color: red;
        font-weight: bold;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# 页面标题
st.markdown('<div class="main-header">小说写作助手 网页界面</div>', unsafe_allow_html=True)

# 侧边栏导航
st.sidebar.title("导航")

# 使用会话状态管理当前页面
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "首页"

# 侧边栏页面选择
page = st.sidebar.radio("选择页面", ["首页", "项目管理", "智能写作助手", "AI辅助分析", "检查点管理"], 
                       index=["首页", "项目管理", "智能写作助手", "AI辅助分析", "检查点管理"].index(st.session_state["current_page"]))

# 更新会话状态
if page != st.session_state["current_page"]:
    st.session_state["current_page"] = page
    st.rerun()

# 首页
if page == "首页":
    st.markdown('<div class="sub-header">我的项目</div>', unsafe_allow_html=True)
    
    # 列出所有workspace目录
    workspaces = []
    for item in os.listdir("."):
        if os.path.isdir(item) and item.startswith("workspace"):
            workspaces.append(item)
    
    if workspaces:
        # 显示项目卡片
        for workspace in workspaces:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"<div class='project-card'>\n<h3>{workspace}</h3>\n<p>包含小说项目文件</p>\n</div>", unsafe_allow_html=True)
            with col2:
                if st.button(f"打开项目", key=f"open_{workspace}"):
                    # 保存当前选择的workspace到会话状态
                    st.session_state["current_workspace"] = workspace
                    # 切换到项目管理页面
                    st.session_state["current_page"] = "项目管理"
                    st.rerun()
    else:
        st.info("暂无项目，点击下方创建新项目")
    
    # 创建新项目
    st.markdown('<div class="sub-header">创建新项目</div>', unsafe_allow_html=True)
    
    with st.form("create_project_form"):
        prompt = st.text_area("写作需求", placeholder="例如：我想写一部末日丧尸视角下的故事，人类可觉醒异能，主角是普通人")
        auto_generate = st.checkbox("自动生成设定文件", value=True)
        auto_workspace = st.checkbox("自动创建新workspace（如果已存在）", value=True)
        submit_button = st.form_submit_button("开始创建")
    
    if submit_button:
        try:
            # 显示加载状态
            with st.spinner("AI正在思考并生成设定文件..."):
                # 准备参数
                path = "workspace"
                overwrite = False
                
                # 调用CLI的init函数
                if auto_workspace:
                    target = Path(path)
                    if target.exists():
                        new_target = find_available_workspace(target)
                        path = str(new_target)
                
                # 手动创建workspace目录
                target = Path(path)
                target.mkdir(parents=True, exist_ok=True)
                (target / "memory").mkdir(exist_ok=True)
                (target / "memory" / "chapters").mkdir(exist_ok=True)
                (target / "drafts").mkdir(exist_ok=True)
                
                # 默认设定文件
                defaults = {
                    "SOUL.md": "你是一位务实、注重细节的小说家。你重视'展示，而非讲述'的写作原则。\n你避免陈词滥调和华丽辞藻。",
                    "USER.md": f"用户想要写一部小说：{prompt}",
                    "TONE.md": "- 严肃但适当加入幽默\n- 注重角色发展和世界观构建",
                    "CHARACTERS.md": "# 主角\n姓名：[待生成]\n年龄：[待生成]\n角色：[待生成]\n\n# 反派\n姓名：[待生成]\n角色：[待生成]",
                    "WORLD.md": "[基于用户需求生成的世界观设定]",
                    "STORY_SUMMARY.md": "尚未开始写作。",
                }
                
                # 如果启用了自动生成，调用AI生成设定文件
                if prompt and auto_generate:
                    try:
                        import asyncio
                        
                        # 显示AI思考状态
                        st.info("AI正在深入分析您的写作需求...")
                        
                        # 调用AI生成设定
                        generated_settings = asyncio.run(generate_settings_from_prompt(prompt))
                        
                        if generated_settings:
                            # 更新默认设定
                            defaults["SOUL.md"] = generated_settings.get("soul", defaults["SOUL.md"])
                            defaults["USER.md"] = generated_settings.get("user", defaults["USER.md"])
                            defaults["TONE.md"] = generated_settings.get("tone", defaults["TONE.md"])
                            defaults["CHARACTERS.md"] = generated_settings.get("characters", defaults["CHARACTERS.md"])
                            defaults["WORLD.md"] = generated_settings.get("world", defaults["WORLD.md"])
                            defaults["STORY_SUMMARY.md"] = generated_settings.get("story_summary", defaults["STORY_SUMMARY.md"])
                            
                            st.success("✅ AI已成功根据您的需求生成了设定文件！")
                        else:
                            st.warning("⚠️ AI生成失败，使用默认设定")
                    except Exception as ai_error:
                        st.warning(f"⚠️ AI生成出错: {str(ai_error)}，使用默认设定")
                
                # 写入设定文件
                for filename, content in defaults.items():
                    file_path = target / filename
                    if not file_path.exists():
                        file_path.write_text(content, encoding="utf-8")
                    elif overwrite:
                        file_path.write_text(content, encoding="utf-8")
                
                st.success(f"项目创建成功！创建了新的workspace: {path}")
                
                # 保存当前选择的workspace到会话状态
                st.session_state["current_workspace"] = path
                
                # 提示用户切换到项目管理页面
                st.info("请点击侧边栏的'项目管理'查看和编辑项目文件")
        except Exception as e:
            st.error(f"创建项目时出错: {str(e)}")
            import traceback
            st.error(f"错误详情: {traceback.format_exc()}")

# 项目管理页面
elif page == "项目管理":
    # 检查是否有选中的workspace
    if "current_workspace" not in st.session_state:
        st.warning("请先从首页选择一个项目")
    else:
        current_workspace = st.session_state["current_workspace"]
        st.markdown(f'<div class="sub-header">{current_workspace} - 项目管理</div>', unsafe_allow_html=True)
        
        # 侧边栏显示目录结构
        st.sidebar.title("项目文件")
        
        # 递归获取所有文件
        def get_all_files(directory):
            file_list = []
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith('.md'):
                        relative_path = os.path.relpath(os.path.join(root, file), directory)
                        file_list.append(relative_path)
            return file_list
        
        files = get_all_files(current_workspace)
        
        # 选择文件
        selected_file = st.sidebar.selectbox("选择文件", files)
        
        if selected_file:
            # 构建完整文件路径
            file_path = os.path.join(current_workspace, selected_file)
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 显示文件编辑器
            st.markdown(f'<div class="sub-header">编辑文件: {selected_file}</div>', unsafe_allow_html=True)
            
            # 左右分屏：编辑区和预览区
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 编辑区")
                edited_content = st.text_area("", content, height=600)
                
                if st.button("保存文件"):
                    try:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(edited_content)
                        st.success("文件保存成功！")
                    except Exception as e:
                        st.error(f"保存文件时出错: {str(e)}")
            
            with col2:
                st.markdown("### 预览区")
                st.markdown(edited_content)
        
        # 底部显示目录结构
        st.markdown('<div class="sub-header">目录结构</div>', unsafe_allow_html=True)
        
        # 递归列出目录结构
        def list_directory(path, prefix=""):
            items = os.listdir(path)
            for item in sorted(items):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    st.markdown(f"📁 {prefix}{item}/")
                    list_directory(item_path, prefix + "  ")
                else:
                    st.markdown(f"📄 {prefix}{item}")
        
        list_directory(current_workspace)

# 智能写作助手页面
elif page == "智能写作助手":
    st.markdown('<div class="sub-header">智能写作助手</div>', unsafe_allow_html=True)
    
    # 检查是否有选中的workspace
    if "current_workspace" not in st.session_state:
        st.warning("请先从首页选择一个项目")
    else:
        current_workspace = st.session_state["current_workspace"]
        st.info(f"当前工作目录: {current_workspace}")
        
        # 导入必要的库
        import json
        import random
        
        # 尝试导入可选依赖
        try:
            import matplotlib.pyplot as plt
            has_matplotlib = True
        except ImportError:
            has_matplotlib = False
        
        try:
            import networkx as nx
            from pyvis.network import Network
            has_networkx = True
            has_pyvis = True
        except ImportError:
            has_networkx = False
            has_pyvis = False
        
        # 1. 写作数据统计
        st.markdown('<div class="sub-header">写作数据统计</div>', unsafe_allow_html=True)
        
        # 计算写作统计数据
        def get_writing_stats(workspace):
            drafts_dir = os.path.join(workspace, "drafts")
            stats = {
                "total_chapters": 0,
                "total_words": 0,
                "average_words_per_chapter": 0
            }
            
            if os.path.exists(drafts_dir):
                for file in os.listdir(drafts_dir):
                    if file.endswith('.md'):
                        stats["total_chapters"] += 1
                        file_path = os.path.join(drafts_dir, file)
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            stats["total_words"] += len(content)
            
            if stats["total_chapters"] > 0:
                stats["average_words_per_chapter"] = stats["total_words"] // stats["total_chapters"]
            
            return stats
        
        stats = get_writing_stats(current_workspace)
        
        # 显示统计数据
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总章节数", stats["total_chapters"])
        with col2:
            st.metric("总字数", stats["total_words"])
        with col3:
            st.metric("平均每章字数", stats["average_words_per_chapter"])
        
        # 聊天界面
        st.markdown('<div class="sub-header">与智能助手聊天</div>', unsafe_allow_html=True)
        
        # 导入AgentLoop
        from novel_bot.agent.loop import AgentLoop
        
        # 初始化AgentLoop
        if "agent_loop" not in st.session_state or st.session_state.get("last_workspace") != current_workspace:
            st.session_state["agent_loop"] = AgentLoop(current_workspace)
            st.session_state["last_workspace"] = current_workspace
            # 从持久化历史加载消息
            saved_history = st.session_state["agent_loop"].recorder.get_history(limit=50)
            st.session_state["messages"] = [
                {"role": msg.get("role"), "content": msg.get("content", "")} 
                for msg in saved_history 
                if msg.get("role") in ["user", "assistant"]
            ]
        
        # 聊天界面
        if "messages" not in st.session_state:
            st.session_state["messages"] = []
        
        # 显示历史记录摘要
        if st.session_state["messages"]:
            history_count = len(st.session_state["messages"])
            st.info(f"📚 已加载 {history_count} 条历史对话记录")
        
        # 显示聊天历史
        for message in st.session_state["messages"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # 用户输入
        if prompt := st.chat_input("输入你的写作需求..."):
            # 添加用户消息
            st.session_state["messages"].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # 显示AI正在思考
            with st.chat_message("assistant"):
                thinking_placeholder = st.empty()
                thinking_placeholder.markdown("思考中...")
                
                try:
                    # 调用Agent处理用户输入
                    import asyncio
                    response = asyncio.run(st.session_state["agent_loop"].process_turn(prompt))
                    
                    # 获取Agent的响应
                    # 注意：AgentLoop的process_turn方法没有返回值，需要从history中获取
                    if st.session_state["agent_loop"].history:
                        # 找到最后一个assistant消息
                        for msg in reversed(st.session_state["agent_loop"].history):
                            if msg.get("role") == "assistant":
                                agent_response = msg.get("content", "")
                                break
                        else:
                            agent_response = "智能助手已处理你的请求"
                    else:
                        agent_response = "智能助手已处理你的请求"
                    
                    # 更新思考占位符为实际响应
                    thinking_placeholder.markdown(agent_response)
                    
                    # 添加AI响应到聊天历史
                    st.session_state["messages"].append({"role": "assistant", "content": agent_response})
                except Exception as e:
                    error_message = f"处理请求时出错: {str(e)}"
                    thinking_placeholder.markdown(error_message)
                    st.session_state["messages"].append({"role": "assistant", "content": error_message})

# AI辅助分析页面
elif page == "AI辅助分析":
    st.markdown('<div class="main-header">AI辅助分析</div>', unsafe_allow_html=True)
    
    # 导入必要的库
    import json
    import random
    import time
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import openai
    import os
    
    # API配置
    st.sidebar.title("API配置")
    
    # 配置文件路径
    config_file = "api_config.json"
    
    # 加载配置
    def load_config():
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                st.sidebar.warning(f"加载配置失败：{str(e)}")
                return {}
        return {}
    
    # 保存配置
    def save_config(config):
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            st.sidebar.success("配置已保存")
        except Exception as e:
            st.sidebar.error(f"保存配置失败：{str(e)}")
    
    # 加载现有配置
    config = load_config()
    
    # 获取自定义API配置的辅助函数（定义在API提供商选择之前）
    def get_custom_api_config():
        # 直接读取配置文件
        try:
            if os.path.exists("api_config.json"):
                with open("api_config.json", 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    return {
                        "api_key": file_config.get("custom_api_key", ""),
                        "base_url": file_config.get("custom_api_base_url", ""),
                        "model_name": file_config.get("custom_api_model_name", "")
                    }
        except Exception as e:
            pass
        
        # 如果直接读取失败，使用传入的config
        return {
            "api_key": config.get("custom_api_key", ""),
            "base_url": config.get("custom_api_base_url", ""),
            "model_name": config.get("custom_api_model_name", "")
        }
    
    # API提供商选择
    api_provider = st.sidebar.selectbox(
        "选择API提供商",
        ["OpenAI", "Anthropic", "Google", "自定义API", "模拟模式"],
        index=["OpenAI", "Anthropic", "Google", "自定义API", "模拟模式"].index(config.get("api_provider", "模拟模式"))
    )
    
    # 模型选择
    model_choice = None
    custom_model_name = None
    api_key = None
    base_url = None
    model_name = None
    
    if api_provider != "模拟模式":
        # 根据API提供商显示相应的模型选择
        if api_provider == "OpenAI":
            model_choice = st.sidebar.selectbox(
                "选择AI模型",
                ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
                index=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"].index(config.get("openai_model", "gpt-3.5-turbo"))
            )
        elif api_provider == "Anthropic":
            model_choice = st.sidebar.selectbox(
                "选择AI模型",
                ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
                index=["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"].index(config.get("anthropic_model", "claude-3-opus-20240229"))
            )
        elif api_provider == "Google":
            model_choice = st.sidebar.selectbox(
                "选择AI模型",
                ["gemini-pro", "gemini-pro-vision"],
                index=["gemini-pro", "gemini-pro-vision"].index(config.get("google_model", "gemini-pro"))
            )
        elif api_provider == "自定义API":
            model_choice = "自定义API模型"
        
        # API配置（针对不同的API提供商）
        if api_provider == "OpenAI":
            api_key = st.sidebar.text_input(
                "OpenAI API密钥", 
                type="password",
                value=config.get("openai_api_key", "")
            )
            if api_key:
                openai.api_key = api_key
                st.sidebar.success("OpenAI API密钥已设置")
            else:
                st.sidebar.warning("请输入OpenAI API密钥以使用真实的AI分析功能")
        elif api_provider == "Anthropic":
            api_key = st.sidebar.text_input(
                "Anthropic API密钥", 
                type="password",
                value=config.get("anthropic_api_key", "")
            )
            if api_key:
                st.sidebar.success("Anthropic API密钥已设置")
            else:
                st.sidebar.warning("请输入Anthropic API密钥以使用真实的AI分析功能")
        elif api_provider == "Google":
            api_key = st.sidebar.text_input(
                "Google API密钥", 
                type="password",
                value=config.get("google_api_key", "")
            )
            if api_key:
                st.sidebar.success("Google API密钥已设置")
            else:
                st.sidebar.warning("请输入Google API密钥以使用真实的AI分析功能")
        elif api_provider == "自定义API":
            # 自定义API配置
            st.sidebar.subheader("自定义API配置")
            api_key = st.sidebar.text_input(
                "API_KEY", 
                type="password", 
                placeholder="输入API密钥",
                value=config.get("custom_api_key", "")
            )
            base_url = st.sidebar.text_input(
                "BASE_URL", 
                placeholder="输入API基础URL，例如：https://api.openai.com/v1",
                value=config.get("custom_api_base_url", "")
            )
            model_name = st.sidebar.text_input(
                "MODEL_NAME", 
                placeholder="输入模型名称",
                value=config.get("custom_api_model_name", "")
            )
            
            # 验证配置
            if api_key and base_url and model_name:
                st.sidebar.success("自定义API配置已完成")
                st.sidebar.info("💡 请点击'保存配置'按钮保存配置")
                
                # 测试连接按钮
                if st.sidebar.button("测试连接"):
                    import requests
                    
                    # 使用统一的辅助函数获取自定义API配置
                    test_config = get_custom_api_config()
                    
                    # 构建测试请求
                    test_data = {
                        "model": test_config["model_name"],
                        "messages": [
                            {"role": "user", "content": "请回复：测试成功"}
                        ],
                        "temperature": 0.0,
                        "max_tokens": 50
                    }
                    
                    # 构建请求头
                    test_headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {test_config['api_key']}"
                    }
                    
                    # 发送测试请求
                    try:
                        with st.spinner("正在测试API连接..."):
                            test_response = requests.post(
                                f"{test_config['base_url']}/chat/completions",
                                json=test_data,
                                headers=test_headers,
                                timeout=15
                            )
                            test_response.raise_for_status()  # 检查响应状态
                            
                            # 处理响应
                            test_result = test_response.json()
                            
                            # 显示完整的响应内容用于调试
                            st.sidebar.info(f"完整响应JSON：{test_result}")
                            st.sidebar.info(f"响应类型：{type(test_result)}")
                            st.sidebar.info(f"响应键：{list(test_result.keys()) if isinstance(test_result, dict) else 'N/A'}")
                            
                            # 尝试多种方式获取响应内容
                            response_content = ""
                            
                            # 方式1：标准OpenAI格式
                            if "choices" in test_result and len(test_result["choices"]) > 0:
                                if "message" in test_result["choices"][0]:
                                    # 优先使用content字段
                                    response_content = test_result["choices"][0]["message"].get("content", "")
                                    # 如果content为None，尝试使用reasoning_content字段
                                    if not response_content:
                                        response_content = test_result["choices"][0]["message"].get("reasoning_content", "")
                                    st.sidebar.info("使用标准OpenAI格式解析")
                            # 方式2：直接在顶层有content字段
                            elif "content" in test_result:
                                response_content = test_result["content"]
                                st.sidebar.info("使用顶层content字段解析")
                            # 方式3：在data字段中
                            elif "data" in test_result:
                                if isinstance(test_result["data"], list) and len(test_result["data"]) > 0:
                                    if "content" in test_result["data"][0]:
                                        response_content = test_result["data"][0]["content"]
                                        st.sidebar.info("使用data.content字段解析")
                            # 方式4：在output字段中
                            elif "output" in test_result:
                                if "content" in test_result["output"]:
                                    response_content = test_result["output"]["content"]
                                    st.sidebar.info("使用output.content字段解析")
                            # 方式5：在result字段中
                            elif "result" in test_result:
                                if "content" in test_result["result"]:
                                    response_content = test_result["result"]["content"]
                                    st.sidebar.info("使用result.content字段解析")
                            # 方式6：在text字段中
                            elif "text" in test_result:
                                response_content = test_result["text"]
                                st.sidebar.info("使用text字段解析")
                            
                            if response_content and "测试成功" in response_content:
                                st.sidebar.success("API连接测试成功！")
                                st.sidebar.info(f"响应状态：{test_response.status_code}")
                                st.sidebar.info(f"模型：{test_result.get('model', '未知')}")
                                st.sidebar.info(f"响应内容：{response_content}")
                            else:
                                st.sidebar.success("API连接测试成功，但响应内容不符合预期")
                                st.sidebar.info(f"响应状态：{test_response.status_code}")
                                st.sidebar.info(f"模型：{test_result.get('model', '未知')}")
                                st.sidebar.info(f"响应内容：{response_content if response_content else '空响应'}")
                                st.sidebar.warning("请检查完整响应JSON以了解API返回的实际格式")
                    except requests.exceptions.ConnectionError:
                        st.sidebar.error("API连接测试失败：无法连接到服务器")
                        st.sidebar.warning(f"请检查BASE_URL是否正确：{test_config['base_url']}")
                    except requests.exceptions.Timeout:
                        st.sidebar.error("API连接测试失败：请求超时")
                        st.sidebar.warning("请检查网络连接或服务器状态")
                    except requests.exceptions.HTTPError as e:
                        st.sidebar.error(f"API连接测试失败：HTTP错误 {e.response.status_code}")
                        try:
                            error_details = e.response.json()
                            if "error" in error_details:
                                st.sidebar.warning(f"错误信息：{error_details['error'].get('message', '未知错误')}")
                        except:
                            pass
                    except Exception as e:
                        st.sidebar.error(f"API连接测试失败：{str(e)}")
                        st.sidebar.warning("请检查API配置是否正确")
            else:
                missing_fields = []
                if not api_key:
                    missing_fields.append("API_KEY")
                if not base_url:
                    missing_fields.append("BASE_URL")
                if not model_name:
                    missing_fields.append("MODEL_NAME")
                if missing_fields:
                    st.sidebar.warning(f"请输入以下字段：{', '.join(missing_fields)}")
        
        # 保存配置按钮
        if st.sidebar.button("保存配置"):
            # 更新配置
            config["api_provider"] = api_provider
            
            # 根据API提供商保存相应的配置
            if api_provider == "OpenAI":
                config["openai_model"] = model_choice
                config["openai_api_key"] = api_key
            elif api_provider == "Anthropic":
                config["anthropic_model"] = model_choice
                config["anthropic_api_key"] = api_key
            elif api_provider == "Google":
                config["google_model"] = model_choice
                config["google_api_key"] = api_key
            elif api_provider == "自定义API":
                config["custom_api_key"] = api_key
                config["custom_api_base_url"] = base_url
                config["custom_api_model_name"] = model_name
            
            # 保存配置到文件
            save_config(config)
    else:
        # 模拟模式
        model_choice = "模拟模型"
        st.sidebar.info("使用模拟模式，无需API密钥")
        
        # 保存配置按钮（模拟模式）
        if st.sidebar.button("保存配置"):
            # 更新配置
            config["api_provider"] = api_provider
            
            # 保存配置到文件
            save_config(config)
    
    # 检查是否可以使用真实模型
    def can_use_real_model():
        if api_provider == "模拟模式" or model_choice == "模拟模型":
            return False
        elif api_provider == "自定义API":
            # 自定义API需要检查API_KEY、BASE_URL和MODEL_NAME
            custom_config = get_custom_api_config()
            return bool(custom_config["api_key"]) and bool(custom_config["base_url"]) and bool(custom_config["model_name"])
        else:
            # 其他模型选择，检查API密钥
            current_api_key = api_key if 'api_key' in locals() and api_key else None
            if api_provider == "OpenAI":
                current_api_key = current_api_key or config.get("openai_api_key", "")
            elif api_provider == "Anthropic":
                current_api_key = current_api_key or config.get("anthropic_api_key", "")
            elif api_provider == "Google":
                current_api_key = current_api_key or config.get("google_api_key", "")
            return bool(current_api_key)
    
    # 检查是否可以使用AI功能（包括模拟模型）
    def check_api_key():
        return can_use_real_model()
    
    # 获取实际使用的模型名称
    def get_actual_model_name():
        if model_choice == "自定义模型" and custom_model_name:
            return custom_model_name
        return model_choice
    
    # 分析类型选择
    analysis_type = st.selectbox(
        "选择分析类型",
        ["内容生成模型分析", "趋势预测分析", "受众分析"]
    )
    
    # 1. 内容生成模型分析
    if analysis_type == "内容生成模型分析":
        st.markdown('<div class="sub-header">内容生成模型分析</div>', unsafe_allow_html=True)
        
        # 小说类型选择
        novel_types = ["玄幻", "都市", "仙侠", "科幻", "悬疑", "言情", "历史", "游戏", "军事"]
        selected_type = st.selectbox("选择小说类型", novel_types)
        
        # 分析维度
        analysis_dimensions = st.multiselect(
            "选择分析维度",
            ["标题特征", "开头模式", "人物设定", "情节结构", "语言风格", "主题元素"]
        )
        
        if st.button("开始分析"):
            with st.spinner("AI正在分析热门小说特征..."):
                # 生成分析结果
                def generate_content_analysis(novel_type, dimensions):
                    analysis_results = {}
                    
                    # 检查是否使用真实模型
                    if can_use_real_model():
                        try:
                            # 根据API提供商选择不同的分析方法
                            if api_provider == "OpenAI":
                                # 使用OpenAI API进行真实分析
                                for dimension in dimensions:
                                    # 构建系统提示
                                    system_prompt = f"你是一位专业的小说分析专家，擅长分析{novel_type}题材小说的特征和模式。请基于你的专业知识，提供详细的分析结果。"
                                    
                                    # 构建用户提示
                                    if dimension == "标题特征":
                                        user_prompt = f"请分析{novel_type}题材小说的标题特征，包括：\n1. 常用关键词\n2. 标题长度分析\n3. 常见的标题结构\n请提供具体的数据和例子。"
                                    elif dimension == "开头模式":
                                        user_prompt = f"请分析{novel_type}题材小说的开头模式，包括：\n1. 常见的开头类型及占比\n2. 理想的开头字数\n3. 核心冲突的引入时机\n请提供具体的数据和例子。"
                                    elif dimension == "人物设定":
                                        user_prompt = f"请分析{novel_type}题材小说的人物设定，包括：\n1. 常见的主角身份设定\n2. 配角配置的合理性\n3. 最具张力的人物关系\n请提供具体的数据和例子。"
                                    elif dimension == "情节结构":
                                        user_prompt = f"请分析{novel_type}题材小说的情节结构，包括：\n1. 合理的章节长度\n2. 受欢迎的情节节奏\n3. 高潮的分布规律\n请提供具体的数据和例子。"
                                    elif dimension == "语言风格":
                                        user_prompt = f"请分析{novel_type}题材小说的语言风格，包括：\n1. 受欢迎的语言特点\n2. 对话内容的合理占比\n3. 重点描写的方面\n请提供具体的数据和例子。"
                                    elif dimension == "主题元素":
                                        user_prompt = f"请分析{novel_type}题材小说的主题元素，包括：\n1. 常见的核心主题\n2. 热门的元素组合\n3. 受认可的价值观表达\n请提供具体的数据和例子。"
                                    
                                    # 调用OpenAI API，使用选择的模型
                                    response = openai.ChatCompletion.create(
                                        model=model_choice,
                                        messages=[
                                            {"role": "system", "content": system_prompt},
                                            {"role": "user", "content": user_prompt}
                                        ],
                                        temperature=0.7,
                                        max_tokens=1000
                                    )
                                    
                                    # 处理响应
                                    analysis_content = response.choices[0].message.content.strip()
                                    # 将分析内容分割为要点
                                    insights = [line.strip() for line in analysis_content.split('\n') if line.strip()]
                                    analysis_results[dimension] = insights
                            elif api_provider == "自定义API":
                                # 自定义API的实现
                                st.info(f"使用自定义API进行分析")
                                
                                # 使用统一的辅助函数获取自定义API配置
                                custom_config = get_custom_api_config()
                                
                                st.info(f"当前自定义API配置：\nAPI_KEY: {'已设置' if custom_config['api_key'] else '未设置'}\nBASE_URL: {custom_config['base_url'] if custom_config['base_url'] else '未设置'}\nMODEL_NAME: {custom_config['model_name'] if custom_config['model_name'] else '未设置'}")
                                
                                # 构建通用的API调用函数
                                def call_custom_api(system_prompt, user_prompt):
                                    import requests
                                    
                                    # 检查必要的变量是否存在
                                    if not custom_config["api_key"]:
                                        st.error("API调用失败：API_KEY未设置")
                                        return None
                                    
                                    if not custom_config["base_url"]:
                                        st.error("API调用失败：BASE_URL未设置")
                                        return None
                                    
                                    if not custom_config["model_name"]:
                                        st.error("API调用失败：MODEL_NAME未设置")
                                        return None
                                    
                                    # 构建请求数据
                                    data = {
                                        "model": custom_config["model_name"],
                                        "messages": [
                                            {"role": "system", "content": system_prompt},
                                            {"role": "user", "content": user_prompt}
                                        ],
                                        "temperature": 0.7,
                                        "max_tokens": 1000
                                    }
                                    
                                    # 构建请求头
                                    headers = {
                                        "Content-Type": "application/json",
                                        "Authorization": f"Bearer {custom_config['api_key']}"
                                    }
                                    
                                    # 发送请求
                                    try:
                                        response = requests.post(
                                            f"{custom_config['base_url']}/chat/completions",
                                            json=data,
                                            headers=headers,
                                            timeout=30
                                        )
                                        response.raise_for_status()  # 检查响应状态
                                        
                                        # 处理响应
                                        result = response.json()
                                        
                                        # 安全获取响应内容
                                        try:
                                            response_content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                                            # 如果content为None，尝试使用reasoning_content字段
                                            if not response_content:
                                                response_content = result.get("choices", [{}])[0].get("message", {}).get("reasoning_content", "")
                                            return response_content
                                        except Exception as e:
                                            st.error(f"解析响应失败：{str(e)}")
                                            return None
                                    except requests.exceptions.ConnectionError:
                                        st.error("API调用失败：无法连接到服务器")
                                        st.warning(f"请检查BASE_URL是否正确：{custom_config['base_url']}")
                                        return None
                                    except requests.exceptions.Timeout:
                                        st.error("API调用失败：请求超时")
                                        st.warning("请检查网络连接或服务器状态")
                                        return None
                                    except requests.exceptions.HTTPError as e:
                                        st.error(f"API调用失败：HTTP错误 {e.response.status_code}")
                                        try:
                                            error_details = e.response.json()
                                            if "error" in error_details:
                                                st.warning(f"错误信息：{error_details['error'].get('message', '未知错误')}")
                                        except:
                                            pass
                                        return None
                                    except Exception as e:
                                        st.error(f"API调用失败：{str(e)}")
                                        return None
                                
                                # 使用自定义API进行分析
                                for dimension in dimensions:
                                    # 构建系统提示
                                    system_prompt = f"你是一位专业的小说分析专家，擅长分析{novel_type}题材小说的特征和模式。请基于你的专业知识，提供详细的分析结果。"
                                    
                                    # 构建用户提示
                                    if dimension == "标题特征":
                                        user_prompt = f"请分析{novel_type}题材小说的标题特征，包括：\n1. 常用关键词\n2. 标题长度分析\n3. 常见的标题结构\n请提供具体的数据和例子。"
                                    elif dimension == "开头模式":
                                        user_prompt = f"请分析{novel_type}题材小说的开头模式，包括：\n1. 常见的开头类型及占比\n2. 理想的开头字数\n3. 核心冲突的引入时机\n请提供具体的数据和例子。"
                                    elif dimension == "人物设定":
                                        user_prompt = f"请分析{novel_type}题材小说的人物设定，包括：\n1. 常见的主角身份设定\n2. 配角配置的合理性\n3. 最具张力的人物关系\n请提供具体的数据和例子。"
                                    elif dimension == "情节结构":
                                        user_prompt = f"请分析{novel_type}题材小说的情节结构，包括：\n1. 合理的章节长度\n2. 受欢迎的情节节奏\n3. 高潮的分布规律\n请提供具体的数据和例子。"
                                    elif dimension == "语言风格":
                                        user_prompt = f"请分析{novel_type}题材小说的语言风格，包括：\n1. 受欢迎的语言特点\n2. 对话内容的合理占比\n3. 重点描写的方面\n请提供具体的数据和例子。"
                                    elif dimension == "主题元素":
                                        user_prompt = f"请分析{novel_type}题材小说的主题元素，包括：\n1. 常见的核心主题\n2. 热门的元素组合\n3. 受认可的价值观表达\n请提供具体的数据和例子。"
                                    
                                    # 调用自定义API
                                    analysis_content = call_custom_api(system_prompt, user_prompt)
                                    
                                    if analysis_content:
                                        # 将分析内容分割为要点
                                        insights = [line.strip() for line in analysis_content.split('\n') if line.strip()]
                                        analysis_results[dimension] = insights
                                    else:
                                        # 如果API调用失败，使用模拟数据
                                        st.warning(f"自定义API调用失败，使用模拟数据进行{dimension}分析")
                                        if dimension not in analysis_results:
                                            analysis_results[dimension] = []
                                
                                # 检查是否所有维度都有分析结果
                                if not analysis_results or any(len(insights) == 0 for insights in analysis_results.values()):
                                    # 如果没有分析结果，使用模拟数据
                                    st.warning("自定义API分析失败，使用模拟数据")
                                    analysis_results = generate_mock_content_analysis(novel_type, dimensions)
                            else:
                                # 其他API提供商的实现（暂未实现，使用模拟数据）
                                st.info(f"{api_provider} API的分析功能暂未实现，使用模拟数据进行分析")
                                analysis_results = generate_mock_content_analysis(novel_type, dimensions)
                        except Exception as e:
                            st.error(f"AI分析失败：{str(e)}")
                            # 回退到模拟数据
                            analysis_results = generate_mock_content_analysis(novel_type, dimensions)
                    else:
                        # 使用模拟模型或回退到模拟数据
                        analysis_results = generate_mock_content_analysis(novel_type, dimensions)
                    
                    return analysis_results
                
                # 生成模拟分析结果（作为回退）
                def generate_mock_content_analysis(novel_type, dimensions):
                    analysis_results = {}
                    
                    # 标题特征
                    if "标题特征" in dimensions:
                        title_patterns = [
                            f"{novel_type}题材标题常用关键词：{random.sample(['最强', '无敌', '重生', '系统', '崛起', '传说', '战神', '圣王'], 4)}",
                            f"标题长度分析：2-6字标题占比 {random.randint(60, 80)}%",
                            f"标题结构：{random.choice(['动词+名词', '形容词+名词', '名词+名词'])} 结构最常见"
                        ]
                        analysis_results["标题特征"] = title_patterns
                    
                    # 开头模式
                    if "开头模式" in dimensions:
                        opening_patterns = [
                            f"常见开头类型：{random.choice(['平凡生活突变', '危机时刻', '神秘事件', '回忆倒叙'])} 占比最高",
                            f"开头字数：{random.randint(300, 800)}字左右的开头最受欢迎",
                            f"冲突引入：第{random.randint(1, 3)}段开始引入核心冲突"
                        ]
                        analysis_results["开头模式"] = opening_patterns
                    
                    # 人物设定
                    if "人物设定" in dimensions:
                        character_patterns = [
                            f"主角身份：{random.choice(['平凡人逆袭', '天才重生', '穿越者', '系统宿主'])} 设定最常见",
                            f"配角配置：平均每部作品有{random.randint(3, 7)}个重要配角",
                            f"人物关系：{random.choice(['师徒', '兄弟', '恋人', '对手'])} 关系最具张力"
                        ]
                        analysis_results["人物设定"] = character_patterns
                    
                    # 情节结构
                    if "情节结构" in dimensions:
                        plot_patterns = [
                            f"章节长度：平均每章{random.randint(2000, 4000)}字",
                            f"情节节奏：{random.choice(['慢热型', '紧凑型', '张弛有度'])} 结构更受欢迎",
                            f"高潮分布：每{random.randint(5, 15)}章出现一次小高潮"
                        ]
                        analysis_results["情节结构"] = plot_patterns
                    
                    # 语言风格
                    if "语言风格" in dimensions:
                        style_patterns = [
                            f"语言特点：{random.choice(['简洁明快', '细腻描写', '幽默风趣', '大气磅礴'])} 风格更受欢迎",
                            f"对话占比：对话内容占章节总字数的{random.randint(20, 40)}%",
                            f"描写重点：{random.choice(['场景描写', '心理描写', '动作描写', '环境描写'])} 更为突出"
                        ]
                        analysis_results["语言风格"] = style_patterns
                    
                    # 主题元素
                    if "主题元素" in dimensions:
                        theme_patterns = [
                            f"核心主题：{random.choice(['成长与蜕变', '善恶对决', '命运抗争', '爱情与责任'])} 最常见",
                            f"热门元素：{random.sample(['系统', '重生', '穿越', '异能', '修真', '末世', '星际', '古风'], 4)} 元素热度最高",
                            f"价值观表达：{random.choice(['正能量', '现实反思', '理想主义', '人文关怀'])} 主题更受认可"
                        ]
                        analysis_results["主题元素"] = theme_patterns
                    
                    return analysis_results
                
                # 获取分析结果
                analysis_results = generate_content_analysis(selected_type, analysis_dimensions)
                
                # 显示分析结果
                for dimension, insights in analysis_results.items():
                    st.markdown(f'<div class="sub-header">{dimension}</div>', unsafe_allow_html=True)
                    for insight in insights:
                        st.markdown(f"• {insight}")
                    st.markdown("---")
    
    # 2. 趋势预测分析
    elif analysis_type == "趋势预测分析":
        st.markdown('<div class="sub-header">趋势预测分析</div>', unsafe_allow_html=True)
        
        # 预测时间范围
        forecast_period = st.selectbox("预测时间范围", ["3个月", "6个月", "1年"])
        
        # 预测维度
        forecast_dimensions = st.multiselect(
            "选择预测维度",
            ["热门题材", "读者偏好", "市场趋势", "创作方向"]
        )
        
        if st.button("开始预测"):
            with st.spinner("AI正在基于历史数据预测趋势..."):
                # 生成预测结果
                def generate_trend_forecast(period, dimensions):
                    forecast_results = {}
                    
                    # 检查是否使用真实模型
                    if can_use_real_model():
                        try:
                            # 根据API提供商选择不同的预测方法
                            if api_provider == "OpenAI":
                                # 使用OpenAI API进行真实预测
                                for dimension in dimensions:
                                    # 构建系统提示
                                    system_prompt = "你是一位专业的小说市场分析师，擅长预测小说行业的发展趋势。请基于你的专业知识和对市场的理解，提供详细的趋势预测。"
                                    
                                    # 构建用户提示
                                    if dimension == "热门题材":
                                        user_prompt = f"请预测未来{period}内小说市场的热门题材趋势，包括：\n1. 可能崛起的新题材\n2. 传统题材的创新方向\n3. 各题材热度的变化趋势\n请提供具体的分析和预测数据。"
                                    elif dimension == "读者偏好":
                                        user_prompt = f"请预测未来{period}内读者阅读偏好的变化趋势，包括：\n1. 读者年龄分布的变化\n2. 阅读习惯的演变\n3. 读者互动需求的变化\n请提供具体的分析和预测数据。"
                                    elif dimension == "市场趋势":
                                        user_prompt = f"请预测未来{period}内小说市场的发展趋势，包括：\n1. 各平台的竞争格局变化\n2. 付费模式的演变\n3. IP衍生市场的发展\n请提供具体的分析和预测数据。"
                                    elif dimension == "创作方向":
                                        user_prompt = f"请预测未来{period}内小说创作的发展方向，包括：\n1. 创作重点的变化\n2. 技术在创作中的应用\n3. 内容监管的趋势\n请提供具体的分析和预测数据。"
                                    
                                    # 调用OpenAI API，使用选择的模型
                                    response = openai.ChatCompletion.create(
                                        model=model_choice,
                                        messages=[
                                            {"role": "system", "content": system_prompt},
                                            {"role": "user", "content": user_prompt}
                                        ],
                                        temperature=0.7,
                                        max_tokens=1000
                                    )
                                    
                                    # 处理响应
                                    forecast_content = response.choices[0].message.content.strip()
                                    # 将预测内容分割为要点
                                    predictions = [line.strip() for line in forecast_content.split('\n') if line.strip()]
                                    forecast_results[dimension] = predictions
                            elif api_provider == "自定义API":
                                # 自定义API的实现
                                st.info(f"使用自定义API进行预测")
                                custom_config = get_custom_api_config()
                                st.info(f"当前自定义API配置：\nAPI_KEY: {'已设置' if custom_config['api_key'] else '未设置'}\nBASE_URL: {custom_config['base_url'] if custom_config['base_url'] else '未设置'}\nMODEL_NAME: {custom_config['model_name'] if custom_config['model_name'] else '未设置'}")
                                
                                # 构建通用的API调用函数
                                def call_custom_api(system_prompt, user_prompt):
                                    import requests
                                    
                                    # 检查必要的变量是否存在
                                    if not custom_config["api_key"]:
                                        st.error("API调用失败：API_KEY未设置")
                                        return None
                                    
                                    if not custom_config["base_url"]:
                                        st.error("API调用失败：BASE_URL未设置")
                                        return None
                                    
                                    if not custom_config["model_name"]:
                                        st.error("API调用失败：MODEL_NAME未设置")
                                        return None
                                    
                                    # 构建请求数据
                                    data = {
                                        "model": custom_config["model_name"],
                                        "messages": [
                                            {"role": "system", "content": system_prompt},
                                            {"role": "user", "content": user_prompt}
                                        ],
                                        "temperature": 0.7,
                                        "max_tokens": 1000
                                    }
                                    
                                    # 构建请求头
                                    headers = {
                                        "Content-Type": "application/json",
                                        "Authorization": f"Bearer {custom_config['api_key']}"
                                    }
                                    
                                    # 发送请求
                                    try:
                                        response = requests.post(
                                            f"{custom_config['base_url']}/chat/completions",
                                            json=data,
                                            headers=headers,
                                            timeout=30
                                        )
                                        response.raise_for_status()  # 检查响应状态
                                        
                                        # 处理响应
                                        result = response.json()
                                        
                                        # 安全获取响应内容
                                        try:
                                            response_content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                                            return response_content
                                        except Exception as e:
                                            st.error(f"解析响应失败：{str(e)}")
                                            return None
                                    except requests.exceptions.ConnectionError:
                                        st.error("API调用失败：无法连接到服务器")
                                        st.warning(f"请检查BASE_URL是否正确：{custom_config['base_url']}")
                                        return None
                                    except requests.exceptions.Timeout:
                                        st.error("API调用失败：请求超时")
                                        st.warning("请检查网络连接或服务器状态")
                                        return None
                                    except requests.exceptions.HTTPError as e:
                                        st.error(f"API调用失败：HTTP错误 {e.response.status_code}")
                                        try:
                                            error_details = e.response.json()
                                            if "error" in error_details:
                                                st.warning(f"错误信息：{error_details['error'].get('message', '未知错误')}")
                                        except:
                                            pass
                                        return None
                                    except Exception as e:
                                        st.error(f"API调用失败：{str(e)}")
                                        return None
                                
                                # 使用自定义API进行预测
                                for dimension in dimensions:
                                    # 构建系统提示
                                    system_prompt = "你是一位专业的小说市场分析师，擅长预测小说行业的发展趋势。请基于你的专业知识和对市场的理解，提供详细的趋势预测。"
                                    
                                    # 构建用户提示
                                    if dimension == "热门题材":
                                        user_prompt = f"请预测未来{period}内小说市场的热门题材趋势，包括：\n1. 可能崛起的新题材\n2. 传统题材的创新方向\n3. 各题材热度的变化趋势\n请提供具体的分析和预测数据。"
                                    elif dimension == "读者偏好":
                                        user_prompt = f"请预测未来{period}内读者阅读偏好的变化趋势，包括：\n1. 读者年龄分布的变化\n2. 阅读习惯的演变\n3. 读者互动需求的变化\n请提供具体的分析和预测数据。"
                                    elif dimension == "市场趋势":
                                        user_prompt = f"请预测未来{period}内小说市场的发展趋势，包括：\n1. 各平台的竞争格局变化\n2. 付费模式的演变\n3. IP衍生市场的发展\n请提供具体的分析和预测数据。"
                                    elif dimension == "创作方向":
                                        user_prompt = f"请预测未来{period}内小说创作的发展方向，包括：\n1. 创作重点的变化\n2. 技术在创作中的应用\n3. 内容监管的趋势\n请提供具体的分析和预测数据。"
                                    
                                    # 调用自定义API
                                    forecast_content = call_custom_api(system_prompt, user_prompt)
                                    
                                    if forecast_content:
                                        # 将预测内容分割为要点
                                        predictions = [line.strip() for line in forecast_content.split('\n') if line.strip()]
                                        forecast_results[dimension] = predictions
                                    else:
                                        # 如果API调用失败，使用模拟数据
                                        st.warning(f"自定义API调用失败，使用模拟数据进行{dimension}预测")
                                        if dimension not in forecast_results:
                                            forecast_results[dimension] = []
                                
                                # 检查是否所有维度都有预测结果
                                if not forecast_results or any(len(predictions) == 0 for predictions in forecast_results.values()):
                                    # 如果没有预测结果，使用模拟数据
                                    st.warning("自定义API预测失败，使用模拟数据")
                                    forecast_results = generate_mock_trend_forecast(period, dimensions)
                            else:
                                # 其他API提供商的实现（暂未实现，使用模拟数据）
                                st.info(f"{api_provider} API的预测功能暂未实现，使用模拟数据进行预测")
                                forecast_results = generate_mock_trend_forecast(period, dimensions)
                        except Exception as e:
                            st.error(f"AI预测失败：{str(e)}")
                            # 回退到模拟数据
                            forecast_results = generate_mock_trend_forecast(period, dimensions)
                    else:
                        # 使用模拟模型或回退到模拟数据
                        forecast_results = generate_mock_trend_forecast(period, dimensions)
                    
                    return forecast_results
                
                # 生成模拟预测结果（作为回退）
                def generate_mock_trend_forecast(period, dimensions):
                    forecast_results = {}
                    
                    # 热门题材
                    if "热门题材" in dimensions:
                        hot_genres = [
                            f"{period}内可能崛起的新题材：{random.choice(['科技修真', '元宇宙冒险', '意识上传', '平行宇宙'])}",
                            f"传统题材创新方向：{random.choice(['玄幻+科技', '都市+异能', '仙侠+悬疑', '历史+穿越'])} 融合趋势明显",
                            f"题材热度变化：{random.choice(['科幻', '悬疑', '历史'])} 题材热度预计上升{random.randint(10, 30)}%"
                        ]
                        forecast_results["热门题材"] = hot_genres
                    
                    # 读者偏好
                    if "读者偏好" in dimensions:
                        reader_preferences = [
                            f"读者年龄分布：{random.choice(['Z世代', ' millennials', '中年人'])} 成为主力读者群",
                            f"阅读习惯变化：碎片化阅读需求增加，{random.randint(20, 40)}%读者偏好短章节",
                            f"互动需求：{random.randint(60, 80)}%读者希望增加与作者的互动机会"
                        ]
                        forecast_results["读者偏好"] = reader_preferences
                    
                    # 市场趋势
                    if "市场趋势" in dimensions:
                        market_trends = [
                            f"平台竞争：{random.choice(['番茄', '七猫', '起点'])} 预计市场份额增长{random.randint(5, 15)}%",
                            f"付费模式：{random.choice(['订阅', '免费+广告', '付费章节'])} 模式将成为主流",
                            f"IP衍生：{random.randint(30, 50)}%的热门小说将进行影视化改编"
                        ]
                        forecast_results["市场趋势"] = market_trends
                    
                    # 创作方向
                    if "创作方向" in dimensions:
                        creation_directions = [
                            f"创作重点：{random.choice(['人物塑造', '世界观构建', '情节创新', '语言风格'])} 将成为核心竞争力",
                            f"技术应用：AI辅助写作工具使用率预计增长{random.randint(40, 60)}%",
                            f"内容监管：对{random.choice(['价值观', '内容质量', '版权保护'])}的要求将更加严格"
                        ]
                        forecast_results["创作方向"] = creation_directions
                    
                    return forecast_results
                
                # 获取预测结果
                forecast_results = generate_trend_forecast(forecast_period, forecast_dimensions)
                
                # 显示预测结果
                for dimension, predictions in forecast_results.items():
                    st.markdown(f'<div class="sub-header">{dimension}</div>', unsafe_allow_html=True)
                    for prediction in predictions:
                        st.markdown(f"• {prediction}")
                    st.markdown("---")
    
    # 3. 受众分析
    elif analysis_type == "受众分析":
        st.markdown('<div class="sub-header">受众分析</div>', unsafe_allow_html=True)
        
        # 受众群体选择
        audience_groups = st.multiselect(
            "选择受众群体",
            ["青少年读者", "年轻白领", "中年读者", "女性读者", "男性读者", "学生群体", "职场人士"]
        )
        
        # 分析维度
        audience_dimensions = st.multiselect(
            "选择分析维度",
            ["阅读偏好", "消费习惯", "平台选择", "内容需求"]
        )
        
        if st.button("开始分析"):
            with st.spinner("AI正在分析不同受众群体阅读偏好..."):
                # 生成分析结果
                def generate_audience_analysis(audience_groups, dimensions):
                    analysis_results = {}
                    
                    # 检查是否使用真实模型
                    if can_use_real_model():
                        try:
                            # 根据API提供商选择不同的分析方法
                            if api_provider == "OpenAI":
                                # 使用OpenAI API进行真实分析
                                for group in audience_groups:
                                    group_results = {}
                                    
                                    for dimension in dimensions:
                                        # 构建系统提示
                                        system_prompt = "你是一位专业的读者行为分析师，擅长分析不同受众群体的阅读偏好和行为特征。请基于你的专业知识，提供详细的分析结果。"
                                        
                                        # 构建用户提示
                                        if dimension == "阅读偏好":
                                            user_prompt = f"请分析{group}的阅读偏好，包括：\n1. 偏好的小说题材\n2. 平均阅读时长\n3. 对作者更新频率的期望\n请提供具体的数据和例子。"
                                        elif dimension == "消费习惯":
                                            user_prompt = f"请分析{group}的阅读消费习惯，包括：\n1. 月均消费金额\n2. 付费意愿和比例\n3. 主要的消费方式\n请提供具体的数据和例子。"
                                        elif dimension == "平台选择":
                                            user_prompt = f"请分析{group}的阅读平台选择，包括：\n1. 常用的阅读平台\n2. 主要使用的阅读设备\n3. 平台忠诚度情况\n请提供具体的数据和例子。"
                                        elif dimension == "内容需求":
                                            user_prompt = f"请分析{group}的内容需求，包括：\n1. 对内容深度的需求\n2. 偏好的章节长度\n3. 对更新稳定性的重视程度\n请提供具体的数据和例子。"
                                        
                                        # 调用OpenAI API，使用选择的模型
                                        response = openai.ChatCompletion.create(
                                            model=model_choice,
                                            messages=[
                                                {"role": "system", "content": system_prompt},
                                                {"role": "user", "content": user_prompt}
                                            ],
                                            temperature=0.7,
                                            max_tokens=1000
                                        )
                                        
                                        # 处理响应
                                        analysis_content = response.choices[0].message.content.strip()
                                        # 将分析内容分割为要点
                                        insights = [line.strip() for line in analysis_content.split('\n') if line.strip()]
                                        group_results[dimension] = insights
                                    
                                    analysis_results[group] = group_results
                            elif api_provider == "自定义API":
                                # 自定义API的实现
                                st.info(f"使用自定义API进行分析")
                                
                                # 使用统一的辅助函数获取自定义API配置
                                custom_config = get_custom_api_config()
                                
                                st.info(f"当前自定义API配置：\nAPI_KEY: {'已设置' if custom_config['api_key'] else '未设置'}\nBASE_URL: {custom_config['base_url'] if custom_config['base_url'] else '未设置'}\nMODEL_NAME: {custom_config['model_name'] if custom_config['model_name'] else '未设置'}")
                                
                                # 构建通用的API调用函数
                                def call_custom_api(system_prompt, user_prompt):
                                    import requests
                                    
                                    # 检查必要的变量是否存在
                                    if not custom_config["api_key"]:
                                        st.error("API调用失败：API_KEY未设置")
                                        return None
                                    
                                    if not custom_config["base_url"]:
                                        st.error("API调用失败：BASE_URL未设置")
                                        return None
                                    
                                    if not custom_config["model_name"]:
                                        st.error("API调用失败：MODEL_NAME未设置")
                                        return None
                                    
                                    # 构建请求数据
                                    data = {
                                        "model": custom_config["model_name"],
                                        "messages": [
                                            {"role": "system", "content": system_prompt},
                                            {"role": "user", "content": user_prompt}
                                        ],
                                        "temperature": 0.7,
                                        "max_tokens": 1000
                                    }
                                    
                                    # 构建请求头
                                    headers = {
                                        "Content-Type": "application/json",
                                        "Authorization": f"Bearer {custom_config['api_key']}"
                                    }
                                    
                                    # 发送请求
                                    try:
                                        response = requests.post(
                                            f"{custom_config['base_url']}/chat/completions",
                                            json=data,
                                            headers=headers,
                                            timeout=30
                                        )
                                        response.raise_for_status()  # 检查响应状态
                                        
                                        # 处理响应
                                        result = response.json()
                                        
                                        # 安全获取响应内容
                                        try:
                                            response_content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                                            return response_content
                                        except Exception as e:
                                            st.error(f"解析响应失败：{str(e)}")
                                            return None
                                    except requests.exceptions.ConnectionError:
                                        st.error("API调用失败：无法连接到服务器")
                                        st.warning(f"请检查BASE_URL是否正确：{custom_config['base_url']}")
                                        return None
                                    except requests.exceptions.Timeout:
                                        st.error("API调用失败：请求超时")
                                        st.warning("请检查网络连接或服务器状态")
                                        return None
                                    except requests.exceptions.HTTPError as e:
                                        st.error(f"API调用失败：HTTP错误 {e.response.status_code}")
                                        try:
                                            error_details = e.response.json()
                                            if "error" in error_details:
                                                st.warning(f"错误信息：{error_details['error'].get('message', '未知错误')}")
                                        except:
                                            pass
                                        return None
                                    except Exception as e:
                                        st.error(f"API调用失败：{str(e)}")
                                        return None
                                
                                # 使用自定义API进行分析
                                for group in audience_groups:
                                    group_results = {}
                                    
                                    for dimension in dimensions:
                                        # 构建系统提示
                                        system_prompt = "你是一位专业的读者受众分析师，擅长分析不同群体的阅读偏好和消费习惯。请基于你的专业知识，提供详细的分析结果。"
                                        
                                        # 构建用户提示
                                        if dimension == "阅读偏好":
                                            user_prompt = f"请分析{group}的阅读偏好，包括：\n1. 偏好的题材类型\n2. 理想的字数长度\n3. 对更新频率的要求\n请提供具体的数据和例子。"
                                        elif dimension == "消费习惯":
                                            user_prompt = f"请分析{group}的消费习惯，包括：\n1. 月均消费金额\n2. 主要消费项目\n3. 影响付费的因素\n请提供具体的数据和例子。"
                                        elif dimension == "平台选择":
                                            user_prompt = f"请分析{group}的阅读平台选择，包括：\n1. 常用的阅读平台\n2. 主要使用的阅读设备\n3. 平台忠诚度情况\n请提供具体的数据和例子。"
                                        elif dimension == "内容需求":
                                            user_prompt = f"请分析{group}的内容需求，包括：\n1. 对内容深度的需求\n2. 偏好的章节长度\n3. 对更新稳定性的重视程度\n请提供具体的数据和例子。"
                                        
                                        # 调用自定义API
                                        analysis_content = call_custom_api(system_prompt, user_prompt)
                                        
                                        if analysis_content:
                                            # 将分析内容分割为要点
                                            insights = [line.strip() for line in analysis_content.split('\n') if line.strip()]
                                            group_results[dimension] = insights
                                        else:
                                            # 如果API调用失败，使用模拟数据
                                            st.warning(f"自定义API调用失败，使用模拟数据进行{group}的{dimension}分析")
                                            if dimension not in group_results:
                                                group_results[dimension] = []
                                    
                                    analysis_results[group] = group_results
                                
                                # 检查是否所有群体和维度都有分析结果
                                if not analysis_results or any(len(group_results) == 0 or any(len(insights) == 0 for insights in group_results.values()) for group_results in analysis_results.values()):
                                    # 如果没有分析结果，使用模拟数据
                                    st.warning("自定义API分析失败，使用模拟数据")
                                    analysis_results = generate_mock_audience_analysis(audience_groups, dimensions)
                            else:
                                # 其他API提供商的实现（暂未实现，使用模拟数据）
                                st.info(f"{api_provider} API的分析功能暂未实现，使用模拟数据进行分析")
                                analysis_results = generate_mock_audience_analysis(audience_groups, dimensions)
                        except Exception as e:
                            st.error(f"AI分析失败：{str(e)}")
                            # 回退到模拟数据
                            analysis_results = generate_mock_audience_analysis(audience_groups, dimensions)
                    else:
                        # 使用模拟模型或回退到模拟数据
                        analysis_results = generate_mock_audience_analysis(audience_groups, dimensions)
                    
                    return analysis_results
                
                # 生成模拟分析结果（作为回退）
                def generate_mock_audience_analysis(audience_groups, dimensions):
                    analysis_results = {}
                    
                    for group in audience_groups:
                        group_results = {}
                        
                        # 阅读偏好
                        if "阅读偏好" in dimensions:
                            preferences = [
                                f"偏好题材：{random.sample(['玄幻', '都市', '仙侠', '科幻', '悬疑', '言情', '历史'], 3)}",
                                f"阅读时长：平均每天阅读{random.randint(30, 180)}分钟",
                                f"更新频率：希望作者每周更新{random.randint(3, 7)}章"
                            ]
                            group_results["阅读偏好"] = preferences
                        
                        # 消费习惯
                        if "消费习惯" in dimensions:
                            consumption = [
                                f"月均消费：{random.randint(0, 200)}元",
                                f"付费意愿：{random.randint(30, 90)}%的读者愿意为优质内容付费",
                                f"消费方式：{random.choice(['订阅VIP', '打赏作者', '购买章节', '周边产品'])} 最常见"
                            ]
                            group_results["消费习惯"] = consumption
                        
                        # 平台选择
                        if "平台选择" in dimensions:
                            platforms = [
                                f"常用平台：{random.sample(['起点', '番茄', '纵横', '晋江', '七猫', '微信读书'], 3)}",
                                f"使用设备：{random.choice(['手机', '电脑', '平板'])} 占比最高",
                                f"平台忠诚度：{random.randint(40, 80)}%的读者长期使用同一平台"
                            ]
                            group_results["平台选择"] = platforms
                        
                        # 内容需求
                        if "内容需求" in dimensions:
                            content_needs = [
                                f"内容深度：{random.choice(['轻松娱乐', '思想深度', '知识科普', '情感共鸣'])} 需求最高",
                                f"章节长度：偏好每章{random.randint(1000, 5000)}字",
                                f"更新稳定性：{random.randint(60, 90)}%的读者重视作者更新稳定性"
                            ]
                            group_results["内容需求"] = content_needs
                        
                        analysis_results[group] = group_results
                    
                    return analysis_results
                
                # 获取分析结果
                analysis_results = generate_audience_analysis(audience_groups, audience_dimensions)
                
                # 显示分析结果
                for group, insights in analysis_results.items():
                    st.markdown(f'<div class="sub-header">{group}</div>', unsafe_allow_html=True)
                    for dimension, items in insights.items():
                        st.markdown(f"**{dimension}**")
                        for item in items:
                            st.markdown(f"• {item}")
                    st.markdown("---")
    
    # AI分析说明
    st.markdown('<div class="sub-header">AI分析说明</div>', unsafe_allow_html=True)
    
    if api_provider == "模拟模式" or model_choice == "模拟模型":
        st.info("当前使用模拟模式，无需API密钥")
        st.info("模拟模式使用说明：\n" +
                "1. 选择分析类型和相关参数\n" +
                "2. 点击开始分析按钮，等待处理\n" +
                "3. 查看模拟的分析结果和洞察\n" +
                "4. 如需更准确的分析，请选择真实的API提供商")
    elif api_provider == "OpenAI":
        if can_use_real_model():
            if model_choice == "自定义模型":
                st.success(f"已接入OpenAI API，使用自定义模型：{custom_model_name}，可进行实时AI分析")
                st.info("自定义模型使用说明：\n" +
                        "1. 确保输入的模型名称正确且可用\n" +
                        "2. 选择分析类型和相关参数\n" +
                        "3. 点击开始分析按钮，等待AI处理\n" +
                        "4. 查看详细的专业分析结果和洞察")
            else:
                st.success(f"已接入OpenAI API，使用模型：{model_choice}，可进行实时AI分析")
                st.info("OpenAI模型使用说明：\n" +
                        "1. 在侧边栏选择OpenAI模型并输入API密钥\n" +
                        "2. 选择分析类型和相关参数\n" +
                        "3. 点击开始分析按钮，等待AI处理\n" +
                        "4. 查看详细的专业分析结果和洞察")
        else:
            if model_choice == "自定义模型" and not custom_model_name:
                st.warning("已选择OpenAI自定义模型，但未输入模型名称")
                st.info("设置自定义模型：\n" +
                        "1. 在侧边栏输入自定义模型名称\n" +
                        "2. 输入OpenAI API密钥\n" +
                        "3. 享受更准确的AI分析结果")
            else:
                st.warning(f"已选择OpenAI API和模型：{model_choice}，但未设置API密钥")
                st.info("设置API密钥后，可使用真实的AI分析功能：\n" +
                        "1. 获取OpenAI API密钥（https://platform.openai.com/api-keys）\n" +
                        "2. 在侧边栏输入API密钥\n" +
                        "3. 享受更准确的AI分析结果")
    elif api_provider == "Anthropic" or api_provider == "Google":
        if can_use_real_model():
            st.success(f"已接入{api_provider} API，使用模型：{model_choice}")
            st.info(f"{api_provider} API使用说明：\n" +
                    "1. 在侧边栏选择{api_provider}模型并输入API密钥\n" +
                    "2. 选择分析类型和相关参数\n" +
                    "3. 点击开始分析按钮，等待AI处理\n" +
                    "4. 查看详细的专业分析结果和洞察")
            st.warning(f"注意：{api_provider} API的分析功能暂未完全实现，当前使用模拟数据进行分析")
        else:
            st.warning(f"已选择{api_provider} API和模型：{model_choice}，但未设置API密钥")
            st.info(f"设置API密钥后，可使用真实的AI分析功能：\n" +
                    f"1. 获取{api_provider} API密钥\n" +
                    "2. 在侧边栏输入API密钥\n" +
                    "3. 享受更准确的AI分析结果")
    elif api_provider == "自定义API":
        if can_use_real_model():
            st.success(f"已接入自定义API，配置完成")
            st.info("自定义API使用说明：\n" +
                    "1. 确保输入的API_KEY、BASE_URL和MODEL_NAME正确且可用\n" +
                    "2. 选择分析类型和相关参数\n" +
                    "3. 点击开始分析按钮，等待AI处理\n" +
                    "4. 查看详细的专业分析结果和洞察")
            custom_config = get_custom_api_config()
            st.info(f"当前自定义API配置：\nAPI_KEY: {'已设置' if custom_config['api_key'] else '未设置'}\nBASE_URL: {custom_config['base_url'] if custom_config['base_url'] else '未设置'}\nMODEL_NAME: {custom_config['model_name'] if custom_config['model_name'] else '未设置'}")
            st.warning(f"注意：自定义API的分析功能暂未完全实现，当前使用模拟数据进行分析")
        else:
            missing_fields = []
            custom_config = get_custom_api_config()
            if not custom_config["api_key"]:
                missing_fields.append("API_KEY")
            if not custom_config["base_url"]:
                missing_fields.append("BASE_URL")
            if not custom_config["model_name"]:
                missing_fields.append("MODEL_NAME")
            
            if missing_fields:
                st.warning(f"已选择自定义API，但缺少以下配置：{', '.join(missing_fields)}")
                st.info("设置自定义API：\n" +
                        "1. 在侧边栏输入API_KEY\n" +
                        "2. 输入BASE_URL\n" +
                        "3. 输入MODEL_NAME\n" +
                        "4. 享受更准确的AI分析结果")
    else:
        st.warning("API配置不完整，请检查设置")
        st.info("API配置指南：\n" +
                "1. 在侧边栏选择API提供商\n" +
                "2. 选择或输入模型名称\n" +
                "3. 输入相应的API密钥\n" +
                "4. 开始使用AI分析功能")
    
    # 未来扩展
    st.markdown('<div class="sub-header">未来扩展</div>', unsafe_allow_html=True)
    st.markdown("• **个性化分析**：根据作者的具体作品进行定制化分析\n" +
                "• **竞品分析**：分析同类型作品的优缺点\n" +
                "• **市场预测**：预测具体题材的市场潜力\n" +
                "• **内容生成**：基于分析结果生成小说大纲和章节内容")

# 检查点管理页面
elif page == "检查点管理":
    st.markdown('<div class="sub-header">检查点管理</div>', unsafe_allow_html=True)
    
    if "current_workspace" not in st.session_state:
        st.warning("请先从首页选择一个项目")
    else:
        current_workspace = st.session_state["current_workspace"]
        
        from novel_bot.agent.checkpoint import CheckpointManager, CheckpointConfig, CheckpointType
        
        if "checkpoint_manager" not in st.session_state or st.session_state.get("last_checkpoint_workspace") != current_workspace:
            config = CheckpointConfig(
                enabled=True,
                require_confirmation=True,
                auto_continue_after_seconds=0,
            )
            st.session_state["checkpoint_manager"] = CheckpointManager(current_workspace, config)
            st.session_state["last_checkpoint_workspace"] = current_workspace
        
        checkpoint_manager = st.session_state["checkpoint_manager"]
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 检查点列表")
            
            checkpoints = checkpoint_manager.list_checkpoints()
            
            if checkpoints:
                for cp in checkpoints:
                    with st.expander(f"**{cp['id']}** - {cp['description'] or cp['type']}"):
                        st.markdown(f"""
                        - **章节**: {cp['chapter_num']}
                        - **类型**: {cp['type']}
                        - **时间**: {cp['timestamp']}
                        - **状态**: {'✅ 已确认' if cp['confirmed'] else '⏳ 待确认'}
                        """)
                        
                        if not cp['confirmed']:
                            col_a, col_b = st.columns(2)
                            with col_a:
                                if st.button("确认", key=f"confirm_{cp['id']}"):
                                    checkpoint_manager.confirm_checkpoint(cp['id'])
                                    st.success("已确认！")
                                    st.rerun()
                            with col_b:
                                if st.button("删除", key=f"delete_{cp['id']}"):
                                    checkpoint_manager.delete_checkpoint(cp['id'])
                                    st.rerun()
            else:
                st.info("暂无检查点")
        
        with col2:
            st.markdown("### 配置")
            
            enabled = st.checkbox("启用检查点", value=True)
            require_confirm = st.checkbox("需要确认", value=True)
            auto_continue = st.number_input("自动继续秒数 (0=禁用)", min_value=0, max_value=300, value=0)
            
            st.markdown("### 检查点类型")
            checkpoint_types = st.multiselect(
                "选择需要暂停的检查点类型",
                ["after_planning", "after_review", "after_writing", "milestone"],
                default=["after_planning", "after_review", "milestone"]
            )
            
            if st.button("保存配置"):
                st.session_state["checkpoint_manager"].config.enabled = enabled
                st.session_state["checkpoint_manager"].config.require_confirmation = require_confirm
                st.session_state["checkpoint_manager"].config.auto_continue_after_seconds = auto_continue
                st.success("配置已保存！")
            
            st.markdown("### 统计")
            summary = checkpoint_manager.get_bible_summary() if hasattr(checkpoint_manager, 'get_bible_summary') else {}
            st.metric("总检查点数", len(checkpoints))
            st.metric("待确认", len([cp for cp in checkpoints if not cp['confirmed']]))

# 确认对话框组件
def show_confirmation_dialog(title: str, message: str, checkpoint_id: str = None):
    st.markdown("""
    <style>
    .confirmation-dialog {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        z-index: 1000;
        max-width: 500px;
        width: 90%;
    }
    .confirmation-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.5);
        z-index: 999;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="confirmation-overlay"></div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="confirmation-dialog">', unsafe_allow_html=True)
        st.markdown(f"### {title}")
        st.markdown(message)
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("✅ 确认继续", key=f"dialog_confirm_{checkpoint_id}", type="primary"):
                return "confirm"
        
        with col2:
            if st.button("❌ 取消", key=f"dialog_cancel_{checkpoint_id}"):
                return "cancel"
        
        with col3:
            if st.button("⏭️ 跳过此类型", key=f"dialog_skip_{checkpoint_id}"):
                return "skip"
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    return None
