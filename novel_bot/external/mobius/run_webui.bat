@echo off
REM Mobius WebUI 一键启动脚本（Windows）

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║          🔥 Mobius WebUI 一键启动                              ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到 Python，请先安装 Python 3.11+
    pause
    exit /b 1
)

echo ✓ 检查依赖...
python -c "import streamlit; import fastapi; import uvicorn" >nul 2>&1
if errorlevel 1 (
    echo ❌ 缺少依赖，正在安装...
    pip install -e ".[webui]"
    if errorlevel 1 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
)

echo ✓ 依赖检查完毕
echo.
echo 🚀 启动服务...
echo.

REM 启动后端
echo [1/2] 启动后端服务 (端口 8000)...
start "Mobius Backend" cmd /k python -m webui.backend.server

REM 等待后端启动
timeout /t 3 /nobreak

REM 启动前端
echo [2/2] 启动前端应用 (端口 8502)...
timeout /t 2 /nobreak

start "Mobius Frontend" cmd /k streamlit run webui/app.py --server.port=8502

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║  ✅ 服务已启动！请在浏览器中打开：                             ║
echo ║                                                                 ║
echo ║  📱 WebUI 前端: http://127.0.0.1:8502                          ║
echo ║                                                                 ║
echo ║  新建的两个窗口是后端和前端服务，请勿关闭                       ║
echo ║  关闭此窗口不会停止服务                                         ║
echo ║                                                                 ║
echo ║  如需停止，请在对应窗口按 Ctrl+C                               ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

timeout /t 5
start http://127.0.0.1:8502

echo 等待中... (按 Ctrl+C 停止)
pause
