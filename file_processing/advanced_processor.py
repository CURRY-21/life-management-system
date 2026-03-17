import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from file_processing.file_processor import FileProcessor

class AdvancedFileProcessor:
    """高级文件处理器，提供文件验证、预处理和后处理等功能"""
    
    def __init__(self, storage_dir: str):
        """初始化高级文件处理器
        
        Args:
            storage_dir: 文件存储目录
        """
        self.storage_dir = storage_dir
        self.base_processor = FileProcessor()
        self.ensure_directories()
    
    def ensure_directories(self):
        """确保存储目录存在"""
        # 创建分类存储目录
        self.categories = {
            'documents': os.path.join(self.storage_dir, 'documents'),
            'images': os.path.join(self.storage_dir, 'images'),
            'audio': os.path.join(self.storage_dir, 'audio'),
            'video': os.path.join(self.storage_dir, 'video'),
            'other': os.path.join(self.storage_dir, 'other')
        }
        
        for category, path in self.categories.items():
            os.makedirs(path, exist_ok=True)
    
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """验证文件是否合法
        
        Args:
            file_path: 文件路径
        
        Returns:
            验证结果，包含is_valid和message字段
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return {'is_valid': False, 'message': '文件不存在'}
            
            # 检查文件大小
            max_size = 100 * 1024 * 1024  # 100MB
            if os.path.getsize(file_path) > max_size:
                return {'is_valid': False, 'message': '文件大小超过限制（最大100MB）'}
            
            # 检查文件扩展名
            _, ext = os.path.splitext(file_path.lower())
            allowed_extensions = {
                # 文档格式
                '.txt', '.md', '.csv', '.docx', '.xlsx', '.xls', '.pdf', '.wps', '.et', '.dps',
                # 图片格式
                '.jpg', '.jpeg', '.png', '.gif', '.bmp',
                # 音频格式
                '.mp3', '.wav', '.ogg', '.flac', '.m4a',
                # 视频格式
                '.mp4', '.avi', '.mov', '.wmv', '.flv'
            }
            
            if ext not in allowed_extensions:
                return {'is_valid': False, 'message': f'不支持的文件格式：{ext}'}
            
            return {'is_valid': True, 'message': '文件验证通过'}
        except Exception as e:
            return {'is_valid': False, 'message': f'文件验证失败：{str(e)}'}
    
    def get_file_category(self, file_path: str) -> str:
        """根据文件扩展名获取文件分类
        
        Args:
            file_path: 文件路径
        
        Returns:
            文件分类
        """
        _, ext = os.path.splitext(file_path.lower())
        
        if ext in ['.txt', '.md', '.csv', '.docx', '.xlsx', '.xls', '.pdf', '.wps', '.et', '.dps']:
            return 'documents'
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            return 'images'
        elif ext in ['.mp3', '.wav', '.ogg', '.flac', '.m4a']:
            return 'audio'
        elif ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv']:
            return 'video'
        else:
            return 'other'
    
    def process_and_store_file(self, file_path: str, original_filename: str) -> Dict[str, Any]:
        """处理并存储文件
        
        Args:
            file_path: 临时文件路径
            original_filename: 原始文件名
        
        Returns:
            文件处理结果，包含文件信息和存储路径
        """
        # 验证文件
        validation = self.validate_file(file_path)
        if not validation['is_valid']:
            return {
                'success': False,
                'message': validation['message'],
                'file_info': None
            }
        
        try:
            # 获取文件分类
            category = self.get_file_category(file_path)
            
            # 生成唯一文件名
            file_id = str(uuid.uuid4())
            _, ext = os.path.splitext(original_filename.lower())
            unique_filename = f"{file_id}{ext}"
            
            # 确定存储路径
            storage_path = os.path.join(self.categories[category], unique_filename)
            
            # 移动文件到存储目录
            import shutil
            shutil.copy2(file_path, storage_path)
            
            # 提取文件内容和元数据
            file_info = self.base_processor.extract_content(storage_path)
            
            # 添加额外的元数据
            file_info['file_id'] = file_id
            file_info['original_filename'] = original_filename
            file_info['category'] = category
            file_info['storage_path'] = storage_path
            file_info['upload_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            file_info['metadata'] = self.extract_metadata(storage_path, category)
            
            return {
                'success': True,
                'message': '文件处理成功',
                'file_info': file_info
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'文件处理失败：{str(e)}',
                'file_info': None
            }
    
    def extract_metadata(self, file_path: str, category: str) -> Dict[str, Any]:
        """提取文件元数据
        
        Args:
            file_path: 文件路径
            category: 文件分类
        
        Returns:
            文件元数据
        """
        metadata = {
            'file_size': os.path.getsize(file_path),
            'last_modified': datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S'),
            'category': category
        }
        
        # 根据文件分类提取特定元数据
        if category == 'images':
            try:
                from PIL import Image
                with Image.open(file_path) as img:
                    metadata['width'], metadata['height'] = img.size
                    metadata['format'] = img.format
            except Exception as e:
                metadata['image_info_error'] = str(e)
        
        elif category == 'audio':
            try:
                import mutagen
                from mutagen import File
                audio = File(file_path)
                if audio:
                    metadata['audio_format'] = audio.info.format if hasattr(audio.info, 'format') else 'Unknown'
                    if hasattr(audio.info, 'length'):
                        metadata['duration'] = audio.info.length
                    if hasattr(audio.info, 'sample_rate'):
                        metadata['sample_rate'] = audio.info.sample_rate
            except Exception as e:
                metadata['audio_info_error'] = str(e)
        
        elif category == 'video':
            try:
                import cv2
                cap = cv2.VideoCapture(file_path)
                if cap.isOpened():
                    metadata['fps'] = cap.get(cv2.CAP_PROP_FPS)
                    metadata['frame_count'] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    metadata['width'] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    metadata['height'] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    cap.release()
            except Exception as e:
                metadata['video_info_error'] = str(e)
        
        return metadata
    
    def generate_thumbnail(self, file_path: str, category: str) -> Optional[str]:
        """生成文件缩略图
        
        Args:
            file_path: 文件路径
            category: 文件分类
        
        Returns:
            缩略图路径，如果无法生成则返回None
        """
        try:
            thumbnail_dir = os.path.join(self.storage_dir, 'thumbnails')
            os.makedirs(thumbnail_dir, exist_ok=True)
            
            _, ext = os.path.splitext(file_path)
            thumbnail_name = f"{os.path.basename(file_path).replace(ext, '')}_thumbnail.jpg"
            thumbnail_path = os.path.join(thumbnail_dir, thumbnail_name)
            
            if category == 'images':
                # 为图片生成缩略图
                from PIL import Image
                with Image.open(file_path) as img:
                    img.thumbnail((200, 200))
                    img.save(thumbnail_path, 'JPEG')
                return thumbnail_path
            
            elif category == 'video':
                # 为视频生成缩略图（提取第一帧）
                import cv2
                cap = cv2.VideoCapture(file_path)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        cv2.imwrite(thumbnail_path, frame)
                    cap.release()
                    return thumbnail_path
            
            # 其他类型文件暂时不生成缩略图
            return None
        except Exception as e:
            print(f"生成缩略图失败：{str(e)}")
            return None
    
    def delete_file(self, file_id: str, category: str) -> bool:
        """删除文件
        
        Args:
            file_id: 文件ID
            category: 文件分类
        
        Returns:
            删除是否成功
        """
        try:
            # 查找文件
            category_dir = self.categories.get(category, self.categories['other'])
            
            # 遍历目录查找匹配的文件
            for filename in os.listdir(category_dir):
                if filename.startswith(file_id):
                    file_path = os.path.join(category_dir, filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        return True
            
            return False
        except Exception as e:
            print(f"删除文件失败：{str(e)}")
            return False
    
    def search_files(self, keyword: str, category: Optional[str] = None) -> list:
        """搜索文件
        
        Args:
            keyword: 搜索关键词
            category: 可选的文件分类
        
        Returns:
            匹配的文件列表
        """
        results = []
        
        # 确定搜索目录
        search_dirs = []
        if category and category in self.categories:
            search_dirs = [self.categories[category]]
        else:
            search_dirs = list(self.categories.values())
        
        # 搜索文件
        for search_dir in search_dirs:
            if os.path.exists(search_dir):
                for filename in os.listdir(search_dir):
                    if keyword.lower() in filename.lower():
                        file_path = os.path.join(search_dir, filename)
                        file_info = {
                            'filename': filename,
                            'path': file_path,
                            'size': os.path.getsize(file_path),
                            'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                        }
                        results.append(file_info)
        
        return results