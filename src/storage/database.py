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

        # 迁移现有数据库（添加新字段）
        self.migrate_add_new_fields()

        logger.info(f"数据库初始化成功: {self.db_path}")

    def _create_tables(self) -> None:
        """创建数据库表"""
        cursor = self.connection.cursor()

        # 检查表是否已存在
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='screenshots'
        """)
        table_exists = cursor.fetchone() is not None

        if table_exists:
            # 表已存在，检查并添加新列
            self._migrate_add_columns(cursor)
        else:
            # 表不存在，创建新表
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
                    status TEXT DEFAULT 'ok',
                    confidence TEXT DEFAULT 'high',
                    is_continuation BOOLEAN DEFAULT 0,
                    sensitive_flag BOOLEAN DEFAULT 0,
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

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status
            ON screenshots(status)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_confidence
            ON screenshots(confidence)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_is_continuation
            ON screenshots(is_continuation)
        """)

        self.connection.commit()
        logger.info("数据库表创建成功")

    def _migrate_add_columns(self, cursor) -> None:
        """迁移现有表，添加新列（如果不存在）"""
        # 获取当前表的所有列
        cursor.execute("PRAGMA table_info(screenshots)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        # 需要添加的新列
        new_columns = {
            'status': "ALTER TABLE screenshots ADD COLUMN status TEXT DEFAULT 'ok'",
            'confidence': "ALTER TABLE screenshots ADD COLUMN confidence TEXT DEFAULT 'high'",
            'is_continuation': "ALTER TABLE screenshots ADD COLUMN is_continuation BOOLEAN DEFAULT 0",
            'sensitive_flag': "ALTER TABLE screenshots ADD COLUMN sensitive_flag BOOLEAN DEFAULT 0"
        }

        for column, sql in new_columns.items():
            if column not in existing_columns:
                try:
                    cursor.execute(sql)
                    logger.info(f"迁移成功：添加列 {column}")
                except sqlite3.OperationalError as e:
                    # 忽略列已存在的错误
                    if 'duplicate column' not in str(e).lower():
                        logger.warning(f"迁移列 {column} 时警告: {e}")

        self.connection.commit()

    def migrate_add_new_fields(self) -> None:
        """迁移数据库：添加新字段（用于现有数据库升级）"""
        cursor = self.connection.cursor()

        try:
            cursor.execute("ALTER TABLE screenshots ADD COLUMN status TEXT DEFAULT 'ok'")
        except sqlite3.OperationalError:
            pass  # 字段已存在

        try:
            cursor.execute("ALTER TABLE screenshots ADD COLUMN confidence TEXT DEFAULT 'high'")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE screenshots ADD COLUMN is_continuation BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE screenshots ADD COLUMN sensitive_flag BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        self.connection.commit()
        logger.info("数据库迁移完成：新字段已添加")

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
        api_called: bool = False,
        status: str = 'ok',
        confidence: str = 'high',
        is_continuation: bool = False,
        sensitive_flag: bool = False
    ) -> int:
        """插入截图记录"""
        cursor = self.connection.cursor()

        keywords_json = json.dumps(keywords, ensure_ascii=False) if keywords else None

        cursor.execute("""
            INSERT INTO screenshots
            (timestamp, app_name, window_title, life_category, activity_form,
             description, keywords, screenshot_path, similarity_score, api_called,
             status, confidence, is_continuation, sensitive_flag)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            api_called,
            status,
            confidence,
            is_continuation,
            sensitive_flag
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

    def get_last_analyzed_screenshot(self) -> Optional[Dict[str, Any]]:
        """获取最后一条有API分析结果的截图记录"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM screenshots
            WHERE api_called = 1 AND life_category IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        row = cursor.fetchone()

        if not row:
            return None

        record = dict(row)
        # 解析 keywords JSON
        if record.get('keywords'):
            try:
                record['keywords'] = json.loads(record['keywords'])
            except (json.JSONDecodeError, TypeError):
                try:
                    import ast
                    record['keywords'] = ast.literal_eval(record['keywords'])
                except (ValueError, SyntaxError):
                    record['keywords'] = []

        return record

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

    def migrate_add_new_fields(self) -> None:
        """迁移数据库：添加新字段（用于现有数据库升级）"""
        cursor = self.connection.cursor()

        try:
            cursor.execute("ALTER TABLE screenshots ADD COLUMN status TEXT DEFAULT 'ok'")
        except sqlite3.OperationalError:
            pass  # 字段已存在

        try:
            cursor.execute("ALTER TABLE screenshots ADD COLUMN confidence TEXT DEFAULT 'high'")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE screenshots ADD COLUMN is_continuation BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE screenshots ADD COLUMN sensitive_flag BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        self.connection.commit()
        logger.info("数据库迁移完成：新字段已添加")

    def update_screenshot_analysis(
        self,
        record_id: int,
        life_category: Optional[str] = None,
        activity_form: Optional[str] = None,
        description: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        status: Optional[str] = None,
        confidence: Optional[str] = None,
        is_continuation: Optional[bool] = None,
        sensitive_flag: Optional[bool] = None
    ) -> None:
        """更新截图记录的分析结果"""
        cursor = self.connection.cursor()

        updates = []
        params = []

        if life_category is not None:
            updates.append("life_category = ?")
            params.append(life_category)

        if activity_form is not None:
            updates.append("activity_form = ?")
            params.append(activity_form)

        if description is not None:
            updates.append("description = ?")
            params.append(description)

        if keywords is not None:
            updates.append("keywords = ?")
            params.append(json.dumps(keywords, ensure_ascii=False))

        if status is not None:
            updates.append("status = ?")
            params.append(status)

        if confidence is not None:
            updates.append("confidence = ?")
            params.append(confidence)

        if is_continuation is not None:
            updates.append("is_continuation = ?")
            params.append(is_continuation)

        if sensitive_flag is not None:
            updates.append("sensitive_flag = ?")
            params.append(sensitive_flag)

        updates.append("api_called = 1")

        if updates:
            params.append(record_id)
            cursor.execute(f"""
                UPDATE screenshots
                SET {', '.join(updates)}
                WHERE id = ?
            """, params)

            self.connection.commit()
            logger.debug(f"更新截图记录: ID={record_id}")

    def get_kpi_metrics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取KPI指标（用于Dashboard模块A）"""
        cursor = self.connection.cursor()

        time_condition = ""
        params = []

        if start_time:
            time_condition += " AND timestamp >= ?"
            params.append(start_time.isoformat())

        if end_time:
            time_condition += " AND timestamp <= ?"
            params.append(end_time.isoformat())

        # 1. 总记录时长（所有 status=ok 的记录）
        cursor.execute(f"""
            SELECT MIN(timestamp) as first_record, MAX(timestamp) as last_record,
                   COUNT(*) as total_count
            FROM screenshots
            WHERE status = 'ok' {time_condition}
        """, params)

        row = cursor.fetchone()
        total_duration_minutes = 0
        if row['first_record'] and row['last_record']:
            first = datetime.fromisoformat(row['first_record'])
            last = datetime.fromisoformat(row['last_record'])
            total_duration_minutes = (last - first).total_seconds() / 60

        # 2. 深度工作时长（work + creating，连续>=30分钟）
        cursor.execute(f"""
            SELECT COUNT(*) as deep_work_count
            FROM screenshots
            WHERE life_category = 'work'
              AND activity_form = 'creating'
              AND status = 'ok' {time_condition}
        """, params)

        deep_work_count = cursor.fetchone()['deep_work_count'] or 0

        # 3. 上下文切换次数（is_continuation=false 的记录数）
        cursor.execute(f"""
            SELECT COUNT(*) as switch_count
            FROM screenshots
            WHERE is_continuation = 0 {time_condition}
        """, params)

        context_switches = cursor.fetchone()['switch_count'] or 0

        # 4. 置信度统计
        cursor.execute(f"""
            SELECT confidence, COUNT(*) as count
            FROM screenshots
            WHERE 1=1 {time_condition}
            GROUP BY confidence
        """, params)

        confidence_stats = {row['confidence']: row['count'] for row in cursor.fetchall()}
        total_for_confidence = sum(confidence_stats.values()) or 1
        low_confidence_ratio = confidence_stats.get('low', 0) / total_for_confidence

        # 5. 状态统计
        cursor.execute(f"""
            SELECT status, COUNT(*) as count
            FROM screenshots
            WHERE 1=1 {time_condition}
            GROUP BY status
        """, params)

        status_stats = {row['status']: row['count'] for row in cursor.fetchall()}
        unrecognizable_ratio = status_stats.get('unrecognizable', 0) / total_for_confidence

        # 6. 最长专注段（通过 is_continuation 连续 true 计算）
        cursor.execute(f"""
            SELECT timestamp, is_continuation, life_category
            FROM screenshots
            WHERE 1=1 {time_condition}
            ORDER BY timestamp ASC
        """, params)

        records = cursor.fetchall()
        max_focus_duration = 0
        current_focus = 0
        current_category = None

        for record in records:
            if record['is_continuation'] and record['life_category'] == current_category:
                current_focus += 1
            else:
                if current_focus > max_focus_duration:
                    max_focus_duration = current_focus
                current_focus = 1 if record['is_continuation'] else 0
                current_category = record['life_category']

        if current_focus > max_focus_duration:
            max_focus_duration = current_focus

        # 7. 综合专注度得分
        total_records = row['total_count'] or 1
        deep_work_ratio = deep_work_count / total_records
        switch_rate = context_switches / total_records

        focus_score = (
            deep_work_ratio * 0.4 +
            (max_focus_duration / max(total_records, 1)) * 0.3 +
            (1 - min(switch_rate, 1)) * 0.3
        ) * 100

        return {
            'total_duration_minutes': round(total_duration_minutes, 1),
            'deep_work_count': deep_work_count,
            'context_switches': context_switches,
            'focus_score': round(focus_score, 1),
            'max_focus_duration': max_focus_duration,
            'low_confidence_ratio': round(low_confidence_ratio * 100, 1),
            'unrecognizable_ratio': round(unrecognizable_ratio * 100, 1),
            'total_records': row['total_count'] or 0
        }

    def get_timeline_data(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """获取时间线数据（用于Dashboard模块B）"""
        cursor = self.connection.cursor()

        time_condition = ""
        params = []

        if start_time:
            time_condition += " AND timestamp >= ?"
            params.append(start_time.isoformat())

        if end_time:
            time_condition += " AND timestamp <= ?"
            params.append(end_time.isoformat())

        cursor.execute(f"""
            SELECT timestamp, app_name, window_title, life_category,
                   activity_form, description, is_continuation, screenshot_path
            FROM screenshots
            WHERE status = 'ok' {time_condition}
            ORDER BY timestamp ASC
        """, params)

        rows = cursor.fetchall()
        results = []

        for row in rows:
            record = dict(row)
            # 解析 keywords
            if record.get('keywords'):
                try:
                    record['keywords'] = json.loads(record['keywords'])
                except (json.JSONDecodeError, TypeError):
                    record['keywords'] = []
            results.append(record)

        return results

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
