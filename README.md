# Novel Bot

An intelligent novel writing agent powered by LLMs. It adopts the "Filesystem as Memory" design philosophy, interacting with the user through a continuous Agent Loop to maintain the coherence of long-form novels.

[中文文档](#中文文档)

---

## Key Features

- **Multi-Agent Architecture**: Five specialized agents (Coordinator, Planner, Writer, Reviewer, Polisher) with role-based permissions and skill bindings.
- **Agent Architecture**: Not just a linear script, but a continuous process capable of thinking and self-reflection.
- **Filesystem as Database**: All Memory, Persona (Soul), and Settings (World) are stored directly as Markdown files in `workspace/`, making it easy for users to manually intervene and modify at any time.
- **AI Auto-Generate Settings**: Automatically generate core setting files (SOUL.md, USER.md, TONE.md, CHARACTERS.md, WORLD.md, STORY_SUMMARY.md) based on writing requirements.
- **Dual Memory System**:
    - **Global Memory**: Records worldview changes and important plot nodes (`memory/MEMORY.md`).
    - **Chapter Memory**: Records detailed summaries of recent chapters (`memory/chapters/`) to prevent context overflow.
- **Story Bible System**: Track characters, suspense, and foreshadowing across chapters.
- **Checkpoint Management**: Pause and confirm at key stages with state persistence.
- **Review System**: 10-dimension quality scoring with automatic rewrite mechanism.
- **OpenAI Compatibility**: Supports models compatible with the OpenAI API.
- **WebUI Support**: Lightweight web interface for browser-based novel writing.

## Multi-Agent Architecture

Novel Bot implements a sophisticated multi-agent system with specialized roles:

| Agent | Role | Permissions |
|-------|------|-------------|
| **Coordinator** | Global coordination and task distribution | Full access |
| **Planner** | Outline, character, and worldview planning | Read all, Write bible/, plans/ |
| **Writer** | Chapter content writing | Read bible/, plans/, Write drafts/ |
| **Reviewer** | Quality checking and review reports | Read all, Write reviews/ |
| **Polisher** | Language refinement and style polish | Read drafts/, reviews/, Write drafts/ |

### Chapter Workflow

The chapter creation process follows a structured workflow:

```
Planning → Writing → Review → Revision → Polish → Archive
    ↓          ↓         ↓         ↓         ↓
 Checkpoint Checkpoint Checkpoint Checkpoint Checkpoint
```

### Review System

10-dimension quality scoring:
- Plot Coherence, Character Consistency, Dialogue Quality
- Narrative Pacing, Description Technique, Emotional Expression
- Suspense Setup, Information Reveal, Language Style, Overall Quality

**Verdict Thresholds:**
- **Pass**: Score ≥ 35
- **Needs Revision**: Score 25-34
- **Needs Rewrite**: Score < 25

## Installation

### 1. Prerequisites

Ensure your Python version is >= 3.10.

```bash
git clone https://github.com/xiaoxiaoxiaotao/novel-bot.git
cd novel-bot
```

### 2. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Configure Model

Create a `.env` file in the project root directory and fill in your API Key and Base URL (you can refer to the `.env.example` file).

The author uses the API from [Try NVIDIA NIM APIs](https://build.nvidia.com/), employing the `moonshotai/kimi-k2.5` model.

```env
NVIDIA_API_KEY=your_nvidia_api_key_here
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
MODEL_NAME=moonshotai/kimi-k2.5
```

## Usage

### 1. Initialize Workspace

When running for the first time, you need to initialize the workspace. This will create the `workspace` directory and necessary setting files (SOUL.md, WORLD.md, etc.).

**Basic usage (default template):**
```bash
python -m novel_bot init
```

**Auto-generate settings from writing requirements:**
```bash
python -m novel_bot init --prompt "I want to write a zombie apocalypse story where humans can awaken superpowers"
```

**Command line arguments:**
- `--path`: Specify workspace path (default: workspace)
- `--prompt` / `-p`: Input writing requirements, AI will auto-generate setting files
- `--overwrite` / `-o`: Overwrite existing setting files
- `--auto` / `-a`: If workspace exists, auto-create new workspace (e.g., workspace_1, workspace_2)

### 2. Start Agent

Launch the interactive writing interface:

```bash
python -m novel_bot start
```

**Start specific project:**
```bash
python -m novel_bot start --workspace workspace_1
```

### 3. Workflow Commands (New)

**Start interactive chapter workflow:**
```bash
python -m novel_bot workflow run --chapter 1 --end 5
```

**Auto mode (no pauses):**
```bash
python -m novel_bot workflow run --chapter 1 --end 5 --auto
```

**Manage checkpoints:**
```bash
python -m novel_bot workflow checkpoints
```

**View story bible:**
```bash
python -m novel_bot workflow bible --show suspense
```

**Workflow options:**
- `--chapter` / `-c`: Start chapter number
- `--end` / `-e`: End chapter number
- `--auto` / `-a`: Auto mode without pauses
- `--max-revisions`: Maximum revision attempts (default: 3)

### 4. Interaction Example

Command the Agent to write as an "Editor" in the terminal:

```text
Editor > I want to write a story from a zombie apocalypse perspective where humans can awaken superpowers. Please write some settings for characters, style, and plot, and generate a worldview and outline.

Thinking...
Agent: [Generated content...]

Editor > Great. Now start writing the first chapter. Focus on describing the cold and gloomy environment.

Thinking...
Agent: [Generated text saved to file]
```

## WebUI

Novel Bot WebUI is a lightweight web interface designed for Novel Bot, allowing users to initialize projects, edit settings, start Agent, and manage drafts through a browser.

### Install WebUI Dependencies

```bash
python -m pip install streamlit
```

### Start WebUI

```bash
streamlit run webui.py
```

Or use Python module:

```bash
python -m streamlit run webui.py
```

After starting, the browser will automatically open the WebUI interface at `http://localhost:8501`.

### WebUI Features

- **New Project Initialization**: Input writing requirements through the web page to automatically generate novel projects and setting files
- **Multi-Project Management**: Support switching and managing multiple workspaces (e.g., workspace_1, workspace_2)
- **File System Visualization**: Intuitively display workspace directory structure, support real-time preview of Markdown content
- **Markdown Editor**: Integrated web-based Markdown editor with split-screen editing and preview
- **Agent Interactive Writing**: Interact with AI Agent through chat interface to start the writing process
- **Checkpoint Management**: View, confirm, and manage workflow checkpoints
- **Story Bible**: Track suspense, foreshadowing, and character development

### WebUI Usage

1. **Home Page**: View all created workspace projects, create new projects
2. **Project Management**: Browse and edit project files (SOUL.md, CHARACTERS.md, etc.)
3. **Smart Writing Assistant**: Chat interface for AI-assisted writing
4. **Checkpoint Management**: Manage workflow checkpoints and confirmations

## Directory Structure

```text
novel_bot/          # Core Code
  agent/            # Agent Logic (Loop, Memory, Tools)
    agents/         # Multi-Agent System
      base.py       # SubAgent Base Class
      coordinator.py # Coordinator Agent
      reviewer.py   # Reviewer Agent
      workflow.py   # ChapterWorkflow
    bible.py        # Story Bible Manager
    checkpoint.py   # Checkpoint Manager
    context.py      # Context Builder
    memory.py       # Memory Store
    skills.py       # Skills Loader
    tools.py        # Tool Registry
  cli/              # CLI Entry Point
    main.py         # Main CLI
    workflow.py     # Workflow CLI
  config/           # Configuration Loading
  skills/           # Built-in Skills (12 skills)
workspace/          # [Auto-Generated] Novel Data Storage (Git Ignored)
  drafts/           # Novel Drafts (e.g. drafts/chapter_01.md)
  reviews/          # Review Reports
  checkpoints/      # Checkpoint Data
  bible/            # Story Bible
    suspense.md     # Suspense Tracking
    foreshadow.md   # Foreshadowing Tracking
    characters.md   # Character Development
  SOUL.md           # AI Persona / Writing Style
  USER.md           # User's Writing Goals and Requirements
  TONE.md           # Novel Tone, Style and Narrative Features
  CHARACTERS.md     # Character Cards
  WORLD.md          # Worldview Settings
  STORY_SUMMARY.md  # Full Story Plot Summary
  memory/           # Automatically Managed Memory System
    chapters/       # Chapter Memory
```

## Skills System

Novel Bot includes 12 built-in skills:

| Skill | Description |
|-------|-------------|
| planner-skill | Outline and planning guidance |
| writer-skill | Writing techniques and style |
| reviewer-skill | Quality review criteria |
| polisher-skill | Language refinement techniques |
| salt-story | Salt-selection genre conventions |
| mystery-novel-conventions | Mystery genre guidelines |
| romance-novel-conventions | Romance genre guidelines |
| novel-evaluator | Novel quality evaluation |
| bible-template | Story bible templates |
| writer-tools | Mobius integration tools |
| skill-creator | Skill creation helper |
| summarize | Content summarization |

## Troubleshooting

### Streamlit startup fails
- Ensure the latest version of Streamlit is installed
- Check if Python version >= 3.10
- Try using `python -m streamlit run webui.py` command to start

### Agent not responding
- Check if API key is correctly configured
- Ensure network connection is normal
- View error information in terminal output

### File save fails
- Check if file permissions are correct
- Ensure sufficient disk space
- View error information in terminal output

## Acknowledgements

- Portions of this project were inspired by and adapt code from [nanobot](https://github.com/HKUDS/nanobot.git).

---

# 中文文档

一个智能小说写作 Agent。它采用 "Filesystem as Memory"（文件即记忆）的设计理念，通过持续的 Agent Loop 与用户交互，能够维护长篇小说的连贯性。

## 核心特性

- **多 Agent 架构**：五个专业 Agent（协调者、规划师、写作者、审查者、润色者），具备角色权限和技能绑定。
- **Agent 架构**：不再是线性的脚本，而是一个会思考、会自省的持续运行进程。
- **文件即数据库**：所有的记忆（Memory）、人设（Soul）、设定（World）都以 Markdown 文件直接存储在 `workspace/` 中，方便用户随时人工干预和修改。
- **AI 自动生成设定**：支持根据写作需求自动生成小说的核心设定文件（SOUL.md, USER.md, TONE.md, CHARACTERS.md, WORLD.md, STORY_SUMMARY.md），快速搭建小说框架。
- **双重记忆系统**：
    - **长期记忆 (Global Memory)**：记录世界观变迁、重要剧情节点 (`memory/MEMORY.md`)。
    - **短期记忆 (Chapter Memory)**：记录最近章节的详细摘要 (`memory/chapters/`)，防止上下文超长。
- **故事圣经系统**：跨章节追踪角色、悬念和伏笔。
- **检查点管理**：在关键阶段暂停确认，支持状态持久化。
- **审查系统**：10维度质量评分，自动重写机制。
- **OpenAI 兼容性**：支持兼容 OpenAI 接口的模型。
- **WebUI 支持**：提供轻量化网页界面，支持浏览器端小说写作。

## 多 Agent 架构

Novel Bot 实现了复杂的多 Agent 系统，各角色分工明确：

| Agent | 角色 | 权限 |
|-------|------|------|
| **Coordinator** | 全局协调和任务分配 | 完全访问 |
| **Planner** | 大纲、人物、世界观规划 | 读取全部，写入 bible/、plans/ |
| **Writer** | 章节正文撰写 | 读取 bible/、plans/，写入 drafts/ |
| **Reviewer** | 质量检查和审查报告 | 读取全部，写入 reviews/ |
| **Polisher** | 语言精修和风格润色 | 读取 drafts/、reviews/，写入 drafts/ |

### 章节工作流

章节创作遵循结构化工作流：

```
规划 → 写作 → 审查 → 修改 → 润色 → 归档
  ↓      ↓      ↓      ↓      ↓
检查点  检查点  检查点  检查点  检查点
```

### 审查系统

10维度质量评分：
- 情节连贯性、角色一致性、对话质量
- 叙事节奏、描写技巧、情感表达
- 悬念设置、信息揭示、语言风格、整体质量

**裁决阈值：**
- **通过**：分数 ≥ 35
- **需修改**：分数 25-34
- **需重写**：分数 < 25

## 部署安装

### 1. 环境准备

确保你的 Python 版本 >= 3.10。

```bash
git clone https://github.com/xiaoxiaoxiaotao/novel-bot.git
cd novel-bot
```

### 2. 安装依赖

```bash
python -m pip install -r requirements.txt
```

### 3. 配置模型

在项目根目录创建 `.env` 文件，填入你的 API Key 和 Base URL（可以参考.env.example文件）。

作者使用的是 [Try NVIDIA NIM APIs](https://build.nvidia.com/) 上的api，采用的 moonshotai/kimi-k2.5 模型。

```env
NVIDIA_API_KEY=your_nvidia_api_key_here
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
MODEL_NAME=moonshotai/kimi-k2.5
```

## 使用方法

### 1. 初始化工作区

首次运行时，需要初始化工作区。这将创建 `workspace` 目录和必要的设定文件（SOUL.md, WORLD.md 等）。

**基本用法（使用默认模板）：**
```bash
python -m novel_bot init
```

**根据写作需求自动生成设定文件：**
```bash
python -m novel_bot init --prompt "我想写一部关于末日丧尸视角下的故事，人类可以觉醒异能，主角是一个在末日中挣扎求生的普通人"
```

**指定工作区路径：**
```bash
python -m novel_bot init --path "my_workspace"
```

**覆盖已存在的设定文件：**
```bash
python -m novel_bot init --prompt "你的写作需求" --overwrite
```

*提示：你可以直接编辑 `workspace/` 下的 Markdown 文件来修改 AI 的人设或小说的大纲。*

**命令行参数说明：**
- `--path`：指定工作区路径（默认：workspace）
- `--prompt` / `-p`：输入写作需求，AI会自动生成设定文件
- `--overwrite` / `-o`：覆盖已存在的设定文件
- `--auto` / `-a`：如果工作区已存在，自动创建新工作区（如 workspace_1, workspace_2）

### 多项目写作

如果你需要同时进行多个小说项目的写作，可以使用 `--auto` 参数自动创建新的工作区：

**创建第一个项目：**
```bash
python -m novel_bot init --auto --prompt "我想写一部关于末日丧尸视角下的故事"
```
这将创建 `workspace` 目录。

**创建第二个项目：**
```bash
python -m novel_bot init --auto --prompt "我想写一部关于仙侠修真的故事"
```
这将自动创建 `workspace_1` 目录。

**启动指定项目：**
```bash
python -m novel_bot start --workspace workspace_1
```

### 2. 启动 Agent

启动交互式写作界面：

```bash
python -m novel_bot start
```

### 3. 工作流命令（新功能）

**启动交互式章节工作流：**
```bash
python -m novel_bot workflow run --chapter 1 --end 5
```

**自动模式（无暂停）：**
```bash
python -m novel_bot workflow run --chapter 1 --end 5 --auto
```

**管理检查点：**
```bash
python -m novel_bot workflow checkpoints
```

**查看故事圣经：**
```bash
python -m novel_bot workflow bible --show suspense
```

**工作流参数：**
- `--chapter` / `-c`：开始章节号
- `--end` / `-e`：结束章节号
- `--auto` / `-a`：自动模式，不暂停
- `--max-revisions`：最大修改次数（默认：3）

### 4. 交互示例

在终端中作为 "Editor" (编辑) 指挥 Agent 写作：

```text
Editor > 我想撰写一个末日丧尸视角下的故事，人类可以觉醒异能，请你为小说撰写一些人物、风格、情节的设定，生成世界观和大纲。

Thinking...
Agent: [生成了...]

Editor > 很好，现在开始写第一章的正文，注意描写环境的阴冷。

Thinking...
Agent: [生成正文并保存到文件]
```

## WebUI 网页界面

Novel Bot WebUI 是一款为 Novel Bot 设计的轻量化网页界面，旨在替代/补充命令行功能，让用户通过浏览器完成小说项目的初始化、编辑设定、启动Agent、管理草稿等操作。

### 安装 WebUI 依赖

```bash
python -m pip install streamlit
```

### 启动 WebUI

```bash
streamlit run webui.py
```

或使用 Python 模块方式：

```bash
python -m streamlit run webui.py
```

启动后，浏览器会自动打开 WebUI 界面，默认地址为 `http://localhost:8501`。

### WebUI 核心功能

- **新项目初始化**：通过网页输入写作需求，自动生成小说项目和设定文件
- **多项目管理**：支持多个workspace（如workspace_1、workspace_2）的切换和管理
- **文件系统可视化**：直观展示workspace目录结构，支持实时预览Markdown内容
- **Markdown编辑器**：集成网页端Markdown编辑器，支持左右分屏编辑和预览
- **Agent交互式写作**：通过聊天界面与AI Agent交互，启动写作流程
- **检查点管理**：查看、确认和管理工作流检查点
- **故事圣经**：追踪悬念、伏笔和角色发展

### WebUI 使用指南

#### 1. 首页

- **项目列表**：显示所有已创建的workspace项目
- **创建新项目**：
  1. 输入写作需求（如"我想写一部末日丧尸视角下的故事"）
  2. 勾选"自动生成设定文件"（默认开启）
  3. 勾选"自动创建新workspace"（默认开启，避免覆盖现有项目）
  4. 点击"开始创建"按钮
  5. 等待项目创建完成，系统会自动生成SOUL.md、WORLD.md等设定文件

#### 2. 项目管理

- **文件浏览**：侧边栏显示项目所有Markdown文件
- **文件编辑**：
  1. 在侧边栏选择要编辑的文件（如CHARACTERS.md）
  2. 在左侧编辑区修改内容
  3. 在右侧预览区实时查看渲染效果
  4. 点击"保存文件"按钮保存更改
- **目录结构**：底部显示完整的项目目录结构

#### 3. 智能写作助手

- **聊天界面**：类似ChatGPT的交互界面
- **启动写作**：
  1. 在输入框中输入写作指令（如"开始写第一章，环境阴冷"）
  2. 点击发送按钮
  3. 等待Agent思考和生成内容
  4. 查看Agent的回复，内容会自动保存到对应文件

#### 4. 检查点管理

- **检查点列表**：显示所有检查点及其状态
- **确认操作**：对待确认检查点进行确认或删除
- **配置管理**：设置暂停行为和自动继续时间

### WebUI 示例操作流程

#### 示例1：创建末日小说项目

1. 进入WebUI首页
2. 在"写作需求"中输入："我想写一部末日丧尸视角下的故事，人类可觉醒异能，主角是普通人"
3. 勾选"自动生成设定文件"和"自动创建新workspace"
4. 点击"开始创建"
5. 等待项目创建完成
6. 进入"项目管理"页面，查看生成的设定文件
7. 点击"智能写作助手"页面，开始与AI交互

#### 示例2：编辑角色设定

1. 从首页选择一个项目（如workspace_1）
2. 进入"项目管理"页面
3. 在侧边栏选择"CHARACTERS.md"
4. 在左侧编辑区修改角色背景、性格等信息
5. 在右侧预览区查看修改效果
6. 点击"保存文件"按钮

#### 示例3：启动Agent写作

1. 从首页选择一个项目
2. 进入"智能写作助手"页面
3. 在输入框中输入："很好，现在开始写第一章的正文，注意描写环境的阴冷"
4. 点击发送按钮
5. 等待Agent生成内容
6. 查看生成的章节内容

## 目录结构

```text
novel_bot/          # 核心代码
  agent/            # Agent 逻辑 (Loop, Memory, Tools)
    agents/         # 多 Agent 系统
      base.py       # SubAgent 基类
      coordinator.py # 协调者 Agent
      reviewer.py   # 审查者 Agent
      workflow.py   # 章节工作流
    bible.py        # 故事圣经管理器
    checkpoint.py   # 检查点管理器
    context.py      # 上下文构建器
    memory.py       # 记忆存储
    skills.py       # 技能加载器
    tools.py        # 工具注册表
  cli/              # 命令行入口
    main.py         # 主 CLI
    workflow.py     # 工作流 CLI
  config/           # 配置加载
  skills/           # 内置技能 (12个)
workspace/          # [自动生成] 小说的数据存储位置 (Git 忽略)
  drafts/           # 小说正文草稿 (e.g. drafts/chapter_01.md)
  reviews/          # 审查报告
  checkpoints/      # 检查点数据
  bible/            # 故事圣经
    suspense.md     # 悬念追踪
    foreshadow.md   # 伏笔追踪
    characters.md   # 角色发展
  SOUL.md           # AI 的人设/写作风格
  USER.md           # 用户的写作目标和需求
  TONE.md           # 小说的基调、风格和叙事特点
  CHARACTERS.md     # 角色卡
  WORLD.md          # 世界观设定
  STORY_SUMMARY.md  # 全书剧情梗概
  memory/           # 自动管理的记忆系统
    chapters/       # 章节记忆
```

## 技能系统

Novel Bot 包含 12 个内置技能：

| 技能 | 描述 |
|-------|------|
| planner-skill | 大纲和规划指导 |
| writer-skill | 写作技巧和风格 |
| reviewer-skill | 质量审查标准 |
| polisher-skill | 语言润色技巧 |
| salt-story | 盐选题材惯例 |
| mystery-novel-conventions | 悬疑题材指南 |
| romance-novel-conventions | 言情题材指南 |
| novel-evaluator | 小说质量评估 |
| bible-template | 故事圣经模板 |
| writer-tools | Mobius 集成工具 |
| skill-creator | 技能创建助手 |
| summarize | 内容摘要 |

## 故障排除

### Streamlit 启动失败
- 确保已安装最新版本的Streamlit
- 检查Python版本是否≥3.10
- 尝试使用 `python -m streamlit run webui.py` 命令启动

### Agent 无响应
- 检查API密钥是否正确配置
- 确保网络连接正常
- 查看终端输出的错误信息

### 文件保存失败
- 检查文件权限是否正确
- 确保磁盘空间充足
- 查看终端输出的错误信息

## 注意事项

1. **文件存储**：WebUI不会改变workspace目录结构，所有编辑操作都会直接写入对应Markdown文件
2. **多项目支持**：保留了CLI版本的多workspace能力，会自动创建workspace_1、workspace_2等
3. **API密钥**：需要与CLI版本使用相同的API密钥配置
4. **性能优化**：对于大型项目，编辑大文件时可能会有轻微延迟
5. **浏览器兼容性**：建议使用Chrome、Firefox等现代浏览器

## 致谢

- 本项目的部分代码参考和借鉴了 [nanobot](https://github.com/HKUDS/nanobot.git) 项目。
