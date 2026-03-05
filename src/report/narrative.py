"""
叙述式报告生成器
使用AI生成日记风格的总结报告
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class NarrativeGenerator:
    """叙述式报告生成器"""

    def __init__(self, db_manager, api_client=None):
        """
        初始化叙述式报告生成器

        Args:
            db_manager: 数据库管理器
            api_client: API客户端（可选，用于AI生成）
        """
        self.db_manager = db_manager
        self.api_client = api_client

    def generate_narrative_report(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        use_ai: bool = False
    ) -> str:
        """
        生成叙述式报告

        Args:
            start_time: 开始时间
            end_time: 结束时间
            use_ai: 是否使用AI生成

        Returns:
            Markdown格式的叙述式报告
        """
        # 查询数据
        screenshots = self.db_manager.get_screenshots(
            start_time=start_time,
            end_time=end_time
        )

        if not screenshots:
            logger.warning("没有找到截图记录")
            return "# 工作总结\n\n暂无数据"

        # 时间范围描述
        time_range = self._get_time_range_description(start_time, end_time)

        if use_ai and self.api_client:
            # 使用AI生成
            return self._generate_with_ai(screenshots, time_range)
        else:
            # 使用模板生成
            return self._generate_with_template(screenshots, time_range)

    def _generate_with_ai(
        self,
        screenshots: List[Dict],
        time_range: str
    ) -> str:
        """
        使用AI生成叙述式报告

        Args:
            screenshots: 截图记录列表
            time_range: 时间范围描述

        Returns:
            AI生成的报告
        """
        try:
            # 准备数据
            formatted_data = []
            for i, record in enumerate(screenshots[:50], 1):  # 限制数量
                timestamp = datetime.fromisoformat(record['timestamp'])
                time_str = timestamp.strftime('%H:%M')
                description = record.get('description', '无描述')
                app = record.get('app_name', '未知应用')

                formatted_data.append(
                    f"{i}. [{time_str}] {description} ({app})"
                )

            data_str = "\n".join(formatted_data)

            # 构建Prompt
            prompt = f"""请根据以下活动记录，生成一份{time_range}的工作总结报告。

【活动记录】
{data_str}

【要求】
1. 用叙述性语言总结主要工作内容
2. 按工作类型分组描述
3. 突出重要成果和关键任务
4. 语言简洁、专业，类似工作周报风格
5. 字数控制在300-500字

【输出格式】
直接输出报告文本，不要包含额外的JSON或格式标记。"""

            # 调用API
            # 注意：这里需要纯文本响应，不是JSON
            result = self.api_client.analyze_image(
                screenshots[0]['screenshot_path'],  # 临时使用第一张图
                prompt
            )

            if result and isinstance(result, str):
                # 如果返回的是纯文本
                return f"# 工作总结 - {time_range}\n\n{result}"
            elif result and isinstance(result, dict):
                # 如果返回的是JSON，提取文本
                text = result.get('text', result.get('content', ''))
                return f"# 工作总结 - {time_range}\n\n{text}"
            else:
                logger.warning("AI生成失败，使用模板生成")
                return self._generate_with_template(screenshots, time_range)

        except Exception as e:
            logger.error(f"AI生成报告失败: {e}")
            return self._generate_with_template(screenshots, time_range)

    def _generate_with_template(
        self,
        screenshots: List[Dict],
        time_range: str
    ) -> str:
        """
        使用模板生成叙述式报告

        Args:
            screenshots: 截图记录列表
            time_range: 时间范围描述

        Returns:
            模板生成的报告
        """
        lines = []
        lines.append(f"# 工作总结 - {time_range}\n")

        # 统计分析
        stats = self._analyze_screenshots(screenshots)

        lines.append("\n## 概述\n")
        lines.append(
            f"{time_range}共记录了{stats['total_count']}次活动，"
            f"涵盖{len(stats['categories'])}个生活维度。\n"
        )

        # 主要工作
        if '工作' in stats['categories']:
            work_items = [s for s in screenshots if s.get('life_category') == '工作']
            lines.append("\n## 工作内容\n")

            # 按应用分组
            work_by_app = {}
            for item in work_items:
                app = item.get('app_name', '未知')
                if app not in work_by_app:
                    work_by_app[app] = []
                work_by_app[app].append(item)

            for app, items in work_by_app.items():
                descriptions = [i.get('description', '') for i in items[:3]]
                lines.append(f"- 在{app}中：{', '.join(descriptions)}")

        # 学习成长
        if '学习' in stats['categories']:
            learn_items = [s for s in screenshots if s.get('life_category') == '学习']
            lines.append("\n## 学习成长\n")

            topics = set()
            for item in learn_items:
                keywords = item.get('keywords', [])
                if isinstance(keywords, str):
                    keywords = eval(keywords)  # 从JSON字符串转换
                topics.update(keywords[:2])

            lines.append(
                f"- 学习内容涵盖：{', '.join(list(topics)[:5])}\n"
                f"- 共计{len(learn_items)}次学习活动"
            )

        # 休闲放松
        if '休闲' in stats['categories']:
            leisure_items = [s for s in screenshots if s.get('life_category') == '休闲']
            lines.append("\n## 休闲放松\n")
            lines.append(f"- 休闲活动：{len(leisure_items)}次")

            # 统计休闲应用
            leisure_apps = {}
            for item in leisure_items:
                app = item.get('app_name', '未知')
                leisure_apps[app] = leisure_apps.get(app, 0) + 1

            top_leisure = sorted(
                leisure_apps.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]

            for app, count in top_leisure:
                lines.append(f"  - {app}: {count}次")

        # 时间分配
        lines.append("\n## 时间分配\n")
        for category, count in sorted(
            stats['categories'].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            percentage = (count / stats['total_count']) * 100
            lines.append(f"- {category}: {percentage:.1f}% ({count}次)")

        # 总结
        lines.append("\n## 总结\n")
        main_category = max(
            stats['categories'].items(),
            key=lambda x: x[1]
        )[0] if stats['categories'] else '未知'

        summary = f"{time_range}的活动主要集中在{main_category}方面"

        if '工作' in stats['categories'] and stats['categories']['工作'] / stats['total_count'] > 0.5:
            summary += "，工作投入较大"

        if '学习' in stats['categories'] and stats['categories']['学习'] / stats['total_count'] > 0.2:
            summary += "，保持了良好的学习习惯"

        summary += "。继续保持！"

        lines.append(summary)

        return "\n".join(lines)

    def _analyze_screenshots(self, screenshots: List[Dict]) -> Dict[str, Any]:
        """
        分析截图数据

        Args:
            screenshots: 截图记录列表

        Returns:
            统计数据字典
        """
        categories = {}
        apps = {}

        for record in screenshots:
            category = record.get('life_category', '未知')
            app = record.get('app_name', '未知')

            categories[category] = categories.get(category, 0) + 1
            apps[app] = apps.get(app, 0) + 1

        return {
            'total_count': len(screenshots),
            'categories': categories,
            'apps': apps
        }

    def _get_time_range_description(
        self,
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> str:
        """
        获取时间范围描述

        Args:
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            时间范围描述字符串
        """
        if not start_time or not end_time:
            return "近期"

        days = (end_time - start_time).days

        if days == 0:
            return "今天"
        elif days == 1:
            return "昨天"
        elif days <= 7:
            return "本周"
        elif days <= 30:
            return "本月"
        else:
            return f"{start_time.strftime('%Y-%m-%d')} 至 {end_time.strftime('%Y-%m-%d')}"

    def generate_weekly_report(self, week_offset: int = 0) -> str:
        """
        生成周报

        Args:
            week_offset: 周偏移量（0=本周，-1=上周）

        Returns:
            Markdown格式的周报
        """
        # 计算本周的起止时间
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_week = start_of_week + timedelta(days=7)

        return self.generate_narrative_report(
            start_time=start_of_week,
            end_time=end_of_week,
            use_ai=False
        )

    def generate_monthly_report(self, month_offset: int = 0) -> str:
        """
        生成月报

        Args:
            month_offset: 月偏移量（0=本月，-1=上月）

        Returns:
            Markdown格式的月报
        """
        # 计算本月的起止时间
        today = datetime.now()
        first_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if month_offset != 0:
            # 调整月份
            month = (today.month + month_offset - 1) % 12 + 1
            year = today.year + (today.month + month_offset - 1) // 12
            first_of_month = first_of_month.replace(year=year, month=month)

        # 下月第一天
        if first_of_month.month == 12:
            first_of_next_month = first_of_month.replace(year=first_of_month.year + 1, month=1)
        else:
            first_of_next_month = first_of_month.replace(month=first_of_month.month + 1)

        return self.generate_narrative_report(
            start_time=first_of_month,
            end_time=first_of_next_month,
            use_ai=False
        )
