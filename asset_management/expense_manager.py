import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

class ExpenseManager:
    """花销管理器，负责记录和管理用户的花销"""
    
    def __init__(self, db_path: str):
        """初始化花销管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建花销记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            expense_id TEXT PRIMARY KEY,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            input_method TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        ''')
        
        # 创建类别表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS expense_categories (
            category_id TEXT PRIMARY KEY,
            category_name TEXT UNIQUE NOT NULL,
            description TEXT
        )
        ''')
        
        # 创建默认类别
        default_categories = [
            ('1', '餐饮', '日常饮食开销'),
            ('2', '交通', '公共交通、打车等'),
            ('3', '购物', '日常购物'),
            ('4', '娱乐', '休闲娱乐活动'),
            ('5', '医疗', '医疗费用'),
            ('6', '教育', '教育相关支出'),
            ('7', '房租', '住房租金'),
            ('8', '其他', '其他开销')
        ]
        
        for category in default_categories:
            try:
                cursor.execute('''
                INSERT OR IGNORE INTO expense_categories (category_id, category_name, description)
                VALUES (?, ?, ?)
                ''', category)
            except Exception as e:
                print(f"创建默认类别失败：{str(e)}")
        
        conn.commit()
        conn.close()
    
    def add_expense(self, expense_info: Dict[str, Any]) -> bool:
        """添加花销记录
        
        Args:
            expense_info: 花销信息字典
        
        Returns:
            添加是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 准备数据
            import uuid
            expense_id = str(uuid.uuid4())
            amount = expense_info.get('amount')
            category = expense_info.get('category')
            description = expense_info.get('description', '')
            date = expense_info.get('date', datetime.now().strftime('%Y-%m-%d'))
            time = expense_info.get('time', datetime.now().strftime('%H:%M:%S'))
            input_method = expense_info.get('input_method', 'manual')
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 插入花销记录
            cursor.execute('''
            INSERT INTO expenses (expense_id, amount, category, description, date, time, input_method, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (expense_id, amount, category, description, date, time, input_method, created_at))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"添加花销记录失败：{str(e)}")
            return False
    
    def get_expense(self, expense_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取花销记录
        
        Args:
            expense_id: 花销记录ID
        
        Returns:
            花销记录字典，如果不存在则返回None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT * FROM expenses WHERE expense_id = ?
            ''', (expense_id,))
            
            row = cursor.fetchone()
            if not row:
                conn.close()
                return None
            
            # 转换为字典
            expense_info = dict(row)
            conn.close()
            return expense_info
        except Exception as e:
            print(f"获取花销记录失败：{str(e)}")
            return None
    
    def list_expenses(self, start_date: Optional[str] = None, end_date: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出花销记录
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            category: 类别筛选
        
        Returns:
            花销记录列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM expenses WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            query += " ORDER BY date DESC, time DESC"
            
            cursor.execute(query, params)
            
            rows = cursor.fetchall()
            expenses = []
            
            for row in rows:
                expense_info = dict(row)
                expenses.append(expense_info)
            
            conn.close()
            return expenses
        except Exception as e:
            print(f"列出花销记录失败：{str(e)}")
            return []
    
    def get_total_expense(self, start_date: Optional[str] = None, end_date: Optional[str] = None, category: Optional[str] = None) -> float:
        """计算总花销
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            category: 类别筛选
        
        Returns:
            总花销金额
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT SUM(amount) FROM expenses WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            cursor.execute(query, params)
            
            total = cursor.fetchone()[0]
            conn.close()
            return total or 0.0
        except Exception as e:
            print(f"计算总花销失败：{str(e)}")
            return 0.0
    
    def get_category_expenses(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, float]:
        """按类别统计花销
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            类别-金额字典
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT category, SUM(amount) FROM expenses WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)
            
            query += " GROUP BY category"
            
            cursor.execute(query, params)
            
            category_expenses = {}
            for row in cursor.fetchall():
                category_expenses[row[0]] = row[1] or 0.0
            
            conn.close()
            return category_expenses
        except Exception as e:
            print(f"按类别统计花销失败：{str(e)}")
            return {}
    
    def get_daily_expenses(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, float]:
        """按日期统计花销
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            日期-金额字典
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT date, SUM(amount) FROM expenses WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)
            
            query += " GROUP BY date ORDER BY date"
            
            cursor.execute(query, params)
            
            daily_expenses = {}
            for row in cursor.fetchall():
                daily_expenses[row[0]] = row[1] or 0.0
            
            conn.close()
            return daily_expenses
        except Exception as e:
            print(f"按日期统计花销失败：{str(e)}")
            return {}
    
    def delete_expense(self, expense_id: str) -> bool:
        """删除花销记录
        
        Args:
            expense_id: 花销记录ID
        
        Returns:
            删除是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            DELETE FROM expenses WHERE expense_id = ?
            ''', (expense_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"删除花销记录失败：{str(e)}")
            return False
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """获取所有类别
        
        Returns:
            类别列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT * FROM expense_categories
            ORDER BY category_name
            ''')
            
            categories = []
            for row in cursor.fetchall():
                category_info = dict(row)
                categories.append(category_info)
            
            conn.close()
            return categories
        except Exception as e:
            print(f"获取类别失败：{str(e)}")
            return []
    
    def add_category(self, category_name: str, description: str = '') -> bool:
        """添加自定义类别
        
        Args:
            category_name: 类别名称
            description: 类别描述
        
        Returns:
            添加是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 生成类别ID
            import uuid
            category_id = str(uuid.uuid4())
            
            # 插入类别
            cursor.execute('''
            INSERT OR IGNORE INTO expense_categories (category_id, category_name, description)
            VALUES (?, ?, ?)
            ''', (category_id, category_name, description))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"添加类别失败：{str(e)}")
            return False
    
    def delete_category(self, category_id: str) -> bool:
        """删除类别
        
        Args:
            category_id: 类别ID
        
        Returns:
            删除是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查是否有关联的花销记录
            cursor.execute('''
            SELECT COUNT(*) FROM expenses WHERE category = (
                SELECT category_name FROM expense_categories WHERE category_id = ?
            )
            ''', (category_id,))
            
            count = cursor.fetchone()[0]
            if count > 0:
                conn.close()
                return False
            
            # 删除类别
            cursor.execute('''
            DELETE FROM expense_categories WHERE category_id = ?
            ''', (category_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"删除类别失败：{str(e)}")
            return False
