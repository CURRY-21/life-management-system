@echo off
chcp 65001 >nul
echo ========================================
echo 人生管理系统 - 自动启动设置
echo ========================================
echo.

:: 设置路径
set "PROJECT_PATH=D:\工作文件\Python\TRAE\IDEA\life_management_system"
set "STARTUP_FOLDER=%USERPROFILE%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"
set "VBS_FILE=%PROJECT_PATH%\start_server.vbs"
set "SHORTCUT_NAME=人生管理系统.lnk"

:: 创建快捷方式
echo 正在创建快捷方式...
echo 项目路径: %PROJECT_PATH%
echo 启动文件夹: %STARTUP_FOLDER%
echo.

:: 使用PowerShell创建快捷方式
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%STARTUP_FOLDER%\%SHORTCUT_NAME%'); $Shortcut.TargetPath = 'wscript.exe'; $Shortcut.Arguments = '`"%VBS_FILE%`"'; $Shortcut.WorkingDirectory = '%PROJECT_PATH%'; $Shortcut.Description = '启动人生管理系统服务器'; $Shortcut.Save()"

if %errorlevel% == 0 (
    echo.
    echo ========================================
    echo 设置完成！
    echo ========================================
    echo.
    echo 快捷方式已创建: %STARTUP_FOLDER%\%SHORTCUT_NAME%
    echo.
    echo 说明：
    echo - 服务器将在每次开机时自动启动
    echo - 启动后请等待 5-10 秒再访问
    echo - 访问地址: http://localhost:5000
    echo.
    echo 如需取消自动启动，请删除以下文件：
    echo %STARTUP_FOLDER%\%SHORTCUT_NAME%
    echo.
    choice /C YN /M "是否立即启动服务器"
    if %errorlevel% == 1 (
        echo.
        echo 正在启动服务器...
        start wscript.exe "%VBS_FILE%"
        timeout /t 3 /nobreak >nul
        echo 服务器已启动！
    )
) else (
    echo.
    echo 创建快捷方式失败，请检查权限...
)

echo.
pause
