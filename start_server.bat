@echo off
chcp 65001 >nul
echo ========================================
echo 人生管理系统 - 记账助手
echo ========================================
echo 正在启动服务器...
echo.

:: 切换到项目目录
cd /d "D:\工作文件\Python\TRAE\IDEA\life_management_system"

:: 激活虚拟环境（如果存在）
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

:: 启动服务器
echo 服务器启动中，请稍候...
echo.
python run.py

:: 如果服务器意外关闭，暂停显示错误信息
if errorlevel 1 (
    echo.
    echo 服务器启动失败，请检查错误信息...
    pause
)
