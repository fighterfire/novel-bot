"""Mobius WebUI - 集成指南"""

# WebUI 与 Mobius 核心的集成指南

## 架构概览

WebUI 采用**三层架构**：

```
┌──────────────────────────────────────┐
│  Streamlit Frontend (webui/app.py)   │
│  - 用户界面                          │
│  - 交互和可视化                      │
└──────────────┬───────────────────────┘
               │ HTTP/WebSocket
┌──────────────▼───────────────────────┐
│  FastAPI Backend (webui/backend/server.py) │
│  - 任务管理                          │
│  - 异步执行                          │
│  - 状态追踪                          │
└──────────────┬───────────────────────┘
               │ Python API
┌──────────────▼───────────────────────┐
│  Mobius Core (src/mobius/*)          │
│  - CLI 功能                          │
│  - LLM 调用                          │
│  - 小说生成逻辑                      │
└──────────────────────────────────────┘
```

## 已实现的功能

### 1. 后端服务（webui/backend/server.py）

- **FastAPI 应用**：RESTful API + WebSocket 支持
- **任务管理系统**：创建、追踪和管理异步任务
- **日志系统**：实时日志收集和流式传输
- **五个工作流阶段**：
  - `setting_pack` - 设定补完
  - `outline` - 概要生成
  - `storyboard` - 分镜生成
  - `expand` - 正文扩写
  - `generate_full` - 完整流程（暂未实现）

**关键 API：**
```
POST /api/tasks              - 创建新任务
GET  /api/tasks/{task_id}   - 获取任务信息
GET  /api/tasks/{task_id}/logs - 获取任务日志
WS   /ws/tasks/{task_id}    - WebSocket 实时流
```

### 2. 前端应用（webui/app.py）

- **Streamlit 应用**：5 个标签页
  1. 🎯 快速生成 - 一键启动完整流程
  2. 📋 工作流 - 分步操作各个阶段
  3. 🔍 任务状态 - 实时监控任務
  4. ⚙️ 设置 - 模型和后端配置
  5. 📖 帮助 - 文档和故障排除

- **交互特性**：
  - 预设文件选择
  - 参数配置
  - 干运行模式
  - 实时日志展示

### 3. 客户端库（webui/backend/client.py）

- `MobiusClient` 类：与后端通信
- 异步接口
- 任务创建和监听
- 日志获取

## 与 Mobius 核心的集成点

### 现状

当前后端服务使用 **占位符实现**（`await asyncio.sleep(...)`）来模拟各个工作流阶段。

### 集成步骤

#### 步骤 1：在后端中导入 Mobius 核心

编辑 `webui/backend/server.py`，在 `_execute_outline` 方法中：

```python
async def _execute_outline(self, task_id: str, request: TaskRequest):
    """执行大纲生成。"""
    self.add_log(task_id, "INFO", "加载设定和配置...")
    self.update_task_status(task_id, TaskStatus.RUNNING, 20)
    
    try:
        # ===== 关键集成代码 =====
        
        # 1. 加载设定
        worldview, plot_outline = load_setting_from_yaml(request.setting_file)
        self.add_log(task_id, "INFO", f"加载设定: {worldview.name}")
        
        # 2. 创建初始状态
        state = create_initial_state(worldview, plot_outline)
        self.update_task_status(task_id, TaskStatus.RUNNING, 40)
        
        # 3. 编译并执行工作流
        outline_graph = compile_outline_graph()
        self.add_log(task_id, "INFO", "编译大纲生成图...")
        
        # 4. 执行并收集结果
        result = outline_graph.invoke(state)
        self.update_task_status(task_id, TaskStatus.RUNNING, 80)
        
        # 5. 保存结果
        output_path = Path(request.output_dir) / "outlines"
        output_path.mkdir(parents=True, exist_ok=True)
        # ... 保存逻辑
        
        self.add_log(task_id, "INFO", "大纲生成完毕")
        self.update_task_status(task_id, TaskStatus.RUNNING, 90)
        
        # ===== 集成代码结束 =====
        
    except Exception as e:
        raise RuntimeError(f"大纲生成失败: {e}")
```

#### 步骤 2：处理模型配置

后端需要从 `NovelConfig` 读取模型设置：

```python
# 在 MobiusBackend.__init__ 中
from mobius.config.settings import NovelConfig

self.config = NovelConfig()

# 在执行任务时传递给 Mobius 核心
state = create_initial_state(
    worldview,
    plot_outline,
    config=self.config,
)
```

#### 步骤 3：流式日志收集

Mobius 核心在生成过程中产生的日志需要被捕获：

```python
# 使用日志处理器捕获 Mobius 日志
import logging

class TaskLogHandler(logging.Handler):
    def __init__(self, task_id: str, backend):
        super().__init__()
        self.task_id = task_id
        self.backend = backend
    
    def emit(self, record):
        msg = self.format(record)
        self.backend.add_log(
            self.task_id,
            record.levelname,
            msg
        )

# 在 _execute_outline 中注册
handler = TaskLogHandler(task_id, self)
logging.getLogger("mobius").addHandler(handler)
```

#### 步骤 4：进度追踪

在长时间运行的任务中定期更新进度：

```python
# 在 compile_outline_graph 中可能需要添加钩子
for chapter_idx, chapter in enumerate(chapters):
    # 生成章节
    result = await generate_chapter(chapter)
    
    # 更新进度
    progress = int(40 + (chapter_idx / len(chapters)) * 50)
    self.update_task_status(task_id, TaskStatus.RUNNING, progress)
    self.add_log(task_id, "INFO", f"已生成第 {chapter_idx + 1} 章")
```

## 实现清单

### 已完成 ✅
- [x] 后端 FastAPI 应用框架
- [x] 任务管理系统（创建、追踪、日志）
- [x] Streamlit 前端界面（5 个标签页）
- [x] WebSocket 实时流支持
- [x] 参数配置面板
- [x] 干运行模式支持
- [x] 依赖管理（pyproject.toml）

### 需要完成 🚧

1. **集成 Mobius 核心**
   - [ ] 在后端中调用 `compile_*_graph()` 函数
   - [ ] 处理异步执行和错误处理
   - [ ] 实现模型配置传递

2. **实现消失路审批流程**
   - [ ] approve-setting 命令集成
   - [ ] approve-outline 命令集成
   - [ ] approve-storyboard 命令集成
   - [ ] 审批状态在 UI 中展示

3. **增强日志和监控**
   - [ ] 详细的 Token 统计（整合 token_tracker）
   - [ ] 时间估计和 ETA
   - [ ] 多任务队列管理

4. **前端优化**
   - [ ] 输出文件预览
   - [ ] 章节编辑器（人工审批界面）
   - [ ] 配置保存和加载
   - [ ] 多语言支持

## 从 CLI 迁移到 WebUI

如果你已有基于 CLI 的工作流，以下是迁移步骤：

### 原 CLI 方式
```bash
# 设定补完
mobius setting-pack preset.yaml -o output

# 人工审批
# (手动查看和编辑文件)

# 概要生成
mobius outline preset.yaml -o output

# ...更多步骤
```

### 新 WebUI 方式
```bash
# 1. 启动 WebUI
python webui/run.py

# 2. 点击 "📋 工作流"

# 3. 执行 "📦 设定补完"

# 4. 系统自动完成现有流程并更新状态

# 5. 人工审批（在 Web 界面中进行）

# 6. 继续后续步骤
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Streamlit 1.28+ |
| 后端 | FastAPI 0.104+ |
| 服务器 | Uvicorn 0.24+ |
| 核心 | LangGraph 0.4+ |
| 数据 | Pydantic 2.0+ |
| 通信 | WebSocket / HTTP |

## 部署建议

### 开发环境
```bash
python webui/run.py
```

### 生产环境
```bash
# 后端
gunicorn webui.backend.server:app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# 前端
streamlit run webui/app.py --server.headless true
```

## 下一步

1. **集成 Mobius 核心逻辑**（优先）
   - 修改 `webui/backend/server.py` 中的 `_execute_*` 方法
   - 添加日志处理器捕获 Mobius 输出
   - 测试端到端工作流

2. **实现人工审批界面**
   - 在 `webui/pages/` 中添加审批编辑器
   - 集成 approve- 命令

3. **性能优化**
   - 添加任务队列（Celery/RQ）
   - 缓存设定和生成结果
   - 支持并行任务

4. **监控和分析**
   - Token 消耗统计
   - 生成时间分析
   - 错误率统计
