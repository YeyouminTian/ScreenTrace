"""
时间线日志生成器
生成按时间顺序的任务列表报告
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class TimelineGenerator:
    """时间线日志生成器"""

    def __init__(self, db_manager):
        """
        初始化时间线生成器

        Args:
            db_manager: 数据库管理器
        """
        self.db_manager = db_manager

    def generate_timeline(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        group_by_hour: bool = False
    ) -> str:
        """
        生成时间线日志

        Args:
            start_time: 开始时间
            end_time: 结束时间
            group_by_hour: 是否按小时分组

        Returns:
            Markdown格式的时间线日志
        """
        # 查询截图记录
        screenshots = self.db_manager.get_screenshots(
            start_time=start_time,
            end_time=end_time
        )

        if not screenshots:
            logger.warning("没有找到截图记录")
            return "# 时间线日志\n\n暂无数据"

        # 生成报告
        lines = []
        lines.append("# 时间线日志\n")

        if start_time and end_time:
            lines.append(f"**时间范围**: {start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%Y-%m-%d %H:%M')}\n")
        else:
            lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        lines.append(f"**总记录数**: {len(screenshots)}\n")

        # 按日期分组
        if group_by_hour:
            self._generate_hourly_timeline(screenshots, lines)
        else:
            self._generate_simple_timeline(screenshots, lines)

        return "\n".join(lines)

    def _generate_simple_timeline(self, screenshots: List[Dict], lines: List[str]) -> None:
        """
        生成简单时间线

        Args:
            screenshots: 截图记录列表
            lines: 输出行列表
        """
        current_date = None

        for record in screenshots:
            timestamp = datetime.fromisoformat(record['timestamp'])
            date_str = timestamp.strftime('%Y-%m-%d')
            time_str = timestamp.strftime('%H:%M:%S')

            # 日期分隔符
            if date_str != current_date:
                if current_date:
                    lines.append("")  # 空行
                lines.append(f"\n## {date_str}\n")
                current_date = date_str

            # 时间线条目
            life_category = record.get('life_category', '未知')
            activity_form = record.get('activity_form', '未知')
            description = record.get('description', '无描述')
            app_name = record.get('app_name', '未知应用')

            # 添加图标
            icon = self._get_category_icon(life_category)

            lines.append(
                f"**{time_str}** | {icon} {life_category} | {activity_form}\n"
                f"  {description} ({app_name})"
            )

    def _generate_hourly_timeline(self, screenshots: List[Dict], lines: List[str]) -> None:
        """
        生成按小时分组的时间线

        Args:
            screenshots: 截图记录列表
            lines: 输出行列表
        """
        current_date = None
        current_hour = None

        for record in screenshots:
            timestamp = datetime.fromisoformat(record['timestamp'])
            date_str = timestamp.strftime('%Y-%m-%d')
            hour_str = timestamp.strftime('%H:00')

            # 日期分隔符
            if date_str != current_date:
                if current_date:
                    lines.append("")  # 空行
                lines.append(f"\n## {date_str}\n")
                current_date = date_str
                current_hour = None

            # 小时分隔符
            if hour_str != current_hour:
                lines.append(f"\n### {hour_str}\n")
                current_hour = hour_str

            # 时间线条目
            time_str = timestamp.strftime('%H:%M')
            life_category = record.get('life_category', '未知')
            description = record.get('description', '无描述')

            lines.append(f"- **{time_str}** {description} [{life_category}]")

    def _get_category_icon(self, category: str) -> str:
        """
        获取生活维度的图标

        Args:
            category: 生活维度

        Returns:
            图标字符
        """
        icons = {
            '工作': '💼',
            '学习': '📚',
            '休闲': '🎮',
            '生活': '🏠',
            '其他': '📌'
        }
        return icons.get(category, '📌')

    def generate_daily_report(self, date: Optional[datetime] = None) -> str:
        """
        生成日报

        Args:
            date: 日期，默认为今天

        Returns:
            Markdown格式的日报
        """
        if date is None:
            date = datetime.now()

        start_time = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=1)

        lines = []
        lines.append(f"# 日报 - {date.strftime('%Y-%m-%d')}\n")

        # 查询数据
        screenshots = self.db_manager.get_screenshots(
            start_time=start_time,
            end_time=end_time
        )

        if not screenshots:
            lines.append("\n暂无数据")
            return "\n".join(lines)

        # 统计信息
        stats = self._calculate_daily_stats(screenshots)

        lines.append("\n## 概览\n")
        lines.append(f"- 总活动次数: {stats['total_count']}")
        lines.append(f"- 活跃时段: {stats['active_hours']} 小时")
        lines.append(f"- 主要活动: {stats['main_activity']}")
        lines.append(f"- 主要应用: {stats['main_app']}")

        # 生活维度分布
        lines.append("\n## 时间分配\n")
        for category, count in stats['category_distribution'].items():
            percentage = (count / stats['total_count']) * 100
            bar = "█" * int(percentage / 5)  # 进度条
            lines.append(f"- {category}: {bar} {percentage:.1f}%")

        # 详细时间线
        lines.append("\n## 活动记录\n")
        self._generate_simple_timeline(screenshots, lines)

        return "\n".join(lines)

    def _calculate_daily_stats(self, screenshots: List[Dict]) -> Dict[str, Any]:
        """
        计算日统计数据

        Args:
            screenshots: 截图记录列表

        Returns:
            统计数据字典
        """
        if not screenshots:
            return {}

        # 生活维度分布
        category_count = {}
        app_count = {}

        for record in screenshots:
            category = record.get('life_category', '未知')
            app = record.get('app_name', '未知')

            category_count[category] = category_count.get(category, 0) + 1
            app_count[app] = app_count.get(app, 0) + 1

        # 活跃小时数
        hours = set()
        for record in screenshots:
            timestamp = datetime.fromisoformat(record['timestamp'])
            hours.add(timestamp.hour)

        # 主要活动和应用
        main_category = max(category_count.items(), key=lambda x: x[1])[0] if category_count else '未知'
        main_app = max(app_count.items(), key=lambda x: x[1])[0] if app_count else '未知'

        return {
            'total_count': len(screenshots),
            'active_hours': len(hours),
            'main_activity': main_category,
            'main_app': main_app,
            'category_distribution': category_count
        }

    def export_to_file(self, content: str, output_path: str) -> bool:
        """
        导出报告到文件

        Args:
            content: 报告内容
            output_path: 输出文件路径

        Returns:
            是否成功
        """
        try:
            from pathlib import Path
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"报告已导出: {output_path}")
            return True

        except Exception as e:
            logger.error(f"导出报告失败: {e}")
            return False
