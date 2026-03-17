import os
import sqlite3
import json
from datetime import datetime, timedelta
import hashlib
import secrets
from typing import Dict, Any, Optional, List

class AuthManager:
    """用户认证管理器，负责用户注册、登录、注销和权限管理"""
    
    def __init__(self, db_path: str):
        """初始化认证管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.init_database()
        self.token_expiry = 24 * 60 * 60  # 令牌过期时间（秒）
    
    def init_database(self):
        """初始化用户数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_login TEXT,
            role TEXT DEFAULT 'user'
        )
        ''')
        
        # 创建用户会话表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            token TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        
        # 创建默认管理员用户（如果不存在）
        admin_username = "admin"
        admin_email = "admin@example.com"
        admin_password = "admin123"
        
        # 检查管理员用户是否存在
        cursor.execute('''
        SELECT user_id FROM users WHERE username = ?
        ''', (admin_username,))
        
        if not cursor.fetchone():
            # 生成盐和密码哈希
            salt = secrets.token_hex(16)
            password_hash = self._hash_password(admin_password, salt)
            
            # 插入管理员用户
            cursor.execute('''
            INSERT INTO users (user_id, username, email, password_hash, salt, created_at, role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                secrets.token_hex(16),
                admin_username,
                admin_email,
                password_hash,
                salt,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'admin'
            ))
            
            print(f"默认管理员用户创建成功：{admin_username}/{admin_password}")
        
        conn.commit()
        conn.close()
    
    def _hash_password(self, password: str, salt: str) -> str:
        """哈希密码
        
        Args:
            password: 原始密码
            salt: 盐值
        
        Returns:
            哈希后的密码
        """
        return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    
    def register(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """用户注册
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
        
        Returns:
            注册结果
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查用户名是否已存在
            cursor.execute('''
            SELECT user_id FROM users WHERE username = ?
            ''', (username,))
            
            if cursor.fetchone():
                conn.close()
                return {
                    'success': False,
                    'message': '用户名已存在'
                }
            
            # 检查邮箱是否已存在
            cursor.execute('''
            SELECT user_id FROM users WHERE email = ?
            ''', (email,))
            
            if cursor.fetchone():
                conn.close()
                return {
                    'success': False,
                    'message': '邮箱已存在'
                }
            
            # 生成用户ID、盐和密码哈希
            user_id = secrets.token_hex(16)
            salt = secrets.token_hex(16)
            password_hash = self._hash_password(password, salt)
            
            # 插入用户记录
            cursor.execute('''
            INSERT INTO users (user_id, username, email, password_hash, salt, created_at, role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                username,
                email,
                password_hash,
                salt,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'user'
            ))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': '注册成功',
                'user_id': user_id
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'注册失败：{str(e)}'
            }
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """用户登录
        
        Args:
            username: 用户名
            password: 密码
        
        Returns:
            登录结果，包含令牌
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 查找用户
            cursor.execute('''
            SELECT user_id, username, email, password_hash, salt, role FROM users WHERE username = ?
            ''', (username,))
            
            user = cursor.fetchone()
            if not user:
                conn.close()
                return {
                    'success': False,
                    'message': '用户名或密码错误'
                }
            
            user_id, username, email, password_hash, salt, role = user
            
            # 验证密码
            if self._hash_password(password, salt) != password_hash:
                conn.close()
                return {
                    'success': False,
                    'message': '用户名或密码错误'
                }
            
            # 更新最后登录时间
            cursor.execute('''
            UPDATE users SET last_login = ? WHERE user_id = ?
            ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id))
            
            # 生成会话令牌
            session_id = secrets.token_hex(16)
            token = secrets.token_hex(32)
            created_at = datetime.now()
            expires_at = created_at + timedelta(seconds=self.token_expiry)
            
            # 插入会话记录
            cursor.execute('''
            INSERT INTO sessions (session_id, user_id, token, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                session_id,
                user_id,
                token,
                created_at.strftime('%Y-%m-%d %H:%M:%S'),
                expires_at.strftime('%Y-%m-%d %H:%M:%S')
            ))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': '登录成功',
                'token': token,
                'user': {
                    'user_id': user_id,
                    'username': username,
                    'email': email,
                    'role': role
                }
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'登录失败：{str(e)}'
            }
    
    def logout(self, token: str) -> Dict[str, Any]:
        """用户注销
        
        Args:
            token: 会话令牌
        
        Returns:
            注销结果
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 删除会话
            cursor.execute('''
            DELETE FROM sessions WHERE token = ?
            ''', (token,))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': '注销成功'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'注销失败：{str(e)}'
            }
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """验证令牌
        
        Args:
            token: 会话令牌
        
        Returns:
            验证结果，包含用户信息
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 查找会话
            cursor.execute('''
            SELECT s.session_id, s.user_id, s.expires_at, u.username, u.email, u.role
            FROM sessions s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.token = ?
            ''', (token,))
            
            session = cursor.fetchone()
            if not session:
                conn.close()
                return {
                    'valid': False,
                    'message': '无效的令牌'
                }
            
            session_id, user_id, expires_at, username, email, role = session
            
            # 检查令牌是否过期
            if datetime.now() > datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S'):
                # 删除过期会话
                cursor.execute('''
                DELETE FROM sessions WHERE session_id = ?
                ''', (session_id,))
                conn.commit()
                conn.close()
                return {
                    'valid': False,
                    'message': '令牌已过期'
                }
            
            conn.close()
            
            return {
                'valid': True,
                'user': {
                    'user_id': user_id,
                    'username': username,
                    'email': email,
                    'role': role
                }
            }
        except Exception as e:
            return {
                'valid': False,
                'message': f'验证失败：{str(e)}'
            }
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """根据用户ID获取用户信息
        
        Args:
            user_id: 用户ID
        
        Returns:
            用户信息字典，如果不存在则返回None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 查找用户
            cursor.execute('''
            SELECT user_id, username, email, created_at, last_login, role FROM users WHERE user_id = ?
            ''', (user_id,))
            
            user = cursor.fetchone()
            if not user:
                conn.close()
                return None
            
            user_id, username, email, created_at, last_login, role = user
            
            conn.close()
            
            return {
                'user_id': user_id,
                'username': username,
                'email': email,
                'created_at': created_at,
                'last_login': last_login,
                'role': role
            }
        except Exception as e:
            print(f"获取用户信息失败：{str(e)}")
            return None
    
    def update_password(self, user_id: str, old_password: str, new_password: str) -> Dict[str, Any]:
        """更新用户密码
        
        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码
        
        Returns:
            更新结果
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 查找用户
            cursor.execute('''
            SELECT password_hash, salt FROM users WHERE user_id = ?
            ''', (user_id,))
            
            user = cursor.fetchone()
            if not user:
                conn.close()
                return {
                    'success': False,
                    'message': '用户不存在'
                }
            
            password_hash, salt = user
            
            # 验证旧密码
            if self._hash_password(old_password, salt) != password_hash:
                conn.close()
                return {
                    'success': False,
                    'message': '旧密码错误'
                }
            
            # 生成新的盐和密码哈希
            new_salt = secrets.token_hex(16)
            new_password_hash = self._hash_password(new_password, new_salt)
            
            # 更新密码
            cursor.execute('''
            UPDATE users SET password_hash = ?, salt = ? WHERE user_id = ?
            ''', (new_password_hash, new_salt, user_id))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': '密码更新成功'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'密码更新失败：{str(e)}'
            }
    
    def list_users(self) -> List[Dict[str, Any]]:
        """列出所有用户
        
        Returns:
            用户列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 查找所有用户
            cursor.execute('''
            SELECT user_id, username, email, created_at, last_login, role FROM users
            ORDER BY created_at DESC
            ''')
            
            users = []
            for user in cursor.fetchall():
                user_id, username, email, created_at, last_login, role = user
                users.append({
                    'user_id': user_id,
                    'username': username,
                    'email': email,
                    'created_at': created_at,
                    'last_login': last_login,
                    'role': role
                })
            
            conn.close()
            return users
        except Exception as e:
            print(f"列出用户失败：{str(e)}")
            return []
    
    def delete_user(self, user_id: str) -> Dict[str, Any]:
        """删除用户
        
        Args:
            user_id: 用户ID
        
        Returns:
            删除结果
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查用户是否存在
            cursor.execute('''
            SELECT user_id FROM users WHERE user_id = ?
            ''', (user_id,))
            
            if not cursor.fetchone():
                conn.close()
                return {
                    'success': False,
                    'message': '用户不存在'
                }
            
            # 删除用户的所有会话
            cursor.execute('''
            DELETE FROM sessions WHERE user_id = ?
            ''', (user_id,))
            
            # 删除用户
            cursor.execute('''
            DELETE FROM users WHERE user_id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': '用户删除成功'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'用户删除失败：{str(e)}'
            }
    
    def cleanup_expired_sessions(self):
        """清理过期的会话"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 删除过期的会话
            cursor.execute('''
            DELETE FROM sessions WHERE expires_at < ?
            ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))
            
            conn.commit()
            conn.close()
            print(f"清理过期会话完成：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            print(f"清理过期会话失败：{str(e)}")