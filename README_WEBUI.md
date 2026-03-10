# Novel Bot WebUI 使用说明

## 项目简介

Novel Bot WebUI 是一款为 Novel Bot 设计的轻量化网页界面，旨在替代/补充命令行功能，让用户通过浏览器完成小说项目的初始化、编辑设定、启动Agent、管理草稿等操作。

## 核心功能

- **新项目初始化**：通过网页输入写作需求，自动生成小说项目和设定文件
- **多项目管理**：支持多个workspace（如workspace_1、workspace_2）的切换和管理
- **文件系统可视化**：直观展示workspace目录结构，支持实时预览Markdown内容
- **Markdown编辑器**：集成网页端Markdown编辑器，支持左右分屏编辑和预览
- **Agent交互式写作**：通过聊天界面与AI Agent交互，启动写作流程

## 技术栈

- **前端框架**：Streamlit（Python原生Web框架）
- **后端集成**：直接调用Novel Bot核心功能
- **文件存储**：与原CLI版本保持一致，使用workspace目录存储所有文件

## 安装步骤

### 1. 安装依赖

```bash
# 安装Streamlit
python -m pip install streamlit

# 确保已安装Novel Bot的依赖
python -m pip install -r requirements.txt
```

### 2. 配置环境变量

在项目根目录创建 `.env` 文件，配置API密钥（与CLI版本相同）：

```env
NVIDIA_API_KEY=your_nvidia_api_key_here
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
MODEL_NAME=moonshotai/kimi-k2.5
```

### 3. 启动WebUI

```bash
# 启动Streamlit服务器
streamlit run webui.py

# 或使用Python模块方式启动
python -m streamlit run webui.py
```

启动后，浏览器会自动打开WebUI界面，默认地址为 `http://localhost:8501`。

## 使用指南

### 1. 首页

- **项目列表**：显示所有已创建的workspace项目
- **创建新项目**：
  1. 输入写作需求（如"我想写一部末日丧尸视角下的故事"）
  2. 勾选"自动生成设定文件"（默认开启）
  3. 勾选"自动创建新workspace"（默认开启，避免覆盖现有项目）
  4. 点击"开始创建"按钮
  5. 等待项目创建完成，系统会自动生成SOUL.md、WORLD.md等设定文件

### 2. 项目管理

- **文件浏览**：侧边栏显示项目所有Markdown文件
- **文件编辑**：
  1. 在侧边栏选择要编辑的文件（如CHARACTERS.md）
  2. 在左侧编辑区修改内容
  3. 在右侧预览区实时查看渲染效果
  4. 点击"保存文件"按钮保存更改
- **目录结构**：底部显示完整的项目目录结构

### 3. Agent写作

- **聊天界面**：类似ChatGPT的交互界面
- **启动写作**：
  1. 在输入框中输入写作指令（如"开始写第一章，环境阴冷"）
  2. 点击发送按钮
  3. 等待Agent思考和生成内容
  4. 查看Agent的回复，内容会自动保存到对应文件

## 示例操作流程

### 示例1：创建末日小说项目

1. 进入WebUI首页
2. 在"写作需求"中输入："我想写一部末日丧尸视角下的故事，人类可觉醒异能，主角是普通人"
3. 勾选"自动生成设定文件"和"自动创建新workspace"
4. 点击"开始创建"
5. 等待项目创建完成
6. 进入"项目管理"页面，查看生成的设定文件
7. 点击"Agent写作"页面，开始与AI交互

### 示例2：编辑角色设定

1. 从首页选择一个项目（如workspace_1）
2. 进入"项目管理"页面
3. 在侧边栏选择"CHARACTERS.md"
4. 在左侧编辑区修改角色背景、性格等信息
5. 在右侧预览区查看修改效果
6. 点击"保存文件"按钮

### 示例3：启动Agent写作

1. 从首页选择一个项目
2. 进入"Agent写作"页面
3. 在输入框中输入："很好，现在开始写第一章的正文，注意描写环境的阴冷"
4. 点击发送按钮
5. 等待Agent生成内容
6. 查看生成的章节内容

## 注意事项

1. **文件存储**：WebUI不会改变workspace目录结构，所有编辑操作都会直接写入对应Markdown文件
2. **多项目支持**：保留了CLI版本的多workspace能力，会自动创建workspace_1、workspace_2等
3. **API密钥**：需要与CLI版本使用相同的API密钥配置
4. **性能优化**：对于大型项目，编辑大文件时可能会有轻微延迟
5. **浏览器兼容性**：建议使用Chrome、Firefox等现代浏览器

## 故障排除

### 1. Streamlit启动失败

- 确保已安装最新版本的Streamlit
- 检查Python版本是否≥3.10
- 尝试使用 `python -m streamlit run webui.py` 命令启动

### 2. Agent无响应

- 检查API密钥是否正确配置
- 确保网络连接正常
- 查看终端输出的错误信息

### 3. 文件保存失败

- 检查文件权限是否正确
- 确保磁盘空间充足
- 查看终端输出的错误信息

## 与CLI版本的关系

WebUI是CLI版本的补充，不会修改核心Agent逻辑，确保与原文件存储机制无缝对接。用户可以根据需要选择使用CLI或WebUI，两种方式操作的是同一套文件系统。

## 后续计划

- 添加文件版本历史查看功能
- 优化Markdown编辑器，支持更多编辑功能
- 添加章节大纲可视化功能
- 支持导出小说为PDF、EPUB等格式

## 联系我们

如果您在使用过程中遇到问题，或有任何建议，请随时联系我们。
