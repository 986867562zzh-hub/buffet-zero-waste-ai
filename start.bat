@echo off
chcp 65001 >nul
title ZeroDine零膳

echo ============================================
echo 🍽️  ZeroDine零膳 - Live Demo
echo ============================================
echo.

:: 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未找到Python，请先安装Python 3.9+
    pause
    exit /b 1
)

:: 安装依赖
echo 📦 安装依赖...
pip install -r requirements.txt -q
echo ✅ 依赖就绪
echo.

:: 创建上传目录
if not exist "static\uploads" mkdir static\uploads

:: 启动服务
echo 🚀 启动Web服务...
echo.
echo 📍 打开浏览器访问: http://127.0.0.1:5000
echo 💡 按 Ctrl+C 停止服务
echo ============================================
echo.

python run.py

pause
