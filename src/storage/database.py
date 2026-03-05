"""
数据库管理模块
负责数据库的初始化、连接和基础CRUD操作
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: str = "./data/screenTrace.db"):
        self.db_path = Path(db_path)
        self.connection: Optional[sqlite3.Connection] = None

    def initialize(self) -> None:
        """初始化数据库"""
        # 确保数据目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 连接数据库
        self.connection = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False
        )
        self.connection.row_factory = sqlite3.Row

        # 创建表
        self._create_tables()

        logger.info(f"数据库初始化成功: {self.db_path}")

    def _create_tables(self) -> None:
        """创建数据库表"""
        cursor = self.connection.cursor()

        # 截图记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS screenshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                app_name TEXT,
                window_title TEXT,
                life_category TEXT,
                activity_form TEXT,
                description TEXT,
                keywords TEXT,
                screenshot_path TEXT NOT NULL,
                similarity_score REAL,
                api_called BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON screenshots(timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_life_category
            ON screenshots(life_category)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_app_name
            ON screenshots(app_name)
        """)

        # API调用日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                provider TEXT,
                model TEXT,
                tokens_used INTEGER,
                cost REAL,
                success BOOLEAN,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 系统日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                event_type TEXT,
                event_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.connection.commit()
        logger.info("数据库表创建成功")

    def insert_screenshot(
        self,
        timestamp: datetime,
        screenshot_path: str,
        app_name: Optional[str] = None,
        window_title: Optional[str] = None,
        life_category: Optional[str] = None,
        activity_form: Optional[str] = None,
        description: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        similarity_score: Optional[float] = None,
        api_called: bool = False
    ) -> int:
        """插入截图记录"""
        cursor = self.connection.cursor()

        keywords_json = json.dumps(keywords, ensure_ascii=False) if keywords else None

        cursor.execute("""
            INSERT INTO screenshots
            (timestamp, app_name, window_title, life_category, activity_form,
             description, keywords, screenshot_path, similarity_score, api_called)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp.isoformat(),
            app_name,
            window_title,
            life_category,
            activity_form,
            description,
            keywords_json,
            screenshot_path,
            similarity_score,
            api_called
        ))

        self.connection.commit()
        record_id = cursor.lastrowid

        logger.debug(f"插入截图记录: ID={record_id}, 时间={timestamp}")
        return record_id

    def get_screenshots(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        life_category: Optional[str] = None,
        app_name: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """查询截图记录"""
        query = "SELECT * FROM screenshots WHERE 1=1"
        params = []

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())

        if life_category:
            query += " AND life_category = ?"
            params.append(life_category)

        if app_name:
            query += " AND app_name = ?"
            params.append(app_name)

        query += " ORDER BY timestamp DESC"

        if limit:
            query += f" LIMIT {limit}"

        cursor = self.connection.cursor()
        cursor.execute(query, params)

        rows = cursor.fetchall()
        results = []

        for row in rows:
            record = dict(row)
            # 解析JSON字段
            if record['keywords']:
                try:
                    record['keywords'] = json.loads(record['keywords'])
                except (json.JSONDecodeError, TypeError):
                    # 如果JSON解析失败，尝试用ast.literal_eval解析Python列表字符串
                    try:
                        import ast
                        record['keywords'] = ast.literal_eval(record['keywords'])
                    except (ValueError, SyntaxError):
                        # 如果还是失败，设置为空列表
                        record['keywords'] = []
            results.append(record)

        return results

    def get_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取统计数据"""
        cursor = self.connection.cursor()

        # 时间范围条件
        time_condition = ""
        params = []

        if start_time:
            time_condition += " AND timestamp >= ?"
            params.append(start_time.isoformat())

        if end_time:
            time_condition += " AND timestamp <= ?"
            params.append(end_time.isoformat())

        # 按生活维度统计
        cursor.execute(f"""
            SELECT life_category, COUNT(*) as count
            FROM screenshots
            WHERE 1=1 {time_condition}
            GROUP BY life_category
            ORDER BY count DESC
        """, params)

        life_category_stats = {row['life_category'] if row['life_category'] else 'N/A': row['count'] for row in cursor.fetchall()}

        # 按活动形式统计
        cursor.execute(f"""
            SELECT activity_form, COUNT(*) as count
            FROM screenshots
            WHERE 1=1 {time_condition}
            GROUP BY activity_form
            ORDER BY count DESC
        """, params)

        activity_form_stats = {row['activity_form'] if row['activity_form'] else 'N/A': row['count'] for row in cursor.fetchall()}

        # 按应用统计TOP 10
        cursor.execute(f"""
            SELECT app_name, COUNT(*) as count
            FROM screenshots
            WHERE 1=1 {time_condition}
            GROUP BY app_name
            ORDER BY count DESC
            LIMIT 10
        """, params)

        app_stats = {row['app_name'] if row['app_name'] else 'Unknown': row['count'] for row in cursor.fetchall()}

        # 总记录数
        cursor.execute(f"""
            SELECT COUNT(*) as total
            FROM screenshots
            WHERE 1=1 {time_condition}
        """, params)

        total_records = cursor.fetchone()['total']

        return {
            'total_records': total_records,
            'life_category': life_category_stats,
            'activity_form': activity_form_stats,
            'top_apps': app_stats
        }

    def delete_old_records(self, days: int) -> int:
        """删除旧记录"""
        cursor = self.connection.cursor()

        # 获取要删除的记录
        cursor.execute("""
            SELECT id, screenshot_path
            FROM screenshots
            WHERE datetime(timestamp) < datetime('now', ?)
        """, (f'-{days} days',))

        records_to_delete = cursor.fetchall()

        # 删除截图文件
        from pathlib import Path
        for record in records_to_delete:
            screenshot_path = Path(record['screenshot_path'])
            if screenshot_path.exists():
                try:
                    screenshot_path.unlink()
                    logger.debug(f"删除截图文件: {screenshot_path}")
                except Exception as e:
                    logger.error(f"删除截图文件失败: {e}")

        # 删除数据库记录
        cursor.execute("""
            DELETE FROM screenshots
            WHERE datetime(timestamp) < datetime('now', ?)
        """, (f'-{days} days',))

        self.connection.commit()
        deleted_count = cursor.rowcount

        logger.info(f"删除 {deleted_count} 条旧记录（保留{days}天）")
        return deleted_count

    def insert_api_log(
        self,
        provider: str,
        model: str,
        tokens_used: int,
        cost: float,
        success: bool,
        error_message: Optional[str] = None
    ) -> None:
        """插入API调用日志"""
        cursor = self.connection.cursor()

        cursor.execute("""
            INSERT INTO api_logs
            (timestamp, provider, model, tokens_used, cost, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            provider,
            model,
            tokens_used,
            cost,
            success,
            error_message
        ))

        self.connection.commit()

    def close(self) -> None:
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            logger.info("数据库连接已关闭")

    def __enter__(self):
        """上下文管理器入口"""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
