#!/usr/bin/env python3
"""WSGI入口文件 - 用于云部署"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

# 创建应用实例
application = create_app()

# 用于Gunicorn
app = application

if __name__ == '__main__':
    # 从环境变量获取配置
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    
    application.run(host=host, port=port)
