#!/usr/bin/env python3
"""
创建桌面快捷方式
"""
import os
import sys

def create_shortcut():
    """创建桌面快捷方式"""
    try:
        # 获取路径
        project_path = r"D:\工作文件\Python\TRAE\IDEA\life_management_system"
        vbs_file = os.path.join(project_path, "start_server.vbs")
        
        # 获取桌面路径
        desktop_path = os.path.join(os.environ['USERPROFILE'], 'Desktop')
        shortcut_path = os.path.join(desktop_path, "人生管理系统.lnk")
        
        print("=" * 50)
        print("人生管理系统 - 快捷方式创建")
        print("=" * 50)
        print()
        print(f"项目路径: {project_path}")
        print(f"桌面路径: {desktop_path}")
        print(f"快捷方式: {shortcut_path}")
        print()
        
        # 使用PowerShell创建快捷方式
        ps_command = f'''
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut('{shortcut_path}')
        $Shortcut.TargetPath = 'wscript.exe'
        $Shortcut.Arguments = '"{vbs_file}"'
        $Shortcut.WorkingDirectory = '{project_path}'
        $Shortcut.Description = '启动人生管理系统服务器'
        $Shortcut.IconLocation = 'C:\\Windows\\System32\\shell32.dll,14'
        $Shortcut.Save()
        '''
        
        result = os.system(f'powershell -Command "{ps_command}"')
        
        if result == 0:
            print("✓ 桌面快捷方式创建成功！")
            print()
            print("=" * 50)
            print("设置完成！")
            print("=" * 50)
            print()
            print("使用方法：")
            print("1. 双击桌面上的'人生管理系统'图标启动服务器")
            print("2. 访问地址: http://localhost:5000")
            print()
            print("如需设置开机自动启动：")
            print("1. 按 Win+R，输入 shell:startup 打开启动文件夹")
            print("2. 将桌面快捷方式复制到启动文件夹中")
            print()
            
            # 询问是否立即启动
            response = input("是否立即启动服务器? (Y/N): ").strip().upper()
            if response == 'Y':
                print()
                print("正在启动服务器...")
                os.system(f'start wscript.exe "{vbs_file}"')
                import time
                time.sleep(3)
                print("服务器已启动！")
                print("访问地址: http://localhost:5000")
        else:
            print("创建快捷方式失败")
            
        input("\n按 Enter 键退出...")
        return True
        
    except Exception as e:
        print(f"错误: {str(e)}")
        input("\n按 Enter 键退出...")
        return False

if __name__ == "__main__":
    create_shortcut()
