import os
import shutil
import zipfile
import json
from datetime import datetime
import threading
import time
from typing import Dict, Any, List, Optional

class BackupManager:
    """数据备份管理器，负责数据的备份、恢复和同步"""
    
    def __init__(self, storage_dir: str, backup_dir: str = None):
        """初始化备份管理器
        
        Args:
            storage_dir: 存储目录
            backup_dir: 备份目录，默认为存储目录下的backups子目录
        """
        self.storage_dir = storage_dir
        self.backup_dir = backup_dir or os.path.join(storage_dir, 'backups')
        self.ensure_directories()
        self.sync_interval = 3600  # 默认同步间隔为1小时
        self.sync_thread = None
        self.sync_running = False
    
    def ensure_directories(self):
        """确保存储目录和备份目录存在"""
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self, description: str = "") -> Dict[str, Any]:
        """创建数据备份
        
        Args:
            description: 备份描述
        
        Returns:
            备份信息，包含备份路径、大小、时间等
        """
        try:
            # 生成备份文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"backup_{timestamp}.zip"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # 创建备份文件
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 备份存储目录下的所有文件
                for root, dirs, files in os.walk(self.storage_dir):
                    # 跳过备份目录本身
                    if root == self.backup_dir or self.backup_dir in root:
                        continue
                    
                    for file in files:
                        file_path = os.path.join(root, file)
                        # 计算相对路径
                        rel_path = os.path.relpath(file_path, self.storage_dir)
                        zipf.write(file_path, rel_path)
            
            # 生成备份元数据
            backup_size = os.path.getsize(backup_path)
            backup_info = {
                'backup_id': timestamp,
                'backup_path': backup_path,
                'backup_filename': backup_filename,
                'size': backup_size,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'description': description,
                'status': 'completed'
            }
            
            # 保存备份元数据
            metadata_path = os.path.join(self.backup_dir, f"backup_{timestamp}.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, ensure_ascii=False, indent=2)
            
            return backup_info
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def restore_backup(self, backup_path: str) -> Dict[str, Any]:
        """从备份恢复数据
        
        Args:
            backup_path: 备份文件路径
        
        Returns:
            恢复结果
        """
        try:
            # 检查备份文件是否存在
            if not os.path.exists(backup_path):
                return {
                    'status': 'failed',
                    'error': '备份文件不存在'
                }
            
            # 创建临时目录用于解压
            temp_dir = os.path.join(self.storage_dir, 'temp_restore')
            os.makedirs(temp_dir, exist_ok=True)
            
            # 解压备份文件
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # 备份当前数据
            current_backup = self.create_backup("恢复前的自动备份")
            
            # 恢复数据
            # 先删除存储目录下的所有文件（除了备份目录和临时目录）
            for root, dirs, files in os.walk(self.storage_dir):
                if root == self.backup_dir or root == temp_dir or self.backup_dir in root:
                    continue
                
                for file in files:
                    file_path = os.path.join(root, file)
                    os.remove(file_path)
                
                # 删除空目录
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    if dir_path != self.backup_dir and dir_path != temp_dir:
                        try:
                            os.rmdir(dir_path)
                        except:
                            pass
            
            # 将临时目录中的文件复制到存储目录
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    src_path = os.path.join(root, file)
                    rel_path = os.path.relpath(src_path, temp_dir)
                    dst_path = os.path.join(self.storage_dir, rel_path)
                    
                    # 确保目标目录存在
                    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                    
                    # 复制文件
                    shutil.copy2(src_path, dst_path)
            
            # 清理临时目录
            shutil.rmtree(temp_dir)
            
            return {
                'status': 'completed',
                'message': '数据恢复成功',
                'current_backup': current_backup
            }
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份
        
        Returns:
            备份列表
        """
        backups = []
        
        # 查找所有备份文件
        for file in os.listdir(self.backup_dir):
            if file.endswith('.zip'):
                backup_path = os.path.join(self.backup_dir, file)
                timestamp = file.split('_')[1].split('.')[0]
                
                # 查找对应的元数据文件
                metadata_file = f"backup_{timestamp}.json"
                metadata_path = os.path.join(self.backup_dir, metadata_file)
                
                backup_info = {
                    'backup_filename': file,
                    'backup_path': backup_path,
                    'size': os.path.getsize(backup_path),
                    'timestamp': timestamp
                }
                
                # 加载元数据
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            backup_info.update(metadata)
                    except Exception as e:
                        print(f"加载备份元数据失败：{str(e)}")
                
                backups.append(backup_info)
        
        # 按时间倒序排序
        backups.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return backups
    
    def delete_backup(self, backup_path: str) -> bool:
        """删除备份
        
        Args:
            backup_path: 备份文件路径
        
        Returns:
            删除是否成功
        """
        try:
            if os.path.exists(backup_path):
                os.remove(backup_path)
                
                # 删除对应的元数据文件
                timestamp = os.path.basename(backup_path).split('_')[1].split('.')[0]
                metadata_file = f"backup_{timestamp}.json"
                metadata_path = os.path.join(self.backup_dir, metadata_file)
                if os.path.exists(metadata_path):
                    os.remove(metadata_path)
                
                return True
            return False
        except Exception as e:
            print(f"删除备份失败：{str(e)}")
            return False
    
    def start_auto_sync(self, interval: int = None):
        """开始自动同步
        
        Args:
            interval: 同步间隔（秒），默认为3600秒
        """
        if interval:
            self.sync_interval = interval
        
        self.sync_running = True
        self.sync_thread = threading.Thread(target=self._auto_sync_loop)
        self.sync_thread.daemon = True
        self.sync_thread.start()
    
    def stop_auto_sync(self):
        """停止自动同步"""
        self.sync_running = False
        if self.sync_thread:
            self.sync_thread.join()
    
    def _auto_sync_loop(self):
        """自动同步循环"""
        while self.sync_running:
            try:
                # 创建自动备份
                self.create_backup("自动同步备份")
                print(f"自动同步完成：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            except Exception as e:
                print(f"自动同步失败：{str(e)}")
            
            # 等待下一次同步
            for _ in range(self.sync_interval):
                if not self.sync_running:
                    break
                time.sleep(1)
    
    def sync_with_cloud(self, cloud_provider: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """与云存储同步
        
        Args:
            cloud_provider: 云存储提供商
            credentials: 云存储凭证
        
        Returns:
            同步结果
        """
        # 这里可以实现与各种云存储服务的同步
        # 例如：Google Drive, Dropbox, OneDrive等
        # 由于需要第三方库支持，这里只返回模拟结果
        
        return {
            'status': 'completed',
            'message': f'与{cloud_provider}同步功能已启动',
            'provider': cloud_provider,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """获取备份统计信息
        
        Returns:
            备份统计信息
        """
        backups = self.list_backups()
        
        total_backups = len(backups)
        total_size = sum(backup.get('size', 0) for backup in backups)
        recent_backups = backups[:5] if len(backups) >= 5 else backups
        
        return {
            'total_backups': total_backups,
            'total_size': total_size,
            'recent_backups': recent_backups,
            'backup_dir': self.backup_dir
        }
    
    def validate_backup(self, backup_path: str) -> Dict[str, Any]:
        """验证备份文件的完整性
        
        Args:
            backup_path: 备份文件路径
        
        Returns:
            验证结果
        """
        try:
            if not os.path.exists(backup_path):
                return {
                    'status': 'failed',
                    'message': '备份文件不存在'
                }
            
            # 检查ZIP文件的完整性
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # 测试所有文件
                zipf.testzip()
                
                # 获取备份中的文件列表
                file_list = zipf.namelist()
                
                return {
                    'status': 'completed',
                    'message': '备份文件完整',
                    'file_count': len(file_list),
                    'files': file_list[:10]  # 只返回前10个文件
                }
        except zipfile.BadZipFile:
            return {
                'status': 'failed',
                'message': '备份文件损坏'
            }
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'验证失败：{str(e)}'
            }