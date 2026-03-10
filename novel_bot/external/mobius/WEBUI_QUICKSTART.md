"""Mobius WebUI - 快速启动指南"""

# WebUI 快速启动

## ⚡ 5分钟快速开始

### 1️⃣ 安装 WebUI 组件

```bash
# 进入项目目录
cd /path/to/mobius

# 安装 WebUI 依赖
pip install -e ".[webui]"
```

### 2️⃣ 配置 API 密钥

创建文件 `webui/.streamlit/secrets.toml`：

```toml
GOOGLE_API_KEY = "your-google-api-key"
BACKEND_URL = "http://127.0.0.1:8000"
```

### 3️⃣ 启动 WebUI

**方案 A：一键启动（推荐）**

```bash
python webui/run.py
```

自动启动后端（端口 8000）和前端（端口 8501）。

**方案 B：分别启动**

```bash
# 终端 1：启动后端
python -m webui.backend.server

# 终端 2：启动前端
streamlit run webui/app.py
```

### 4️⃣ 打开浏览器

访问 http://localhost:8501

---

## 🎯 主要功能

### 快速生成
```
一键启动完整工作流
预设文件 → 自动生成小说
```

### 工作流控制
```
设定补完 → 概要生成 → 分镜生成 → 正文扩写
每步需人工审批
```

### 实时监控
```
输入任务 ID
查看实时日志、进度百分比、错误信息
```

### 灵活配置
```
选择 LLM 提供商
调整生成参数
管理输出目录
```

---

## 📋 工作流示例

### 示例 1：快速测试流程

```bash
# 1. 启动 WebUI
python webui/run.py

# 2. 点击 "🎯 快速生成" 标签
# 3. 勾选 "干运行"（不调用模型）
# 4. 点击 "🚀 一键生成"
# 5. 查看任务状态

# 预期：1-2 秒完成，验证流程可行
```

### 示例 2：完整创作流

```bash
# 1. 启动 WebUI
python webui/run.py

# 2. 点击 "📋 工作流" 标签

# 3. 执行 "📦 设定补完"
# - 输入预设文件
# - 点击执行
# - 待日志显示完成

# 4. 人工审批（离线操作）
# - 查看 output/outlines/setting_pack.json
# - 如无问题，继续

# 5. 执行 "📝 章节概要"
# - 点击执行
# - 等待完成

# 6. 执行 "🎬 章节分镜"
# - 点击执行

# 7. 执行 "✍️ 正文扩写"
# - 点击执行

# 8. 查看输出
# - 完成后在 output/ 目录中查看生成的小说
```

---

## 🔧 常见问题

### Q: 后端无法连接
**A:** 
```bash
# 检查后端是否运行
curl http://127.0.0.1:8000/api/health

# 如返回 {"status":"ok"} 则后端正常
```

### Q: API Key 错误
**A:** 
```bash
# 确保 secrets.toml 中的密钥正确
# 重新启动前端
streamlit run webui/app.py
```

### Q: 生成速度很慢
**A:** 
- 使用 `--dry-run` 测试流程
- 检查网络连接
- 查看后端日志了解具体耗时

### Q: 任务卡住
**A:**
- 查看任务监控页面的详细日志
- 检查 API 限制
- 重新启动后端服务

---

## 🚀 进阶用法

### 自定义后端地址

编辑 `webui/.streamlit/secrets.toml`：

```toml
BACKEND_URL = "http://your-server.com:8000"
```

### 使用不同的 LLM 提供商

在 WebUI 的 "⚙️ 设置" 标签中修改模型提供商和名称。

### 集成自定义 Agent

编辑 `webui/backend/server.py`，在对应的 `_execute_* 方法中添加自定义逻辑。

---

## 📚 更详细的文档

查看 [webui/README.md](./README.md) 了解：
- 完整的 API 文档
- 前端页面详细说明
- 后端架构
- 开发指南

---

## 🐛 调试

启用详细日志：

```bash
# 前端
streamlit run webui/app.py --logger.level=debug

# 后端
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from webui.backend.server import run_server
run_server()
"
```

---

## 📞 支持

问题反馈、功能建议：
- 查看任务日志识别具体错误
- 检查网络和 API 配置
- 参考本指南的故障排除部分
