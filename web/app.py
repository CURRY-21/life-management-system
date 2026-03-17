from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, session
import os
import tempfile
from datetime import datetime
from config.config import config
from file_processing.advanced_processor import AdvancedFileProcessor
from asset_management.asset_manager import AssetManager
from asset_management.expense_manager import ExpenseManager
from asset_management.backup_manager import BackupManager
from core.auth_manager import AuthManager

def create_app():
    """创建Flask应用实例"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['UPLOAD_FOLDER'] = config.UPLOAD_DIR
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
    
    # 确保静态文件目录存在
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    os.makedirs(static_dir, exist_ok=True)
    icons_dir = os.path.join(static_dir, 'icons')
    os.makedirs(icons_dir, exist_ok=True)
    
    # 初始化文件处理器和资产管理器
    advanced_processor = AdvancedFileProcessor(config.STORAGE_DIR)
    asset_manager = AssetManager(os.path.join(config.STORAGE_DIR, 'life_management.db'))
    expense_manager = ExpenseManager(os.path.join(config.STORAGE_DIR, 'life_management.db'))
    backup_manager = BackupManager(config.STORAGE_DIR)
    auth_manager = AuthManager(os.path.join(config.STORAGE_DIR, 'auth.db'))
    
    # 全局变量
    app.advanced_processor = advanced_processor
    app.asset_manager = asset_manager
    app.expense_manager = expense_manager
    app.backup_manager = backup_manager
    app.auth_manager = auth_manager
    
    # 启动自动同步
    backup_manager.start_auto_sync()
    
    # 路由定义
    # 认证装饰器
    def login_required(f):
        """登录要求装饰器"""
        from functools import wraps
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 检查会话中是否有token
            token = session.get('token')
            if not token:
                flash('请先登录')
                return redirect(url_for('login'))
            
            # 验证token
            result = auth_manager.validate_token(token)
            if not result['valid']:
                flash('登录已过期，请重新登录')
                session.pop('token', None)
                session.pop('user', None)
                return redirect(url_for('login'))
            
            # 将用户信息存储到会话中
            session['user'] = result['user']
            return f(*args, **kwargs)
        return decorated_function
    
    def admin_required(f):
        """管理员权限要求装饰器"""
        from functools import wraps
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 检查是否登录
            token = session.get('token')
            if not token:
                flash('请先登录')
                return redirect(url_for('login'))
            
            # 验证token
            result = auth_manager.validate_token(token)
            if not result['valid']:
                flash('登录已过期，请重新登录')
                session.pop('token', None)
                session.pop('user', None)
                return redirect(url_for('login'))
            
            # 检查是否为管理员
            user = result['user']
            if user['role'] != 'admin':
                flash('您没有权限执行此操作')
                return redirect(url_for('index'))
            
            # 将用户信息存储到会话中
            session['user'] = user
            return f(*args, **kwargs)
        return decorated_function
    
    @app.route('/')
    def index():
        """首页"""
        # 获取文件统计信息
        statistics = asset_manager.get_file_statistics()
        recent_files = statistics.get('recent_files', [])
        category_stats = statistics.get('category_stats', {})
        total_files = statistics.get('total_files', 0)
        total_size = statistics.get('total_size', 0)
        
        # 转换文件大小为可读格式
        def format_size(size_bytes):
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.2f} KB"
            elif size_bytes < 1024 * 1024 * 1024:
                return f"{size_bytes / (1024 * 1024):.2f} MB"
            else:
                return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
        
        total_size_formatted = format_size(total_size)
        
        return render_template('index.html', 
                               total_files=total_files,
                               total_size=total_size_formatted,
                               category_stats=category_stats,
                               recent_files=recent_files,
                               user=session.get('user'))
    
    @app.route('/upload', methods=['GET', 'POST'])
    def upload_file():
        """文件上传页面"""
        if request.method == 'POST':
            # 检查是否有文件被上传
            if 'file' not in request.files:
                flash('没有选择文件')
                return redirect(request.url)
            
            file = request.files['file']
            
            # 检查文件名是否为空
            if file.filename == '':
                flash('没有选择文件')
                return redirect(request.url)
            
            # 保存临时文件
            if file:
                try:
                    # 创建临时文件
                    temp_dir = tempfile.gettempdir()
                    temp_path = os.path.join(temp_dir, file.filename)
                    file.save(temp_path)
                    
                    # 处理并存储文件
                    result = advanced_processor.process_and_store_file(temp_path, file.filename)
                    
                    if result['success']:
                        # 添加文件到数据库
                        file_info = result['file_info']
                        asset_manager.add_file(file_info)
                        
                        # 清理临时文件
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        
                        flash(f'文件上传成功：{file.filename}')
                        return redirect(url_for('files'))
                    else:
                        # 清理临时文件
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        
                        flash(f'文件上传失败：{result["message"]}')
                        return redirect(request.url)
                except Exception as e:
                    flash(f'文件处理错误：{str(e)}')
                    return redirect(request.url)
        
        return render_template('upload.html')
    
    @app.route('/files')
    def files():
        """文件列表页面"""
        # 获取查询参数
        category = request.args.get('category', None)
        page = int(request.args.get('page', 1))
        limit = 20
        offset = (page - 1) * limit
        
        # 获取文件列表
        file_list = asset_manager.list_files(category=category, limit=limit, offset=offset)
        
        # 获取分类统计
        statistics = asset_manager.get_file_statistics()
        category_stats = statistics.get('category_stats', {})
        
        return render_template('files.html', 
                               files=file_list,
                               category_stats=category_stats,
                               current_category=category,
                               current_page=page,
                               limit=limit)
    
    @app.route('/file/<file_id>')
    def view_file(file_id):
        """查看文件详情"""
        # 获取文件信息
        file_info = asset_manager.get_file(file_id)
        if not file_info:
            flash('文件不存在')
            return redirect(url_for('files'))
        
        # 转换文件大小为可读格式
        def format_size(size_bytes):
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.2f} KB"
            elif size_bytes < 1024 * 1024 * 1024:
                return f"{size_bytes / (1024 * 1024):.2f} MB"
            else:
                return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
        
        file_info['file_size_formatted'] = format_size(file_info['file_size'])
        
        return render_template('file_detail.html', file=file_info)
    
    @app.route('/file/<file_id>/download')
    def download_file(file_id):
        """下载文件"""
        # 获取文件信息
        file_info = asset_manager.get_file(file_id)
        if not file_info:
            flash('文件不存在')
            return redirect(url_for('files'))
        
        # 确保文件存在
        storage_path = file_info['storage_path']
        if not os.path.exists(storage_path):
            flash('文件不存在')
            return redirect(url_for('files'))
        
        # 发送文件
        directory = os.path.dirname(storage_path)
        filename = file_info['original_filename']
        return send_from_directory(directory, os.path.basename(storage_path), as_attachment=True, download_name=filename)
    
    @app.route('/file/<file_id>/delete', methods=['POST'])
    def delete_file(file_id):
        """删除文件"""
        try:
            # 获取文件信息
            file_info = asset_manager.get_file(file_id)
            if not file_info:
                flash('文件不存在')
                return redirect(url_for('files'))
            
            # 删除物理文件
            storage_path = file_info['storage_path']
            if os.path.exists(storage_path):
                os.remove(storage_path)
            
            # 从数据库删除
            asset_manager.delete_file(file_id)
            
            flash('文件删除成功')
            return redirect(url_for('files'))
        except Exception as e:
            flash(f'文件删除失败：{str(e)}')
            return redirect(url_for('files'))
    
    @app.route('/search', methods=['GET'])
    def search():
        """搜索页面"""
        keyword = request.args.get('keyword', '')
        category = request.args.get('category', None)
        
        if keyword:
            # 搜索文件
            results = asset_manager.search_files(keyword=keyword, category=category)
        else:
            results = []
        
        return render_template('search.html', 
                               keyword=keyword,
                               category=category,
                               results=results)
    
    @app.route('/tags')
    def tags():
        """标签管理页面"""
        # 获取所有标签
        all_tags = asset_manager.get_tags()
        
        return render_template('tags.html', tags=all_tags)
    
    @app.route('/file/<file_id>/add_tag', methods=['POST'])
    def add_file_tag(file_id):
        """为文件添加标签"""
        tag_name = request.form.get('tag_name', '').strip()
        
        if not tag_name:
            flash('标签名称不能为空')
            return redirect(url_for('view_file', file_id=file_id))
        
        try:
            success = asset_manager.add_file_tag(file_id, tag_name)
            if success:
                flash(f'标签 "{tag_name}" 添加成功')
            else:
                flash('标签添加失败')
        except Exception as e:
            flash(f'标签添加错误：{str(e)}')
        
        return redirect(url_for('view_file', file_id=file_id))
    
    @app.route('/file/<file_id>/remove_tag/<tag_name>', methods=['POST'])
    def remove_file_tag(file_id, tag_name):
        """移除文件标签"""
        try:
            success = asset_manager.remove_file_tag(file_id, tag_name)
            if success:
                flash(f'标签 "{tag_name}" 移除成功')
            else:
                flash('标签移除失败')
        except Exception as e:
            flash(f'标签移除错误：{str(e)}')
        
        return redirect(url_for('view_file', file_id=file_id))
    
    @app.route('/api/files', methods=['GET'])
    def api_files():
        """文件API接口"""
        category = request.args.get('category', None)
        files = asset_manager.list_files(category=category)
        return jsonify({'success': True, 'files': files})
    
    @app.route('/api/file/<file_id>', methods=['GET'])
    def api_file(file_id):
        """文件详情API接口"""
        file_info = asset_manager.get_file(file_id)
        if file_info:
            return jsonify({'success': True, 'file': file_info})
        else:
            return jsonify({'success': False, 'message': '文件不存在'})
    
    @app.route('/api/search', methods=['GET'])
    def api_search():
        """搜索API接口"""
        keyword = request.args.get('keyword', '')
        category = request.args.get('category', None)
        
        if keyword:
            results = asset_manager.search_files(keyword=keyword, category=category)
            return jsonify({'success': True, 'results': results})
        else:
            return jsonify({'success': False, 'message': '搜索关键词不能为空'})
    
    @app.route('/api/statistics', methods=['GET'])
    def api_statistics():
        """统计信息API接口"""
        statistics = asset_manager.get_file_statistics()
        return jsonify({'success': True, 'statistics': statistics})
    
    @app.route('/mobile')
    def mobile():
        """移动端适配页面"""
        return render_template('mobile.html')
    
    @app.route('/backups')
    def backups():
        """备份管理页面"""
        # 获取备份列表
        backup_list = backup_manager.list_backups()
        
        # 获取备份统计信息
        statistics = backup_manager.get_backup_statistics()
        
        return render_template('backups.html', 
                               backups=backup_list,
                               statistics=statistics)
    
    @app.route('/create_backup', methods=['POST'])
    def create_backup():
        """创建备份"""
        description = request.form.get('description', '')
        
        try:
            result = backup_manager.create_backup(description)
            if result['status'] == 'completed':
                flash('备份创建成功')
            else:
                flash(f'备份创建失败：{result.get("error", "未知错误")}')
        except Exception as e:
            flash(f'备份创建失败：{str(e)}')
        
        return redirect(url_for('backups'))
    
    @app.route('/restore_backup/<backup_filename>', methods=['POST'])
    def restore_backup(backup_filename):
        """恢复备份"""
        backup_path = os.path.join(backup_manager.backup_dir, backup_filename)
        
        try:
            # 验证备份文件是否存在
            if not os.path.exists(backup_path):
                flash('备份文件不存在')
                return redirect(url_for('backups'))
            
            # 恢复备份
            result = backup_manager.restore_backup(backup_path)
            if result['status'] == 'completed':
                flash('数据恢复成功')
            else:
                flash(f'数据恢复失败：{result.get("error", "未知错误")}')
        except Exception as e:
            flash(f'数据恢复失败：{str(e)}')
        
        return redirect(url_for('backups'))
    
    @app.route('/delete_backup/<backup_filename>', methods=['POST'])
    def delete_backup(backup_filename):
        """删除备份"""
        backup_path = os.path.join(backup_manager.backup_dir, backup_filename)
        
        try:
            success = backup_manager.delete_backup(backup_path)
            if success:
                flash('备份删除成功')
            else:
                flash('备份删除失败')
        except Exception as e:
            flash(f'备份删除失败：{str(e)}')
        
        return redirect(url_for('backups'))
    
    @app.route('/download_backup/<backup_filename>')
    def download_backup(backup_filename):
        """下载备份"""
        backup_path = os.path.join(backup_manager.backup_dir, backup_filename)
        
        try:
            # 验证备份文件是否存在
            if not os.path.exists(backup_path):
                flash('备份文件不存在')
                return redirect(url_for('backups'))
            
            # 发送文件
            return send_from_directory(backup_manager.backup_dir, backup_filename, as_attachment=True)
        except Exception as e:
            flash(f'备份下载失败：{str(e)}')
            return redirect(url_for('backups'))
    
    @app.route('/about')
    def about():
        """关于页面"""
        return render_template('about.html', user=session.get('user'))
    
    # 认证相关路由
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """用户注册页面"""
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            # 验证输入
            if not username:
                flash('用户名不能为空')
                return redirect(url_for('register'))
            
            if not email:
                flash('邮箱不能为空')
                return redirect(url_for('register'))
            
            if not password:
                flash('密码不能为空')
                return redirect(url_for('register'))
            
            if password != confirm_password:
                flash('两次输入的密码不一致')
                return redirect(url_for('register'))
            
            # 注册用户
            result = auth_manager.register(username, email, password)
            if result['success']:
                flash('注册成功，请登录')
                return redirect(url_for('login'))
            else:
                flash(result['message'])
                return redirect(url_for('register'))
        
        return render_template('register.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """用户登录页面"""
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            
            # 验证输入
            if not username:
                flash('用户名不能为空')
                return redirect(url_for('login'))
            
            if not password:
                flash('密码不能为空')
                return redirect(url_for('login'))
            
            # 登录用户
            result = auth_manager.login(username, password)
            if result['success']:
                # 存储token到会话
                session['token'] = result['token']
                session['user'] = result['user']
                flash('登录成功')
                return redirect(url_for('index'))
            else:
                flash(result['message'])
                return redirect(url_for('login'))
        
        return render_template('login.html')
    
    @app.route('/logout')
    def logout():
        """用户注销"""
        token = session.get('token')
        if token:
            auth_manager.logout(token)
        
        # 清除会话
        session.clear()
        flash('注销成功')
        return redirect(url_for('index'))
    
    @app.route('/users')
    @admin_required
    def users():
        """用户管理页面"""
        # 获取用户列表
        user_list = auth_manager.list_users()
        
        return render_template('users.html', users=user_list, user=session.get('user'))
    
    @app.route('/user/<user_id>/delete', methods=['POST'])
    @admin_required
    def delete_user(user_id):
        """删除用户"""
        try:
            result = auth_manager.delete_user(user_id)
            if result['success']:
                flash('用户删除成功')
            else:
                flash(result['message'])
        except Exception as e:
            flash(f'用户删除失败：{str(e)}')
        
        return redirect(url_for('users'))
    
    # 花销记录相关路由
    @app.route('/expenses')
    def expenses():
        """花销记录列表页面"""
        # 获取查询参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        category = request.args.get('category')
        
        # 获取花销记录
        expenses_list = expense_manager.list_expenses(start_date=start_date, end_date=end_date, category=category)
        
        # 获取所有类别
        categories = expense_manager.get_categories()
        
        # 计算总花销
        total_expense = expense_manager.get_total_expense(start_date=start_date, end_date=end_date, category=category)
        
        return render_template('expenses.html', 
                               expenses=expenses_list,
                               categories=categories,
                               current_category=category,
                               start_date=start_date,
                               end_date=end_date,
                               total_expense=total_expense)
    
    @app.route('/expenses/add', methods=['GET', 'POST'])
    def add_expense():
        """添加花销记录页面"""
        # 获取所有类别
        categories = expense_manager.get_categories()
        
        if request.method == 'POST':
            # 获取表单数据
            amount = request.form.get('amount')
            category = request.form.get('category')
            description = request.form.get('description', '')
            date = request.form.get('date', datetime.now().strftime('%Y-%m-%d'))
            time = request.form.get('time', datetime.now().strftime('%H:%M:%S'))
            input_method = request.form.get('input_method', 'manual')
            
            # 验证输入
            if not amount:
                flash('金额不能为空')
                return redirect(url_for('add_expense'))
            
            if not category:
                flash('类别不能为空')
                return redirect(url_for('add_expense'))
            
            try:
                amount = float(amount)
                if amount <= 0:
                    flash('金额必须大于0')
                    return redirect(url_for('add_expense'))
            except ValueError:
                flash('金额必须是数字')
                return redirect(url_for('add_expense'))
            
            # 准备花销信息
            expense_info = {
                'amount': amount,
                'category': category,
                'description': description,
                'date': date,
                'time': time,
                'input_method': input_method
            }
            
            # 添加花销记录
            success = expense_manager.add_expense(expense_info)
            if success:
                flash('花销记录添加成功')
                return redirect(url_for('expenses'))
            else:
                flash('花销记录添加失败')
                return redirect(url_for('add_expense'))
        
        return render_template('add_expense.html', categories=categories)
    
    @app.route('/expenses/<expense_id>/delete', methods=['POST'])
    def delete_expense(expense_id):
        """删除花销记录"""
        try:
            success = expense_manager.delete_expense(expense_id)
            if success:
                flash('花销记录删除成功')
            else:
                flash('花销记录删除失败')
        except Exception as e:
            flash(f'删除失败：{str(e)}')
        
        return redirect(url_for('expenses'))
    
    @app.route('/expenses/categories')
    def expense_categories():
        """类别管理页面"""
        categories = expense_manager.get_categories()
        return render_template('expense_categories.html', categories=categories)
    
    @app.route('/expenses/categories/add', methods=['POST'])
    def add_expense_category():
        """添加类别"""
        category_name = request.form.get('category_name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not category_name:
            flash('类别名称不能为空')
            return redirect(url_for('expense_categories'))
        
        success = expense_manager.add_category(category_name, description)
        if success:
            flash('类别添加成功')
        else:
            flash('类别添加失败')
        
        return redirect(url_for('expense_categories'))
    
    @app.route('/expenses/categories/<category_id>/delete', methods=['POST'])
    def delete_expense_category(category_id):
        """删除类别"""
        success = expense_manager.delete_category(category_id)
        if success:
            flash('类别删除成功')
        else:
            flash('类别删除失败，该类别下可能存在花销记录')
        
        return redirect(url_for('expense_categories'))
    
    @app.route('/expenses/statistics')
    def expense_statistics():
        """花销统计页面"""
        # 获取查询参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 计算总花销
        total_expense = expense_manager.get_total_expense(start_date=start_date, end_date=end_date)
        # 确保total_expense是数字类型
        try:
            total_expense = float(total_expense)
        except (ValueError, TypeError):
            total_expense = 0.0
        
        # 按类别统计
        category_expenses = expense_manager.get_category_expenses(start_date=start_date, end_date=end_date)
        # 确保category_expenses中的值都是数字类型
        for category, amount in category_expenses.items():
            try:
                category_expenses[category] = float(amount)
            except (ValueError, TypeError):
                category_expenses[category] = 0.0
        
        # 按日期统计
        daily_expenses = expense_manager.get_daily_expenses(start_date=start_date, end_date=end_date)
        # 确保daily_expenses中的值都是数字类型
        for date, amount in daily_expenses.items():
            try:
                daily_expenses[date] = float(amount)
            except (ValueError, TypeError):
                daily_expenses[date] = 0.0
        
        return render_template('expense_statistics.html', 
                               total_expense=total_expense,
                               category_expenses=category_expenses,
                               daily_expenses=daily_expenses,
                               start_date=start_date,
                               end_date=end_date)
    
    # API接口
    @app.route('/api/expenses', methods=['GET'])
    def api_expenses():
        """花销记录API接口"""
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        category = request.args.get('category')
        
        expenses_list = expense_manager.list_expenses(start_date=start_date, end_date=end_date, category=category)
        return jsonify({'success': True, 'expenses': expenses_list})
    
    @app.route('/api/expenses/statistics', methods=['GET'])
    def api_expense_statistics():
        """花销统计API接口"""
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        total_expense = expense_manager.get_total_expense(start_date=start_date, end_date=end_date)
        category_expenses = expense_manager.get_category_expenses(start_date=start_date, end_date=end_date)
        daily_expenses = expense_manager.get_daily_expenses(start_date=start_date, end_date=end_date)
        
        return jsonify({
            'success': True,
            'total_expense': total_expense,
            'category_expenses': category_expenses,
            'daily_expenses': daily_expenses
        })
    
    @app.route('/api/expenses/batch', methods=['POST'])
    def api_batch_expenses():
        """批量保存花销记录API接口"""
        try:
            data = request.get_json()
            if not data or not isinstance(data, list):
                return jsonify({'success': False, 'message': '无效的请求数据'})
            
            saved_count = 0
            for expense_info in data:
                # 验证数据
                if 'amount' not in expense_info or 'description' not in expense_info:
                    continue
                
                # 自动匹配类别
                category = '其他'  # 默认类别
                # 根据描述自动匹配类别
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
                
                for cat, keywords in category_keywords.items():
                    for keyword in keywords:
                        if keyword in expense_info['description']:
                            category = cat
                            break
                    if category != '其他':
                        break
                
                # 准备花销信息
                expense_data = {
                    'amount': float(expense_info['amount']),
                    'category': category,
                    'description': expense_info['description'],
                    'date': expense_info.get('date', datetime.now().strftime('%Y-%m-%d')),
                    'time': expense_info.get('time', datetime.now().strftime('%H:%M:%S')),
                    'input_method': 'text'
                }
                
                # 添加花销记录
                if expense_manager.add_expense(expense_data):
                    saved_count += 1
            
            return jsonify({'success': True, 'saved_count': saved_count, 'total_count': len(data)})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)