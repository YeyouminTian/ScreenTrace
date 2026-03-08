"""
启动 ScreenTrace Dashboard (FastAPI 版本)
使用 FastAPI 后端提供更现代的 API 和更好的性能
"""

import sys
import logging
import webbrowser
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.config import ConfigManager


def setup_logging():
    """配置日志系统"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def main():
    """主函数"""
    logger = setup_logging()
    logger.info("=" * 50)
    logger.info("ScreenTrace Dashboard v2.0 (FastAPI)")
    logger.info("=" * 50)

    try:
        # 加载配置
        config_manager = ConfigManager()
        config_manager.load()

        # 获取配置
        port = config_manager.get("dashboard.port", 8080)
        auto_open = config_manager.get("dashboard.auto_open_browser", False)

        # 自动打开浏览器
        if auto_open:
            webbrowser.open(f"http://localhost:{port}")

        # 运行 FastAPI 应用
        logger.info(f"\nDashboard 已启动: http://localhost:{port}")
        logger.info(f"API 文档: http://localhost:{port}/docs")
        logger.info("按 Ctrl+C 停止服务器\n")

        import uvicorn
        from src.dashboard.fastapi_app import app

        uvicorn.run(
            app,
            host="localhost",
            port=port,
            log_level="info"
        )

    except KeyboardInterrupt:
        logger.info("\n用户中断，正在关闭...")
    except ImportError as e:
        logger.error(f"缺少依赖: {e}")
        logger.info("请运行: pip install fastapi uvicorn jinja2")
        sys.exit(1)
    except Exception as e:
        logger.error(f"启动失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
