# 设置开机自动启动人生管理系统服务器

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "人生管理系统 - 自动启动设置" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 获取启动文件夹路径
$startupFolder = [Environment]::GetFolderPath("Startup")
$projectPath = "D:\工作文件\Python\TRAE\IDEA\life_management_system"
$batchFile = Join-Path $projectPath "start_server.bat"
$vbsFile = Join-Path $projectPath "start_server.vbs"

Write-Host "项目路径: $projectPath" -ForegroundColor Yellow
Write-Host "启动文件夹: $startupFolder" -ForegroundColor Yellow
Write-Host ""

# 创建快捷方式
$WshShell = New-Object -ComObject WScript.Shell
$shortcutPath = Join-Path $startupFolder "人生管理系统.lnk"
$Shortcut = $WshShell.CreateShortcut($shortcutPath)

# 设置快捷方式属性
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = "`"$vbsFile`""
$Shortcut.WorkingDirectory = $projectPath
$Shortcut.Description = "启动人生管理系统服务器"
$Shortcut.IconLocation = "C:\Windows\System32\shell32.dll, 14"

# 保存快捷方式
$Shortcut.Save()

Write-Host "快捷方式已创建: $shortcutPath" -ForegroundColor Green
Write-Host ""
Write-Host "设置完成！" -ForegroundColor Green
Write-Host ""
Write-Host "说明：" -ForegroundColor Cyan
Write-Host "- 服务器将在每次开机时自动启动" -ForegroundColor White
Write-Host "- 启动后请等待 5-10 秒再访问" -ForegroundColor White
Write-Host "- 访问地址: http://localhost:5000" -ForegroundColor White
Write-Host ""
Write-Host "如需取消自动启动，请删除以下文件：" -ForegroundColor Yellow
Write-Host "$shortcutPath" -ForegroundColor Yellow
Write-Host ""

# 询问是否立即启动服务器
$startNow = Read-Host "是否立即启动服务器? (Y/N)"
if ($startNow -eq "Y" -or $startNow -eq "y") {
    Write-Host "正在启动服务器..." -ForegroundColor Cyan
    Start-Process "wscript.exe" -ArgumentList "`"$vbsFile`""
    Start-Sleep -Seconds 3
    Write-Host "服务器已启动！" -ForegroundColor Green
}

Read-Host "按 Enter 键退出"
