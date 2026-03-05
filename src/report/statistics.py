"""
统计分析器
任务归类统计、时长计算、趋势分析
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class StatisticsAnalyzer:
    """统计分析器"""

    def __init__(self, db_manager):
        """
        初始化统计分析器

        Args:
            db_manager: 数据库管理器
        """
        self.db_manager = db_manager

    def get_category_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取生活维度统计

        Args:
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            统计数据字典
        """
        screenshots = self.db_manager.get_screenshots(
            start_time=start_time,
            end_time=end_time
        )

        if not screenshots:
            return {}

        # 统计各维度
        category_stats = defaultdict(lambda: {
            'count': 0,
            'screenshots': [],
            'apps': set()
        })

        for record in screenshots:
            category = record.get('life_category', '未知')
            if category:
                category_stats[category]['count'] += 1
                category_stats[category]['screenshots'].append(record)
                if record.get('app_name'):
                    category_stats[category]['apps'].add(record['app_name'])

        # 计算百分比
        total = len(screenshots)
        result = {}

        for category, stats in category_stats.items():
            result[category] = {
                'count': stats['count'],
                'percentage': (stats['count'] / total * 100),
                'apps': list(stats['apps']),
                'avg_per_day': self._calculate_avg_per_day(
                    stats['screenshots'],
                    start_time,
                    end_time
                )
            }

        return result

    def get_activity_form_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取活动形式统计

        Args:
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            统计数据字典
        """
        screenshots = self.db_manager.get_screenshots(
            start_time=start_time,
            end_time=end_time
        )

        if not screenshots:
            return {}

        # 统计各形式
        form_stats = defaultdict(int)

        for record in screenshots:
            form = record.get('activity_form', '未知')
            if form:
                form_stats[form] += 1

        # 计算百分比
        total = len(screenshots)
        result = {}

        for form, count in form_stats.items():
            result[form] = {
                'count': count,
                'percentage': (count / total * 100)
            }

        return result

    def get_app_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取应用使用统计

        Args:
            start_time: 开始时间
            end_time: 结束时间
            top_n: 返回前N个应用

        Returns:
            应用统计列表
        """
        screenshots = self.db_manager.get_screenshots(
            start_time=start_time,
            end_time=end_time
        )

        if not screenshots:
            return []

        # 统计各应用
        app_stats = defaultdict(lambda: {
            'count': 0,
            'categories': defaultdict(int),
            'forms': defaultdict(int)
        })

        for record in screenshots:
            app = record.get('app_name', '未知')
            category = record.get('life_category', '未知')
            form = record.get('activity_form', '未知')

            app_stats[app]['count'] += 1
            app_stats[app]['categories'][category] += 1
            app_stats[app]['forms'][form] += 1

        # 排序并取前N个
        sorted_apps = sorted(
            app_stats.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:top_n]

        # 格式化结果
        result = []
        for app, stats in sorted_apps:
            main_category = max(
                stats['categories'].items(),
                key=lambda x: x[1]
            )[0] if stats['categories'] else '未知'

            main_form = max(
                stats['forms'].items(),
                key=lambda x: x[1]
            )[0] if stats['forms'] else '未知'

            result.append({
                'app': app,
                'count': stats['count'],
                'main_category': main_category,
                'main_form': main_form,
                'categories': dict(stats['categories']),
                'forms': dict(stats['forms'])
            })

        return result

    def get_hourly_distribution(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[int, int]:
        """
        获取小时分布统计

        Args:
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            小时分布字典 {小时: 计数}
        """
        screenshots = self.db_manager.get_screenshots(
            start_time=start_time,
            end_time=end_time
        )

        if not screenshots:
            return {}

        # 统计各小时
        hourly_stats = defaultdict(int)

        for record in screenshots:
            timestamp = datetime.fromisoformat(record['timestamp'])
            hourly_stats[timestamp.hour] += 1

        return dict(sorted(hourly_stats.items()))

    def get_trend_analysis(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        获取趋势分析（最近N天）

        Args:
            days: 分析天数

        Returns:
            趋势数据字典
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        screenshots = self.db_manager.get_screenshots(
            start_time=start_time,
            end_time=end_time
        )

        if not screenshots:
            return {}

        # 按日期分组
        daily_stats = defaultdict(lambda: {
            'total': 0,
            'categories': defaultdict(int)
        })

        for record in screenshots:
            timestamp = datetime.fromisoformat(record['timestamp'])
            date_str = timestamp.strftime('%Y-%m-%d')
            category = record.get('life_category', '未知')

            daily_stats[date_str]['total'] += 1
            daily_stats[date_str]['categories'][category] += 1

        # 构建趋势数据
        dates = sorted(daily_stats.keys())
        trend_data = {
            'dates': dates,
            'total_counts': [daily_stats[date]['total'] for date in dates],
            'categories': {}
        }

        # 各维度的趋势
        all_categories = set()
        for stats in daily_stats.values():
            all_categories.update(stats['categories'].keys())

        for category in all_categories:
            trend_data['categories'][category] = [
                daily_stats[date]['categories'].get(category, 0)
                for date in dates
            ]

        return trend_data

    def get_efficiency_metrics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取效率指标

        Args:
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            效率指标字典
        """
        screenshots = self.db_manager.get_screenshots(
            start_time=start_time,
            end_time=end_time
        )

        if not screenshots:
            return {}

        # 深度工作时长（连续工作>25分钟）
        deep_work_sessions = self._calculate_deep_work_sessions(screenshots)

        # 任务切换频率
        switch_frequency = self._calculate_switch_frequency(screenshots)

        # 最高效时段
        peak_hours = self._calculate_peak_hours(screenshots)

        # 平均会话时长
        avg_session_duration = self._calculate_avg_session_duration(screenshots)

        return {
            'deep_work_sessions': deep_work_sessions,
            'switch_frequency': switch_frequency,
            'peak_hours': peak_hours,
            'avg_session_duration': avg_session_duration,
            'total_screenshots': len(screenshots)
        }

    def _calculate_avg_per_day(
        self,
        screenshots: List[Dict],
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> float:
        """计算日均次数"""
        if not start_time or not end_time:
            return len(screenshots)

        days = (end_time - start_time).days
        if days == 0:
            days = 1

        return len(screenshots) / days

    def _calculate_deep_work_sessions(
        self,
        screenshots: List[Dict],
        min_duration_minutes: int = 25
    ) -> int:
        """计算深度工作会话数"""
        # 简化版本：统计连续工作类别截图的次数
        work_sessions = 0
        consecutive_count = 0

        for record in screenshots:
            if record.get('life_category') == '工作':
                consecutive_count += 1
            else:
                # 如果连续工作截图>=3次，算一次深度工作
                if consecutive_count >= 3:
                    work_sessions += 1
                consecutive_count = 0

        # 处理最后的连续段
        if consecutive_count >= 3:
            work_sessions += 1

        return work_sessions

    def _calculate_switch_frequency(self, screenshots: List[Dict]) -> float:
        """计算任务切换频率（每小时切换次数）"""
        if len(screenshots) < 2:
            return 0.0

        switches = 0
        prev_category = None

        for record in screenshots:
            category = record.get('life_category')
            if prev_category and category != prev_category:
                switches += 1
            prev_category = category

        # 计算时间跨度（小时）
        first_time = datetime.fromisoformat(screenshots[-1]['timestamp'])
        last_time = datetime.fromisoformat(screenshots[0]['timestamp'])
        hours = (last_time - first_time).total_seconds() / 3600

        if hours == 0:
            hours = 1

        return switches / hours

    def _calculate_peak_hours(self, screenshots: List[Dict]) -> List[int]:
        """计算最高效时段"""
        hourly_count = defaultdict(int)

        for record in screenshots:
            if record.get('life_category') == '工作':
                timestamp = datetime.fromisoformat(record['timestamp'])
                hourly_count[timestamp.hour] += 1

        if not hourly_count:
            return []

        # 返回计数最高的3个小时段
        sorted_hours = sorted(
            hourly_count.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]

        return [hour for hour, _ in sorted_hours]

    def _calculate_avg_session_duration(self, screenshots: List[Dict]) -> float:
        """计算平均会话时长（分钟）"""
        if len(screenshots) < 2:
            return 0.0

        # 计算总时间跨度
        first_time = datetime.fromisoformat(screenshots[-1]['timestamp'])
        last_time = datetime.fromisoformat(screenshots[0]['timestamp'])

        total_minutes = (last_time - first_time).total_seconds() / 60

        return total_minutes / len(screenshots)

    def generate_summary_report(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> str:
        """
        生成统计摘要报告

        Args:
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            Markdown格式的报告
        """
        lines = []
        lines.append("# 统计分析报告\n")

        if start_time and end_time:
            lines.append(
                f"**时间范围**: {start_time.strftime('%Y-%m-%d')} - "
                f"{end_time.strftime('%Y-%m-%d')}\n"
            )

        # 生活维度统计
        category_stats = self.get_category_statistics(start_time, end_time)
        if category_stats:
            lines.append("\n## 生活维度分布\n")
            for category, stats in sorted(
                category_stats.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            ):
                bar = "█" * int(stats['percentage'] / 5)
                lines.append(
                    f"- **{category}**: {bar} {stats['percentage']:.1f}% "
                    f"({stats['count']}次)"
                )

        # 活动形式统计
        form_stats = self.get_activity_form_statistics(start_time, end_time)
        if form_stats:
            lines.append("\n## 活动形式分布\n")
            for form, stats in sorted(
                form_stats.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            ):
                lines.append(f"- **{form}**: {stats['percentage']:.1f}% ({stats['count']}次)")

        # 应用统计
        app_stats = self.get_app_statistics(start_time, end_time, top_n=5)
        if app_stats:
            lines.append("\n## 常用应用 (Top 5)\n")
            for i, app in enumerate(app_stats, 1):
                lines.append(
                    f"{i}. **{app['app']}**: {app['count']}次 "
                    f"[{app['main_category']}]"
                )

        # 效率指标
        efficiency = self.get_efficiency_metrics(start_time, end_time)
        if efficiency:
            lines.append("\n## 效率指标\n")
            lines.append(f"- 深度工作会话: {efficiency['deep_work_sessions']} 次")
            lines.append(f"- 任务切换频率: {efficiency['switch_frequency']:.2f} 次/小时")
            lines.append(f"- 最高效时段: {', '.join(f'{h}:00' for h in efficiency['peak_hours'])}")

        return "\n".join(lines)
