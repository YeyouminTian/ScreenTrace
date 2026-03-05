"""
可视化图表生成器
生成饼图、柱状图、时间轴、热力图等图表
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import logging

logger = logging.getLogger(__name__)


class VisualizationGenerator:
    """可视化图表生成器"""

    def __init__(self, db_manager):
        """
        初始化可视化生成器

        Args:
            db_manager: 数据库管理器
        """
        self.db_manager = db_manager

    def generate_category_pie_chart(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        title: str = "生活维度分布"
    ) -> str:
        """
        生成生活维度饼图

        Args:
            start_time: 开始时间
            end_time: 结束时间
            title: 图表标题

        Returns:
            Plotly图表的HTML字符串
        """
        # 查询数据
        screenshots = self.db_manager.get_screenshots(
            start_time=start_time,
            end_time=end_time
        )

        if not screenshots:
            return self._generate_empty_chart("暂无数据")

        # 统计各维度
        category_count = {}
        for record in screenshots:
            category = record.get('life_category', '未知')
            category_count[category] = category_count.get(category, 0) + 1

        # 创建饼图
        fig = go.Figure(data=[go.Pie(
            labels=list(category_count.keys()),
            values=list(category_count.values()),
            hole=0.3,  # 环形图
            textinfo='label+percent',
            textposition='outside',
            marker=dict(
                colors=px.colors.qualitative.Set3
            )
        )])

        fig.update_layout(
            title=title,
            showlegend=True,
            height=500
        )

        return fig.to_html(include_plotlyjs=True, full_html=False)

    def generate_daily_bar_chart(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        title: str = "每日活动统计"
    ) -> str:
        """
        生成每日活动柱状图

        Args:
            start_time: 开始时间
            end_time: 结束时间
            title: 图表标题

        Returns:
            Plotly图表的HTML字符串
        """
        # 查询数据
        screenshots = self.db_manager.get_screenshots(
            start_time=start_time,
            end_time=end_time
        )

        if not screenshots:
            return self._generate_empty_chart("暂无数据")

        # 按日期和维度统计
        daily_stats = {}
        for record in screenshots:
            timestamp = datetime.fromisoformat(record['timestamp'])
            date_str = timestamp.strftime('%Y-%m-%d')
            category = record.get('life_category', '未知')

            if date_str not in daily_stats:
                daily_stats[date_str] = {}

            daily_stats[date_str][category] = daily_stats[date_str].get(category, 0) + 1

        # 准备数据
        dates = sorted(daily_stats.keys())
        all_categories = set()
        for stats in daily_stats.values():
            all_categories.update(stats.keys())

        # 创建堆叠柱状图
        fig = go.Figure()

        colors = px.colors.qualitative.Set2

        for i, category in enumerate(sorted(all_categories)):
            values = [daily_stats[date].get(category, 0) for date in dates]

            fig.add_trace(go.Bar(
                name=category,
                x=dates,
                y=values,
                marker_color=colors[i % len(colors)]
            ))

        fig.update_layout(
            title=title,
            barmode='stack',
            xaxis_title='日期',
            yaxis_title='活动次数',
            height=500,
            xaxis=dict(tickangle=-45)
        )

        return fig.to_html(include_plotlyjs=True, full_html=False)

    def generate_hourly_heatmap(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        title: str = "活动时段热力图"
    ) -> str:
        """
        生成时段热力图

        Args:
            start_time: 开始时间
            end_time: 结束时间
            title: 图表标题

        Returns:
            Plotly图表的HTML字符串
        """
        # 查询数据
        screenshots = self.db_manager.get_screenshots(
            start_time=start_time,
            end_time=end_time
        )

        if not screenshots:
            return self._generate_empty_chart("暂无数据")

        # 按星期和小时统计
        heatmap_data = [[0] * 24 for _ in range(7)]  # 7天 x 24小时

        for record in screenshots:
            timestamp = datetime.fromisoformat(record['timestamp'])
            weekday = timestamp.weekday()  # 0=周一
            hour = timestamp.hour

            heatmap_data[weekday][hour] += 1

        # 创建热力图
        weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        hours = [f'{i}:00' for i in range(24)]

        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data,
            x=hours,
            y=weekdays,
            colorscale='Blues',
            hoverongaps=False
        ))

        fig.update_layout(
            title=title,
            xaxis_title='小时',
            yaxis_title='星期',
            height=400
        )

        return fig.to_html(include_plotlyjs=True, full_html=False)

    def generate_trend_line_chart(
        self,
        days: int = 7,
        title: str = "活动趋势图"
    ) -> str:
        """
        生成趋势折线图

        Args:
            days: 统计天数
            title: 图表标题

        Returns:
            Plotly图表的HTML字符串
        """
        # 计算时间范围
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        screenshots = self.db_manager.get_screenshots(
            start_time=start_time,
            end_time=end_time
        )

        if not screenshots:
            return self._generate_empty_chart("暂无数据")

        # 按日期和维度统计
        daily_stats = {}
        for record in screenshots:
            timestamp = datetime.fromisoformat(record['timestamp'])
            date_str = timestamp.strftime('%m-%d')
            category = record.get('life_category', '未知')

            if date_str not in daily_stats:
                daily_stats[date_str] = {}

            daily_stats[date_str][category] = daily_stats[date_str].get(category, 0) + 1

        # 准备数据
        dates = sorted(daily_stats.keys())
        all_categories = set()
        for stats in daily_stats.values():
            all_categories.update(stats.keys())

        # 创建折线图
        fig = go.Figure()

        colors = px.colors.qualitative.Set1

        for i, category in enumerate(sorted(all_categories)):
            values = [daily_stats[date].get(category, 0) for date in dates]

            fig.add_trace(go.Scatter(
                name=category,
                x=dates,
                y=values,
                mode='lines+markers',
                line=dict(color=colors[i % len(colors)], width=2),
                marker=dict(size=8)
            ))

        fig.update_layout(
            title=title,
            xaxis_title='日期',
            yaxis_title='活动次数',
            height=500,
            hovermode='x unified'
        )

        return fig.to_html(include_plotlyjs=True, full_html=False)

    def generate_app_usage_chart(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        top_n: int = 10,
        title: str = "应用使用统计"
    ) -> str:
        """
        生成应用使用柱状图

        Args:
            start_time: 开始时间
            end_time: 结束时间
            top_n: 显示前N个应用
            title: 图表标题

        Returns:
            Plotly图表的HTML字符串
        """
        # 查询数据
        screenshots = self.db_manager.get_screenshots(
            start_time=start_time,
            end_time=end_time
        )

        if not screenshots:
            return self._generate_empty_chart("暂无数据")

        # 统计各应用
        app_count = {}
        for record in screenshots:
            app = record.get('app_name', '未知')
            app_count[app] = app_count.get(app, 0) + 1

        # 取前N个
        sorted_apps = sorted(
            app_count.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

        apps = [app for app, _ in sorted_apps]
        counts = [count for _, count in sorted_apps]

        # 创建横向柱状图
        fig = go.Figure(go.Bar(
            x=counts,
            y=apps,
            orientation='h',
            marker_color=px.colors.qualitative.Pastel
        ))

        fig.update_layout(
            title=title,
            xaxis_title='使用次数',
            yaxis_title='应用',
            height=max(400, top_n * 30),
            yaxis=dict(autorange="reversed")  # 从上到下排序
        )

        return fig.to_html(include_plotlyjs=True, full_html=False)

    def generate_combined_dashboard(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> str:
        """
        生成综合仪表板（多个图表组合）

        Args:
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            Plotly图表的HTML字符串
        """
        # 查询数据
        screenshots = self.db_manager.get_screenshots(
            start_time=start_time,
            end_time=end_time
        )

        if not screenshots:
            return self._generate_empty_chart("暂无数据")

        # 统计数据
        category_count = {}
        app_count = {}

        for record in screenshots:
            category = record.get('life_category', '未知')
            app = record.get('app_name', '未知')

            category_count[category] = category_count.get(category, 0) + 1
            app_count[app] = app_count.get(app, 0) + 1

        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('生活维度分布', '应用使用Top10', '每日活动趋势', '活动时段分布'),
            specs=[
                [{"type": "pie"}, {"type": "bar"}],
                [{"type": "scatter"}, {"type": "bar"}]
            ]
        )

        # 1. 饼图
        fig.add_trace(
            go.Pie(
                labels=list(category_count.keys()),
                values=list(category_count.values()),
                name="维度分布"
            ),
            row=1, col=1
        )

        # 2. 应用柱状图
        top_apps = sorted(app_count.items(), key=lambda x: x[1], reverse=True)[:10]
        fig.add_trace(
            go.Bar(
                x=[app for app, _ in top_apps],
                y=[count for _, count in top_apps],
                name="应用使用"
            ),
            row=1, col=2
        )

        # 3. 趋势图（简化版）
        daily_count = {}
        for record in screenshots:
            timestamp = datetime.fromisoformat(record['timestamp'])
            date_str = timestamp.strftime('%m-%d')
            daily_count[date_str] = daily_count.get(date_str, 0) + 1

        dates = sorted(daily_count.keys())
        counts = [daily_count[date] for date in dates]

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=counts,
                mode='lines+markers',
                name="活动趋势"
            ),
            row=2, col=1
        )

        # 4. 时段分布
        hourly_count = {}
        for record in screenshots:
            timestamp = datetime.fromisoformat(record['timestamp'])
            hour = timestamp.hour
            hourly_count[hour] = hourly_count.get(hour, 0) + 1

        hours = sorted(hourly_count.keys())
        hour_counts = [hourly_count[h] for h in hours]

        fig.add_trace(
            go.Bar(
                x=[f'{h}:00' for h in hours],
                y=hour_counts,
                name="时段分布"
            ),
            row=2, col=2
        )

        # 更新布局
        fig.update_layout(
            height=800,
            showlegend=False,
            title_text="ScreenTrace 统计仪表板"
        )

        return fig.to_html(include_plotlyjs=True, full_html=False)

    def _generate_empty_chart(self, message: str) -> str:
        """
        生成空图表

        Args:
            message: 提示信息

        Returns:
            HTML字符串
        """
        fig = go.Figure()

        fig.add_annotation(
            text=message,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=20)
        )

        fig.update_layout(
            height=400,
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False)
        )

        return fig.to_html(include_plotlyjs=True, full_html=False)
