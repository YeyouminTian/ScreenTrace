"""
ScreenTrace Dashboard - FastAPI 后端
基于 FastAPI 的现代 Web 统计面板，提供 JSON API 和交互式图表
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# 全局变量（将在 startup 中初始化）
_db_manager = None
_api_client = None
_stats_analyzer = None
_timeline_generator = None
_narrative_generator = None
_viz_generator = None


def get_db():
    """获取数据库管理器"""
    return _db_manager


class ScreenshotInDB(BaseModel):
    """截图记录模型"""
    timestamp: Optional[str] = None
    app_name: Optional[str] = None
    window_title: Optional[str] = None
    life_category: Optional[str] = None
    activity_form: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    status: Optional[str] = 'ok'
    confidence: Optional[str] = 'high'
    is_continuation: Optional[bool] = False
    sensitive_flag: Optional[bool] = False


class StatsOverview(BaseModel):
    """统计概览模型"""
    total_records: int
    life_category: Dict[str, int]
    activity_form: Dict[str, int]
    top_apps: Dict[str, int]


class KPIMetrics(BaseModel):
    """KPI 指标模型"""
    total_duration_minutes: float
    deep_work_count: int
    context_switches: int
    focus_score: float
    max_focus_duration: int
    low_confidence_ratio: float
    unrecognizable_ratio: float
    total_records: int


class TimelineData(BaseModel):
    """时间线数据模型"""
    records: List[Dict[str, Any]]


class APIResponse(BaseModel):
    """通用 API 响应模型"""
    success: bool
    data: Any = None
    error: str = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global _db_manager, _api_client, _stats_analyzer, _timeline_generator, _narrative_generator, _viz_generator

    # Startup
    logger.info("正在初始化 FastAPI 应用...")

    # 加载配置
    try:
        from src.utils.config import ConfigManager
        from src.storage.database import DatabaseManager
        from src.api.client import APIClient
        from src.report.statistics import StatisticsAnalyzer
        from src.report.timeline import TimelineGenerator
        from src.report.narrative import NarrativeGenerator
        from src.report.visualization import VisualizationGenerator

        config_manager = ConfigManager()
        config_manager.load()

        # 初始化数据库
        db_path = config_manager.get("storage.database_path", "./data/screenTrace.db")
        _db_manager = DatabaseManager(db_path)
        _db_manager.initialize()
        _db_manager.migrate_add_new_fields()  # 确保新字段存在
        logger.info("数据库初始化成功")

        # 初始化 API 客户端
        api_config = config_manager.config.get("api", {})
        if api_config.get("api_key"):
            _api_client = APIClient(api_config)
            logger.info("API 客户端初始化成功")

        # 初始化报告生成器
        _stats_analyzer = StatisticsAnalyzer(_db_manager)
        _timeline_generator = TimelineGenerator(_db_manager)
        _narrative_generator = NarrativeGenerator(_db_manager, _api_client)
        _viz_generator = VisualizationGenerator(_db_manager)
        logger.info("报告生成器初始化成功")

    except Exception as e:
        logger.error(f"初始化失败: {e}")
        raise

    yield

    # Shutdown
    if _db_manager:
        _db_manager.close()
    logger.info("FastAPI 应用已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="ScreenTrace Dashboard",
    description="智能屏幕活动追踪与时间管理工具",
    version="2.0.0",
    lifespan=lifespan
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 获取静态文件目录
_current_dir = Path(__file__).parent
_static_dir = _current_dir / "static"
_templates_dir = _current_dir / "templates"

if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

templates = Jinja2Templates(directory=str(_templates_dir))


# ==================== 页面路由 ====================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """主页"""
    template_path = _templates_dir / "index.html"
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


@app.get("/docs")
async def api_docs():
    """API 文档页面"""
    return {
        "message": "访问 /docs 查看交互式 API 文档",
        "endpoints": {
            "overview": "/api/stats/overview",
            "kpi": "/api/stats/kpi",
            "category": "/api/stats/category",
            "apps": "/api/stats/apps",
            "timeline": "/api/timeline",
            "recent": "/api/recent-activities",
            "efficiency": "/api/efficiency"
        }
    }


# ==================== 统计 API ====================

def parse_date_params(days: int, start_date: Optional[str], end_date: Optional[str]):
    """解析日期参数，返回 start_time 和 end_time"""
    end_time = datetime.now()

    if start_date and end_date:
        # 使用自定义日期范围
        start_time = datetime.strptime(start_date, '%Y-%m-%d')
        start_time = start_time.replace(hour=0, minute=0, second=0)
        end_time = datetime.strptime(end_date, '%Y-%m-%d')
        end_time = end_time.replace(hour=23, minute=59, second=59)
    else:
        # 使用天数
        start_time = end_time - timedelta(days=days)

    return start_time, end_time


@app.get("/api/stats/overview")
async def get_stats_overview(
    days: int = Query(7, ge=1, le=365),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """统计概览 API"""
    try:
        start_time, end_time = parse_date_params(days, start_date, end_date)
        stats = _db_manager.get_statistics(start_time, end_time)

        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"获取统计概览失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/stats/kpi")
async def get_kpi_metrics(
    days: int = Query(7, ge=1, le=365),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """KPI 指标 API（模块 A）"""
    try:
        start_time, end_time = parse_date_params(days, start_date, end_date)

        metrics = _db_manager.get_kpi_metrics(start_time, end_time)

        return {
            "success": True,
            "data": metrics
        }
    except Exception as e:
        logger.error(f"获取KPI指标失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/stats/category")
async def get_category_stats(
    days: int = Query(7, ge=1, le=365),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """生活维度统计 API（模块 C）"""
    try:
        start_time, end_time = parse_date_params(days, start_date, end_date)

        stats = _stats_analyzer.get_category_statistics(start_time, end_time)

        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"获取维度统计失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/stats/apps")
async def get_app_stats(
    days: int = Query(7, ge=1, le=365),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    top: int = Query(10, ge=1, le=50)
):
    """应用统计 API（模块 E）"""
    try:
        start_time, end_time = parse_date_params(days, start_date, end_date)
        start_time = end_time - timedelta(days=days)

        stats = _stats_analyzer.get_app_statistics(start_time, end_time, top)

        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"获取应用统计失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/stats/activity-form")
async def get_activity_form_stats(days: int = Query(7, ge=1, le=365)):
    """活动形式统计 API（模块 D）"""
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        stats = _stats_analyzer.get_category_statistics(start_time, end_time)

        return {
            "success": True,
            "data": stats.get('activity_form', {})
        }
    except Exception as e:
        logger.error(f"获取活动形式统计失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# ==================== 时间线 API ====================

@app.get("/api/timeline")
async def get_timeline(days: int = Query(1, ge=1, le=365)):
    """时间线 API（模块 B）"""
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        records = _db_manager.get_timeline_data(start_time, end_time)

        return {
            "success": True,
            "data": {
                "records": records,
                "total": len(records)
            }
        }
    except Exception as e:
        logger.error(f"获取时间线失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/recent-activities")
async def get_recent_activities(limit: int = Query(20, ge=1, le=100)):
    """最近活动 API"""
    try:
        screenshots = _db_manager.get_screenshots(limit=limit)

        activities = []
        for record in screenshots:
            activities.append({
                'timestamp': record['timestamp'],
                'app': record.get('app_name', 'Unknown'),
                'category': record.get('life_category', 'N/A'),
                'form': record.get('activity_form', 'N/A'),
                'description': record.get('description', 'N/A'),
                'status': record.get('status', 'ok'),
                'confidence': record.get('confidence', 'high'),
                'is_continuation': record.get('is_continuation', False)
            })

        return {
            "success": True,
            "data": activities
        }
    except Exception as e:
        logger.error(f"获取最近活动失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# ==================== 效率指标 API ====================

@app.get("/api/efficiency")
async def get_efficiency_metrics(days: int = Query(7, ge=1, le=365)):
    """效率指标 API"""
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        metrics = _stats_analyzer.get_efficiency_metrics(start_time, end_time)

        return {
            "success": True,
            "data": metrics
        }
    except Exception as e:
        logger.error(f"获取效率指标失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# ==================== 报告 API ====================

@app.get("/api/report/timeline")
async def get_timeline_report(days: int = Query(1, ge=1, le=365)):
    """时间线报告 API"""
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        report = _timeline_generator.generate_timeline(start_time, end_time)

        return {
            "success": True,
            "data": report
        }
    except Exception as e:
        logger.error(f"生成时间线失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/report/narrative")
async def get_narrative_report(
    days: int = Query(7, ge=1, le=365),
    ai: bool = Query(False)
):
    """叙述式报告 API"""
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        report = _narrative_generator.generate_narrative_report(
            start_time,
            end_time,
            use_ai=ai
        )

        return {
            "success": True,
            "data": report
        }
    except Exception as e:
        logger.error(f"生成叙述式报告失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# ==================== 数据质量 API（模块 J） ====================

@app.get("/api/quality/metrics")
async def get_quality_metrics(days: int = Query(7, ge=1, le=365)):
    """数据质量指标 API"""
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        # 获取 KPI 指标
        kpi = _db_manager.get_kpi_metrics(start_time, end_time)

        # 构建质量指标
        quality = {
            "low_confidence_rate": kpi['low_confidence_ratio'],
            "unrecognizable_rate": kpi['unrecognizable_ratio'],
            "total_records": kpi['total_records'],
            "status": "ok" if kpi['low_confidence_ratio'] < 15 else "warning"
        }

        return {
            "success": True,
            "data": quality
        }
    except Exception as e:
        logger.error(f"获取数据质量指标失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# ==================== ECharts 图表数据 API（第三阶段） ====================

@app.get("/api/charts/category-pie")
async def get_category_pie_chart(days: int = Query(7, ge=1, le=365)):
    """生活维度饼图数据（ECharts）"""
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        stats = _db_manager.get_statistics(start_time, end_time)
        category_data = stats.get('life_category', {})

        # 转换为 ECharts 饼图格式
        data = [
            {"name": k, "value": v}
            for k, v in category_data.items()
        ]

        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        logger.error(f"获取饼图数据失败: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/charts/daily-bar")
async def get_daily_bar_chart(days: int = Query(7, ge=1, le=365)):
    """每日活动柱状图数据（ECharts）"""
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        # 获取每日数据
        cursor = _db_manager.connection.cursor()
        cursor.execute("""
            SELECT DATE(timestamp) as date, COUNT(*) as count
            FROM screenshots
            WHERE timestamp >= ? AND timestamp <= ?
            GROUP BY DATE(timestamp)
            ORDER BY date ASC
        """, (start_time.isoformat(), end_time.isoformat()))

        rows = cursor.fetchall()

        dates = [row['date'] for row in rows]
        counts = [row['count'] for row in rows]

        return {
            "success": True,
            "data": {
                "dates": dates,
                "counts": counts
            }
        }
    except Exception as e:
        logger.error(f"获取柱状图数据失败: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/charts/heatmap")
async def get_heatmap_chart(days: int = Query(7, ge=1, le=365)):
    """时段热力图数据（ECharts）"""
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        cursor = _db_manager.connection.cursor()
        cursor.execute("""
            SELECT
                CAST(strftime('%w', timestamp) AS INTEGER) as weekday,
                CAST(strftime('%H', timestamp) AS INTEGER) as hour,
                COUNT(*) as count
            FROM screenshots
            WHERE timestamp >= ? AND timestamp <= ?
            GROUP BY weekday, hour
            ORDER BY weekday, hour
        """, (start_time.isoformat(), end_time.isoformat()))

        rows = cursor.fetchall()

        # 转换为 ECharts 热力图格式
        data = [[row['weekday'], row['hour'], row['count']] for row in rows]

        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        logger.error(f"获取热力图数据失败: {e}")
        return {"success": False, "error": str(e)}


# ==================== 健康检查 ====================

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8080)
