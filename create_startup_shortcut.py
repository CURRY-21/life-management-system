#!/usr/bin/env python3
"""
创建Windows启动文件夹快捷方式
"""
import os
import sys
from win32com.client import Dispatch

def create_startup_shortcut():
    """在Windows启动文件夹中创建快捷方式"""
    try:
        # 获取路径
        project_path = r"D:\工作文件\Python\TRAE\IDEA\life_management_system"
        vbs_file = os.path.join(project_path, "start_server.vbs")
        
        # 获取启动文件夹路径
        startup_folder = os.path.join(
            os.environ['USERPROFILE'],
            r'AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup'
        )
        
        shortcut_path = os.path.join(startup_folder, "人生管理系统.lnk")
        
        print("=" * 50)
        print("人生管理系统 - 自动启动设置")
        print("=" * 50)
        print()
        print(f"项目路径: {project_path}")
        print(f"启动文件夹: {startup_folder}")
        print(f"快捷方式: {shortcut_path}")
        print()
        
        # 创建快捷方式
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = "wscript.exe"
        shortcut.Arguments = f'"{vbs_file}"'
        shortcut.WorkingDirectory = project_path
        shortcut.Description = "启动人生管理系统服务器"
        shortcut.IconLocation = r"C:\Windows\System32\shell32.dll,14"
        shortcut.save()
        
        print("✓ 快捷方式创建成功！")
        print()
        print("=" * 50)
        print("设置完成！")
        print("=" * 50)
        print()
        print("说明：")
        print("- 服务器将在每次开机时自动启动")
        print("- 启动后请等待 5-10 秒再访问")
        print("- 访问地址: http://localhost:5000")
        print()
        print("如需取消自动启动，请删除以下文件：")
        print(shortcut_path)
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
        
        input("\n按 Enter 键退出...")
        return True
        
    except Exception as e:
        print(f"错误: {str(e)}")
        input("\n按 Enter 键退出...")
        return False

if __name__ == "__main__":
    create_startup_shortcut()
