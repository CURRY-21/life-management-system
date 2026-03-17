' 隐藏命令行窗口启动服务器
Set WshShell = CreateObject("WScript.Shell")

' 获取当前目录
strPath = WshShell.CurrentDirectory

' 创建启动命令 - 使用最小化窗口
strCommand = "cmd /c cd /d """ & strPath & """ && start_server.bat"

' 运行命令，窗口最小化
WshShell.Run strCommand, 7, False

' 显示提示
MsgBox "人生管理系统服务器正在后台启动..." & vbCrLf & vbCrLf & _
       "访问地址：" & vbCrLf & _
       "http://localhost:5000" & vbCrLf & vbCrLf & _
       "请稍候 5-10 秒后刷新浏览器", vbInformation, "服务器启动"

Set WshShell = Nothing
