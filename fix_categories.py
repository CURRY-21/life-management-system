#!/usr/bin/env python3
"""
修复花销记录的分类问题
"""
import os
import sqlite3
from datetime import datetime

# 数据库路径
db_path = os.path.join('storage', 'life_management.db')

# 分类关键词
category_keywords = {
    '餐饮': ['餐', '饭', '午餐', '晚餐', '早餐', '外卖', '餐厅', '食堂', '买吃的', '啤酒', '烧烤', '喝酒', '唱歌', '早餐饭团', '午餐井冈山豆皮', '晚饭'],
    '交通': ['交通', '打车', '公交', '地铁', '加油', '停车', '客车', '火车票', '返程火车票', '坐公交'],
    '购物': ['购物', '买', '超市', '商场', '淘宝', '京东', '饮用水', '买吃的'],
    '娱乐': ['娱乐', '电影', '游戏', 'KTV', '旅游'],
    '医疗': ['医疗', '医院', '药店', '药'],
    '教育': ['教育', '学费', '培训', '书本', '学习'],
    '房租': ['房租', '房费', '住宿'],
    '礼品': ['送礼', '礼物', '礼品', '妇女节'],
    '个人护理': ['剪发', '理发', '美容', '护肤', '个人护理'],
    '财务': ['借钱', '借', '还钱', '还款', '财务']
}

def get_category(description):
    """根据描述自动匹配类别"""
    for cat, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in description:
                return cat
    return '其他'

def fix_categories():
    """修复数据库中的分类"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取所有花销记录
        cursor.execute('SELECT expense_id, description, category FROM expenses')
        records = cursor.fetchall()
        
        print(f'找到 {len(records)} 条记录')
        
        updated_count = 0
        for expense_id, description, old_category in records:
            new_category = get_category(description)
            if new_category != old_category:
                # 更新分类
                cursor.execute('''
                UPDATE expenses SET category = ? WHERE expense_id = ?
                ''', (new_category, expense_id))
                updated_count += 1
                print(f'更新记录 {expense_id}: {old_category} -> {new_category}')
        
        conn.commit()
        conn.close()
        
        print(f'\n修复完成！更新了 {updated_count} 条记录')
    except Exception as e:
        print(f'修复失败：{str(e)}')

def show_category_stats():
    """显示分类统计"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 按类别统计
        cursor.execute('SELECT category, COUNT(*), SUM(amount) FROM expenses GROUP BY category')
        stats = cursor.fetchall()
        
        print('\n分类统计：')
        for category, count, total in stats:
            print(f'{category}: {count} 条记录，总计 ¥{total:.2f}')
        
        conn.close()
    except Exception as e:
        print(f'统计失败：{str(e)}')

if __name__ == '__main__':
    print('开始修复花销记录分类...')
    fix_categories()
    show_category_stats()
