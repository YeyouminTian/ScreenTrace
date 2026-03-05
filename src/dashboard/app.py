"""
Web统计面板
Flask应用和API路由
"""

from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
from typing import Optional
import logging

from src.report.statistics import StatisticsAnalyzer
from src.report.timeline import TimelineGenerator
from src.report.narrative import NarrativeGenerator
from src.report.visualization import VisualizationGenerator

logger = logging.getLogger(__name__)


class DashboardApp:
    """Web统计面板应用"""

    def __init__(self, db_manager, api_client=None):
        """
        初始化Web应用

        Args:
            db_manager: 数据库管理器
            api_client: API客户端（可选）
        """
        self.app = Flask(__name__)
        self.db_manager = db_manager
        self.api_client = api_client

        # 初始化各个生成器
        self.stats_analyzer = StatisticsAnalyzer(db_manager)
        self.timeline_generator = TimelineGenerator(db_manager)
        self.narrative_generator = NarrativeGenerator(db_manager, api_client)
        self.viz_generator = VisualizationGenerator(db_manager)

        # 注册路由
        self._register_routes()

        # 添加CORS支持
        @self.app.after_request
        def after_request(response):
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
            return response

    def _register_routes(self):
        """注册Flask路由"""

        @self.app.route('/')
        def index():
            """主页"""
            return render_template('index.html')

        @self.app.route('/api/stats/overview')
        def api_stats_overview():
            """统计概览API"""
            try:
                days = request.args.get('days', 7, type=int)
                end_time = datetime.now()
                start_time = end_time - timedelta(days=days)

                stats = self.db_manager.get_statistics(start_time, end_time)

                return jsonify({
                    'success': True,
                    'data': stats
                })

            except Exception as e:
                logger.error(f"获取统计概览失败: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })

        @self.app.route('/api/stats/category')
        def api_stats_category():
            """生活维度统计API"""
            try:
                days = request.args.get('days', 7, type=int)
                end_time = datetime.now()
                start_time = end_time - timedelta(days=days)

                stats = self.stats_analyzer.get_category_statistics(
                    start_time,
                    end_time
                )

                return jsonify({
                    'success': True,
                    'data': stats
                })

            except Exception as e:
                logger.error(f"获取维度统计失败: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })

        @self.app.route('/api/stats/apps')
        def api_stats_apps():
            """应用统计API"""
            try:
                days = request.args.get('days', 7, type=int)
                top_n = request.args.get('top', 10, type=int)
                end_time = datetime.now()
                start_time = end_time - timedelta(days=days)

                stats = self.stats_analyzer.get_app_statistics(
                    start_time,
                    end_time,
                    top_n
                )

                return jsonify({
                    'success': True,
                    'data': stats
                })

            except Exception as e:
                logger.error(f"获取应用统计失败: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })

        @self.app.route('/api/recent-activities')
        def api_recent_activities():
            """最近活动API"""
            try:
                limit = request.args.get('limit', 20, type=int)

                screenshots = self.db_manager.get_screenshots(limit=limit)

                activities = []
                for record in screenshots:
                    activities.append({
                        'timestamp': record['timestamp'],
                        'app': record.get('app_name', 'Unknown'),
                        'category': record.get('life_category', 'N/A'),
                        'form': record.get('activity_form', 'N/A'),
                        'description': record.get('description', 'N/A')
                    })

                return jsonify({
                    'success': True,
                    'data': activities
                })

            except Exception as e:
                logger.error(f"获取最近活动失败: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })

        @self.app.route('/api/chart/category-pie')
        def api_chart_category_pie():
            """生活维度饼图API"""
            try:
                days = request.args.get('days', 7, type=int)
                end_time = datetime.now()
                start_time = end_time - timedelta(days=days)

                chart_html = self.viz_generator.generate_category_pie_chart(
                    start_time,
                    end_time
                )

                return chart_html

            except Exception as e:
                logger.error(f"生成饼图失败: {e}")
                return f"Error: {str(e)}", 500

        @self.app.route('/api/chart/daily-bar')
        def api_chart_daily_bar():
            """每日活动柱状图API"""
            try:
                days = request.args.get('days', 7, type=int)
                end_time = datetime.now()
                start_time = end_time - timedelta(days=days)

                chart_html = self.viz_generator.generate_daily_bar_chart(
                    start_time,
                    end_time
                )

                return chart_html

            except Exception as e:
                logger.error(f"生成柱状图失败: {e}")
                return f"Error: {str(e)}", 500

        @self.app.route('/api/chart/heatmap')
        def api_chart_heatmap():
            """时段热力图API"""
            try:
                days = request.args.get('days', 7, type=int)
                end_time = datetime.now()
                start_time = end_time - timedelta(days=days)

                chart_html = self.viz_generator.generate_hourly_heatmap(
                    start_time,
                    end_time
                )

                return chart_html

            except Exception as e:
                logger.error(f"生成热力图失败: {e}")
                return f"Error: {str(e)}", 500

        @self.app.route('/api/chart/trend')
        def api_chart_trend():
            """趋势图API"""
            try:
                days = request.args.get('days', 7, type=int)

                chart_html = self.viz_generator.generate_trend_line_chart(days)

                return chart_html

            except Exception as e:
                logger.error(f"生成趋势图失败: {e}")
                return f"Error: {str(e)}", 500

        @self.app.route('/api/chart/dashboard')
        def api_chart_dashboard():
            """综合仪表板API"""
            try:
                days = request.args.get('days', 7, type=int)
                end_time = datetime.now()
                start_time = end_time - timedelta(days=days)

                chart_html = self.viz_generator.generate_combined_dashboard(
                    start_time,
                    end_time
                )

                return chart_html

            except Exception as e:
                logger.error(f"生成仪表板失败: {e}")
                return f"Error: {str(e)}", 500

        @self.app.route('/api/report/timeline')
        def api_report_timeline():
            """时间线报告API"""
            try:
                days = request.args.get('days', 1, type=int)
                end_time = datetime.now()
                start_time = end_time - timedelta(days=days)

                report = self.timeline_generator.generate_timeline(
                    start_time,
                    end_time
                )

                return jsonify({
                    'success': True,
                    'data': report
                })

            except Exception as e:
                logger.error(f"生成时间线失败: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })

        @self.app.route('/api/report/narrative')
        def api_report_narrative():
            """叙述式报告API"""
            try:
                days = request.args.get('days', 7, type=int)
                use_ai = request.args.get('ai', False, type=bool)

                end_time = datetime.now()
                start_time = end_time - timedelta(days=days)

                report = self.narrative_generator.generate_narrative_report(
                    start_time,
                    end_time,
                    use_ai=use_ai
                )

                return jsonify({
                    'success': True,
                    'data': report
                })

            except Exception as e:
                logger.error(f"生成叙述式报告失败: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })

        @self.app.route('/api/efficiency')
        def api_efficiency():
            """效率指标API"""
            try:
                days = request.args.get('days', 7, type=int)
                end_time = datetime.now()
                start_time = end_time - timedelta(days=days)

                metrics = self.stats_analyzer.get_efficiency_metrics(
                    start_time,
                    end_time
                )

                return jsonify({
                    'success': True,
                    'data': metrics
                })

            except Exception as e:
                logger.error(f"获取效率指标失败: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })

    def run(self, host: str = 'localhost', port: int = 8080, debug: bool = False):
        """
        运行Web应用

        Args:
            host: 主机地址
            port: 端口号
            debug: 是否启用调试模式
        """
        logger.info(f"Web面板启动: http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)
