import os

class Config:
    """系统配置类"""
    # 基础配置
    SECRET_KEY = 'your-secret-key-here'
    DEBUG = True
    
    # 文件存储配置
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    STORAGE_DIR = os.path.join(BASE_DIR, 'storage')
    UPLOAD_DIR = os.path.join(STORAGE_DIR, 'uploads')
    THUMBNAIL_DIR = os.path.join(STORAGE_DIR, 'thumbnails')
    
    # 确保存储目录存在
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(THUMBNAIL_DIR, exist_ok=True)
    
    # 允许的文件格式
    ALLOWED_EXTENSIONS = {
        # 文档格式
        'txt', 'md', 'csv', 'docx', 'xlsx', 'xls', 'pdf',
        # 图片格式
        'jpg', 'jpeg', 'png', 'gif', 'bmp',
        # 音频格式
        'mp3', 'wav', 'ogg', 'flac', 'm4a',
        # 视频格式
        'mp4', 'avi', 'mov', 'wmv', 'flv',
        # WPS格式
        'wps', 'et', 'dps'
    }
    
    # 最大文件大小 (100MB)
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024
    
    # 数据库配置
    DATABASE_URI = 'sqlite:///' + os.path.join(STORAGE_DIR, 'life_management.db')
    
    # 移动端配置
    MOBILE_API_KEY = ''
    
    # 数据同步配置
    SYNC_INTERVAL = 3600  # 默认1小时
    
    # 安全配置
    ALLOWED_ORIGINS = ['*']

# 创建配置实例
config = Config()