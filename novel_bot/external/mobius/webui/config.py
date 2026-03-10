"""WebUI 配置文件。

在 webui 目录下创建 .streamlit/config.toml 和 secrets.toml
"""

# .streamlit/config.toml
config_toml = """
[theme]
primaryColor = "#ff4500"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "serif"

[client]
toolbarMode = "developer"
showErrorDetails = true

[logger]
level = "debug"
messageFormat = "[%(asctime)s] %(levelname)s - %(message)s"

[server]
maxUploadSize = 200
runOnSave = false
"""

# .streamlit/secrets.toml
secrets_toml = """
# LLM API 密钥（选择一个或多个）
GOOGLE_API_KEY = "your-key-here"
# OPENAI_API_KEY = "your-key-here"
# ANTHROPIC_API_KEY = "your-key-here"
# MINIMAX_API_KEY = "your-key-here"

# WebUI 后端配置
BACKEND_URL = "http://127.0.0.1:8000"

# 模型配置
MOBIUS_PROVIDER = "google"
MOBIUS_MODEL = "gemini-3-flash-preview"
MOBIUS_TEMPERATURE = 0.8
"""

if __name__ == "__main__":
    print("Streamlit 配置文件内容：")
    print("\n--- .streamlit/config.toml ---")
    print(config_toml)
    print("\n--- .streamlit/secrets.toml ---")
    print(secrets_toml)
