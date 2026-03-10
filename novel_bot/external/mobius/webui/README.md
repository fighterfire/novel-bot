# Mobius WebUI - 使用指南

## 概述

Mobius WebUI 是一个完整的网页界面，提供：

- 🎯 **快速生成** - 一键启动完整创作流程
- 📋 **工作流控制** - 分步骤精细管理各个创作阶段
- 🔍 **实时监控** - WebSocket 实时日志和进度显示
- ⚙️ **灵活配置** - LLM 模型、参数、输出目录等

## 系统架构

```
┌─────────────────────────────────────┐
│      Streamlit Frontend              │
│  (app.py + pages/*)                 │
└──────────────┬──────────────────────┘
               │ HTTP/WebSocket
┌──────────────▼──────────────────────┐
│   FastAPI Backend Server             │
│  (webui/backend/server.py)          │
│  - 任务管理                          │
│  - 异步执行                          │
│  - 实时流式输出                      │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Mobius 核心引擎                    │
│  (src/mobius/*)                     │
│  - CLI 功能集成                      │
│  - LLM 调用                          │
│  - 小说生成                          │
└─────────────────────────────────────┘
```

## 安装

### 1. 安装 WebUI 依赖

```bash
cd /path/to/mobius
pip install -e ".[webui]"
```

### 2. 配置 API 密钥

创建 `webui/.streamlit/secrets.toml`：

```toml
# 必选：选择一个LLM提供商
GOOGLE_API_KEY = "your-google-api-key"
# 或
# OPENAI_API_KEY = "your-openai-api-key"

# 可选：自定义后端地址
BACKEND_URL = "http://127.0.0.1:8000"
```

## 运行

### 方案1：分别启动后端和前端（推荐）

```bash
# 终端1：启动后端服务（默认 http://127.0.0.1:8000）
python -m webui.backend.server

# 终端2：启动 Streamlit 前端（默认 http://localhost:8501）
streamlit run webui/app.py
```

### 方案2：使用启动脚本

```bash
# 后端
mobius-backend --host 127.0.0.1 --port 8000

# 前端
mobius-webui
```

## 功能说明

### 标签页 1: 🎯 快速生成

一键启动完整工作流：

```
预设 YAML → 设定补完 → 概要生成 → 分镜生成 → 正文扩写 → 完成
```

**输入**：
- 预设文件路径（`presets/ai_love_story.yaml`）
- 输出目录（`output/my_novel`）

**选项**：
- 干运行（不调用模型，用于流程验证）
- 交互式模式（逐章调整，暂未实现）

### 标签页 2: 📋 工作流

分步骤精细控制智慧型小说创作：

#### 📦 设定补完 (Setting Pack)
- 输入：预设 YAML
- 输出：结构化世界观、人物档案、时间线
- 需要人工来审批

#### 📝 章节概要 (Outline)
- 输入：已批准的设定集
- 输出：全书每章的概要、主线、思想推进
- 需要人工来审批

#### 🎬 章节分镜 (Storyboard)
- 输入：已批准的概要
- 输出：每章 4-8 个场景、因果链、降密场景
- 需要人工来审批

#### ✍️ 正文扩写 (Expand)
- 输入：已批准的分镜
- 输出：完整的小说正文
- 经过质量评审

### 标签页 3: 🔍 任务状态

实时监控任务进度：

- 任务 ID 搜索
- 实时日志流
- 进度百分比
- 错误提示
- 输出文件列表

### 标签页 4: ⚙️ 设置

- **后端配置**：服务地址、连接测试
- **模型配置**：提供商、模型名称、温度参数

### 标签页 5: 📖 帮助

- 快速开始指南
- 概念解释
- 故障排除

## APIs

后端服务提供了以下 RESTful APIs：

### 创建任务

```http
POST /api/tasks

{
  "phase": "outline",
  "setting_file": "presets/example.yaml",
  "output_dir": "output/my_novel",
  "start_chapter": 1,
  "end_chapter": 9999,
  "dry_run": false
}

Response:
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 获取任务信息

```http
GET /api/tasks/{task_id}

Response:
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "phase": "outline",
  "status": "running",
  "progress": 45,
  "logs": [
    {
      "timestamp": "2024-03-04T10:30:45.123456",
      "level": "INFO",
      "message": "加载设定文件..."
    }
  ],
  "output_dir": "output/my_novel",
  "error": "",
  "started_at": "2024-03-04T10:30:40.000000",
  "completed_at": ""
}
```

### 实时监听（WebSocket）

```javascript
const ws = new WebSocket(
  'ws://127.0.0.1:8000/ws/tasks/550e8400-e29b-41d4-a716-446655440000'
);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'log') {
    console.log(data.data);  // {timestamp, level, message}
  } else if (data.type === 'status') {
    console.log(data.data);  // {status, progress}
  } else if (data.type === 'done') {
    console.log('任务完成');
  }
};
```

## 进阶用法

### 集成自定义 LLM

编辑 `webui/backend/server.py`，在 `MobiusBackend._execute_* 方法中集成：

```python
async def _execute_outline(self, task_id: str, request: TaskRequest):
    # ... 加载设定
    
    # 调用 Mobius 核心
    from mobius.graph.novel_graph import compile_outline_graph
    
    graph = compile_outline_graph()
    result = await graph.ainvoke(initial_state)
    
    # 更新日志和进度
    self.add_log(task_id, "INFO", "大纲生成完毕")
```

### 自定义前端页面

在 `webui/pages/` 目录下添加新的 `.py` 文件：

```python
# webui/pages/04_custom_page.py
import streamlit as st

st.set_page_config(page_title="自定义页面", page_icon="✨")
st.markdown("# ✨ 自定义功能")
```

Streamlit 会自动识别并添加到导航栏。

## 故障排除

### 后端无法连接

```bash
# 1. 检查后端是否运行
ps aux | grep "webui.backend.server"

# 2. 查看后端日志
# (终端中运行后端命令查看输出)

# 3. 尝试手动连接
curl http://127.0.0.1:8000/api/health
```

### 生成速度慢

- 检查 API 配额
- 查看后端日志中的 LLM 调用时间
- 使用 `--dry-run` 测试流程

### 任务卡住

- 查看任务日志了解具体错误
- 检查网络和 API 连接
- 重新启动后端服务

## 开发指南

### 目录结构

```
webui/
├── app.py                    # Streamlit 主应用
├── config.py                 # 配置文件参考
├── __init__.py
├── pages/
│   ├── __init__.py
│   └── 03_task_monitor.py   # 任务监控页面
└── backend/
    ├── __init__.py
    ├── server.py            # FastAPI 后端
    └── client.py            # 客户端库
```

### 扩展任务类型

1. 在 `backend/server.py` 的 `TaskPhase` 中添加新阶段
2. 实现对应的 `_execute_* 方法
3. 在 `app.py` 中更新 UI

### 本地测试

```bash
# 测试客户端
python -m webui.backend.client

# 运行后端
python -m webui.backend.server --port 8001

# 运行前端
streamlit run webui/app.py --logger.level=debug
```

## 许可证

与 Mobius 项目相同。
