import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

class AssetManager:
    """数字资产管理器，负责文件元数据的存储、检索和管理"""
    
    def __init__(self, db_path: str):
        """初始化资产管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建文件表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            file_id TEXT PRIMARY KEY,
            original_filename TEXT NOT NULL,
            storage_path TEXT NOT NULL,
            category TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            upload_time TEXT NOT NULL,
            last_modified TEXT NOT NULL,
            metadata TEXT,
            content TEXT
        )
        ''')
        
        # 创建标签表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            tag_id TEXT PRIMARY KEY,
            tag_name TEXT UNIQUE NOT NULL
        )
        ''')
        
        # 创建文件-标签关联表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_tags (
            file_id TEXT NOT NULL,
            tag_id TEXT NOT NULL,
            FOREIGN KEY (file_id) REFERENCES files(file_id),
            FOREIGN KEY (tag_id) REFERENCES tags(tag_id),
            PRIMARY KEY (file_id, tag_id)
        )
        ''')
        
        # 创建分类表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            category_id TEXT PRIMARY KEY,
            category_name TEXT UNIQUE NOT NULL,
            parent_category TEXT,
            description TEXT
        )
        ''')
        
        # 创建文件-分类关联表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_categories (
            file_id TEXT NOT NULL,
            category_id TEXT NOT NULL,
            FOREIGN KEY (file_id) REFERENCES files(file_id),
            FOREIGN KEY (category_id) REFERENCES categories(category_id),
            PRIMARY KEY (file_id, category_id)
        )
        ''')
        
        # 创建默认分类
        default_categories = [
            ('1', '文档', None, '各种文档文件'),
            ('2', '图片', None, '各种图片文件'),
            ('3', '音频', None, '各种音频文件'),
            ('4', '视频', None, '各种视频文件'),
            ('5', '其他', None, '其他类型文件')
        ]
        
        for category in default_categories:
            try:
                cursor.execute('''
                INSERT OR IGNORE INTO categories (category_id, category_name, parent_category, description)
                VALUES (?, ?, ?, ?)
                ''', category)
            except Exception as e:
                print(f"创建默认分类失败：{str(e)}")
        
        conn.commit()
        conn.close()
    
    def add_file(self, file_info: Dict[str, Any]) -> bool:
        """添加文件到数据库
        
        Args:
            file_info: 文件信息字典
        
        Returns:
            添加是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 准备数据
            file_id = file_info.get('file_id')
            original_filename = file_info.get('original_filename')
            storage_path = file_info.get('storage_path')
            category = file_info.get('category')
            file_type = file_info.get('file_type')
            file_size = file_info.get('file_size')
            upload_time = file_info.get('upload_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            last_modified = file_info.get('last_modified', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            metadata = json.dumps(file_info.get('metadata', {}))
            content = file_info.get('content', '')[:10000]  # 只存储前10000个字符
            
            # 插入文件记录
            cursor.execute('''
            INSERT INTO files (file_id, original_filename, storage_path, category, file_type, file_size, upload_time, last_modified, metadata, content)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (file_id, original_filename, storage_path, category, file_type, file_size, upload_time, last_modified, metadata, content))
            
            # 关联默认分类
            category_map = {
                'documents': '1',
                'images': '2',
                'audio': '3',
                'video': '4',
                'other': '5'
            }
            
            if category in category_map:
                cursor.execute('''
                INSERT INTO file_categories (file_id, category_id)
                VALUES (?, ?)
                ''', (file_id, category_map[category]))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"添加文件失败：{str(e)}")
            return False
    
    def get_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """根据文件ID获取文件信息
        
        Args:
            file_id: 文件ID
        
        Returns:
            文件信息字典，如果不存在则返回None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT * FROM files WHERE file_id = ?
            ''', (file_id,))
            
            row = cursor.fetchone()
            if not row:
                conn.close()
                return None
            
            # 转换为字典
            file_info = dict(row)
            file_info['metadata'] = json.loads(file_info['metadata']) if file_info['metadata'] else {}
            
            # 获取文件标签
            cursor.execute('''
            SELECT t.tag_name FROM tags t
            JOIN file_tags ft ON t.tag_id = ft.tag_id
            WHERE ft.file_id = ?
            ''', (file_id,))
            
            tags = [row[0] for row in cursor.fetchall()]
            file_info['tags'] = tags
            
            # 获取文件分类
            cursor.execute('''
            SELECT c.category_name FROM categories c
            JOIN file_categories fc ON c.category_id = fc.category_id
            WHERE fc.file_id = ?
            ''', (file_id,))
            
            categories = [row[0] for row in cursor.fetchall()]
            file_info['categories'] = categories
            
            conn.close()
            return file_info
        except Exception as e:
            print(f"获取文件失败：{str(e)}")
            return None
    
    def list_files(self, category: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """列出文件
        
        Args:
            category: 可选的分类筛选
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            文件列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if category:
                cursor.execute('''
                SELECT f.* FROM files f
                WHERE f.category = ?
                ORDER BY f.upload_time DESC
                LIMIT ? OFFSET ?
                ''', (category, limit, offset))
            else:
                cursor.execute('''
                SELECT * FROM files
                ORDER BY upload_time DESC
                LIMIT ? OFFSET ?
                ''', (limit, offset))
            
            rows = cursor.fetchall()
            files = []
            
            for row in rows:
                file_info = dict(row)
                file_info['metadata'] = json.loads(file_info['metadata']) if file_info['metadata'] else {}
                files.append(file_info)
            
            conn.close()
            return files
        except Exception as e:
            print(f"列出文件失败：{str(e)}")
            return []
    
    def search_files(self, keyword: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """搜索文件
        
        Args:
            keyword: 搜索关键词
            category: 可选的分类筛选
        
        Returns:
            匹配的文件列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            search_term = f"%{keyword}%"
            
            if category:
                cursor.execute('''
                SELECT * FROM files
                WHERE (original_filename LIKE ? OR content LIKE ?)
                AND category = ?
                ORDER BY upload_time DESC
                ''', (search_term, search_term, category))
            else:
                cursor.execute('''
                SELECT * FROM files
                WHERE original_filename LIKE ? OR content LIKE ?
                ORDER BY upload_time DESC
                ''', (search_term, search_term))
            
            rows = cursor.fetchall()
            files = []
            
            for row in rows:
                file_info = dict(row)
                file_info['metadata'] = json.loads(file_info['metadata']) if file_info['metadata'] else {}
                files.append(file_info)
            
            conn.close()
            return files
        except Exception as e:
            print(f"搜索文件失败：{str(e)}")
            return []
    
    def add_tag(self, tag_name: str) -> str:
        """添加标签
        
        Args:
            tag_name: 标签名称
        
        Returns:
            标签ID
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查标签是否存在
            cursor.execute('''
            SELECT tag_id FROM tags WHERE tag_name = ?
            ''', (tag_name,))
            
            row = cursor.fetchone()
            if row:
                conn.close()
                return row[0]
            
            # 生成标签ID
            import uuid
            tag_id = str(uuid.uuid4())
            
            # 插入标签
            cursor.execute('''
            INSERT INTO tags (tag_id, tag_name)
            VALUES (?, ?)
            ''', (tag_id, tag_name))
            
            conn.commit()
            conn.close()
            return tag_id
        except Exception as e:
            print(f"添加标签失败：{str(e)}")
            return ''
    
    def add_file_tag(self, file_id: str, tag_name: str) -> bool:
        """为文件添加标签
        
        Args:
            file_id: 文件ID
            tag_name: 标签名称
        
        Returns:
            添加是否成功
        """
        try:
            # 获取或创建标签
            tag_id = self.add_tag(tag_name)
            if not tag_id:
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查关联是否已存在
            cursor.execute('''
            SELECT 1 FROM file_tags WHERE file_id = ? AND tag_id = ?
            ''', (file_id, tag_id))
            
            if cursor.fetchone():
                conn.close()
                return True
            
            # 添加关联
            cursor.execute('''
            INSERT INTO file_tags (file_id, tag_id)
            VALUES (?, ?)
            ''', (file_id, tag_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"添加文件标签失败：{str(e)}")
            return False
    
    def remove_file_tag(self, file_id: str, tag_name: str) -> bool:
        """移除文件标签
        
        Args:
            file_id: 文件ID
            tag_name: 标签名称
        
        Returns:
            移除是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取标签ID
            cursor.execute('''
            SELECT tag_id FROM tags WHERE tag_name = ?
            ''', (tag_name,))
            
            row = cursor.fetchone()
            if not row:
                conn.close()
                return True
            
            tag_id = row[0]
            
            # 移除关联
            cursor.execute('''
            DELETE FROM file_tags WHERE file_id = ? AND tag_id = ?
            ''', (file_id, tag_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"移除文件标签失败：{str(e)}")
            return False
    
    def update_file_metadata(self, file_id: str, metadata: Dict[str, Any]) -> bool:
        """更新文件元数据
        
        Args:
            file_id: 文件ID
            metadata: 新的元数据
        
        Returns:
            更新是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取现有元数据
            cursor.execute('''
            SELECT metadata FROM files WHERE file_id = ?
            ''', (file_id,))
            
            row = cursor.fetchone()
            if not row:
                conn.close()
                return False
            
            existing_metadata = json.loads(row[0]) if row[0] else {}
            existing_metadata.update(metadata)
            
            # 更新元数据
            cursor.execute('''
            UPDATE files SET metadata = ? WHERE file_id = ?
            ''', (json.dumps(existing_metadata), file_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"更新文件元数据失败：{str(e)}")
            return False
    
    def delete_file(self, file_id: str) -> bool:
        """删除文件
        
        Args:
            file_id: 文件ID
        
        Returns:
            删除是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 开始事务
            conn.execute('BEGIN TRANSACTION')
            
            # 删除文件-标签关联
            cursor.execute('''
            DELETE FROM file_tags WHERE file_id = ?
            ''', (file_id,))
            
            # 删除文件-分类关联
            cursor.execute('''
            DELETE FROM file_categories WHERE file_id = ?
            ''', (file_id,))
            
            # 删除文件记录
            cursor.execute('''
            DELETE FROM files WHERE file_id = ?
            ''', (file_id,))
            
            # 提交事务
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"删除文件失败：{str(e)}")
            return False
    
    def get_file_statistics(self) -> Dict[str, Any]:
        """获取文件统计信息
        
        Returns:
            统计信息字典
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            statistics = {}
            
            # 总文件数
            cursor.execute('''
            SELECT COUNT(*) FROM files
            ''')
            statistics['total_files'] = cursor.fetchone()[0]
            
            # 按分类统计
            cursor.execute('''
            SELECT category, COUNT(*) as count FROM files
            GROUP BY category
            ''')
            category_stats = {}
            for row in cursor.fetchall():
                category_stats[row[0]] = row[1]
            statistics['category_stats'] = category_stats
            
            # 总文件大小
            cursor.execute('''
            SELECT SUM(file_size) FROM files
            ''')
            total_size = cursor.fetchone()[0]
            statistics['total_size'] = total_size or 0
            
            # 最近上传的文件
            cursor.execute('''
            SELECT file_id, original_filename, upload_time FROM files
            ORDER BY upload_time DESC
            LIMIT 5
            ''')
            recent_files = []
            for row in cursor.fetchall():
                recent_files.append({
                    'file_id': row[0],
                    'original_filename': row[1],
                    'upload_time': row[2]
                })
            statistics['recent_files'] = recent_files
            
            conn.close()
            return statistics
        except Exception as e:
            print(f"获取文件统计信息失败：{str(e)}")
            return {}
    
    def get_tags(self) -> List[str]:
        """获取所有标签
        
        Returns:
            标签列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT tag_name FROM tags
            ORDER BY tag_name
            ''')
            
            tags = [row[0] for row in cursor.fetchall()]
            conn.close()
            return tags
        except Exception as e:
            print(f"获取标签失败：{str(e)}")
            return []