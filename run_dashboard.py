"""
启动Web统计面板
独立运行的Web服务器
"""

import sys
import logging
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.config import ConfigManager
from src.storage.database import DatabaseManager
from src.api.client import APIClient
from src.dashboard.app import DashboardApp


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
    logger.info("ScreenTrace Web面板启动")
    logger.info("=" * 50)

    try:
        # 加载配置
        config_manager = ConfigManager()
        config_manager.load()

        # 初始化数据库
        db_path = config_manager.get("storage.database_path", "./data/screenTrace.db")
        db_manager = DatabaseManager(db_path)
        db_manager.initialize()
        logger.info("数据库初始化成功")

        # 初始化API客户端（可选）
        api_config = config_manager.config.get("api", {})
        api_client = APIClient(api_config) if api_config.get("api_key") else None

        # 创建Web应用
        dashboard = DashboardApp(db_manager, api_client)

        # 获取配置
        port = config_manager.get("dashboard.port", 8080)
        auto_open = config_manager.get("dashboard.auto_open_browser", False)

        # 自动打开浏览器
        if auto_open:
            import webbrowser
            webbrowser.open(f"http://localhost:{port}")

        # 运行Web服务器
        logger.info(f"\nWeb面板已启动: http://localhost:{port}")
        logger.info("按 Ctrl+C 停止服务器\n")

        dashboard.run(host='localhost', port=port, debug=False)

    except KeyboardInterrupt:
        logger.info("\n用户中断，正在关闭...")
    except Exception as e:
        logger.error(f"启动失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
