#!/usr/bin/env python3
"""人生管理系统主入口文件"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.app import create_app

if __name__ == '__main__':
    print("人生管理系统启动中...")
    print("=======================================")
    
    # 创建应用实例
    app = create_app()
    
    # 从环境变量获取配置（支持云部署）
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    print(f"访问地址: http://localhost:{port}")
    if not os.environ.get('RAILWAY_ENVIRONMENT'):
        # 本地运行时显示网络地址
        try:
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            print(f"网络访问: http://{local_ip}:{port}")
        except:
            pass
    print("按 Ctrl+C 停止服务")
    print("=======================================")
    
    # 启动Flask应用
    app.run(host=host, port=port, debug=debug)
