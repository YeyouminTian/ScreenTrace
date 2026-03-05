"""
ScreenTrace 主入口
"""

import sys
import signal
import time
import logging
from pathlib import Path
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.config import ConfigManager, ConfigWizard
from src.storage.database import DatabaseManager
from src.core.screenshot import ScreenshotCapture
from src.core.window_listener import WindowListener, WindowBlacklistChecker
from src.core.deduplication import DeduplicationChecker
from src.core.monitor import MonitorScheduler
from src.api.client import APIClient
from src.api.prompts import PromptBuilder
from src.api.cost_tracker import CostTracker

# 配置日志
def setup_logging():
    """配置日志系统"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/screentrace.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger(__name__)


def main():
    """主函数"""
    logger = setup_logging()
    logger.info("=" * 50)
    logger.info("ScreenTrace 启动")
    logger.info("=" * 50)

    # 全局变量
    db_manager = None
    scheduler = None

    try:
        # 1. 加载配置
        config_manager = ConfigManager()
        config_path = Path("config/settings.json")

        if not config_path.exists():
            logger.info("首次运行，启动配置向导")
            wizard = ConfigWizard(config_manager)
            wizard.run()
        else:
            config_manager.load()

        # 2. 验证配置
        if not config_manager.validate():
            logger.error("配置验证失败，请检查配置文件")
            sys.exit(1)

        # 3. 初始化数据库
        db_path = config_manager.get("storage.database_path", "./data/screenTrace.db")
        db_manager = DatabaseManager(db_path)
        db_manager.initialize()
        logger.info("数据库初始化成功")

        # 4. 初始化核心组件
        logger.info("初始化核心组件...")

        # 4.1 截图采集器
        screenshot_capture = ScreenshotCapture(
            screenshot_dir=config_manager.get("storage.screenshot_path", "./data/screenshots"),
            image_quality=config_manager.get("screenshot.image_quality", 85),
            max_resolution=tuple(config_manager.get("screenshot.max_resolution", [1920, 1080]))
        )
        logger.info("截图采集器初始化完成")

        # 4.2 窗口监听器
        window_listener = WindowListener()
        logger.info("窗口监听器初始化完成")

        # 4.3 黑名单检查器
        blacklist_checker = WindowBlacklistChecker(
            blacklist_apps=config_manager.get("privacy.blacklist_apps", []),
            blacklist_title_keywords=config_manager.get("privacy.blacklist_title_keywords", [])
        )
        logger.info("黑名单检查器初始化完成")

        # 4.4 去重检查器
        dedup_checker = DeduplicationChecker(
            similarity_threshold=config_manager.get("screenshot.similarity_threshold", 0.85),
            skip_if_last_within_minutes=config_manager.get("screenshot.skip_if_last_within_minutes", 2)
        )
        logger.info("去重检查器初始化完成")

        # 4.5 API客户端
        api_config = config_manager.config.get("api", {})
        api_client = APIClient(api_config)
        logger.info(f"API客户端初始化完成 (提供商: {api_config.get('provider', 'unknown')})")

        # 4.6 Prompt构建器
        prompt_builder = PromptBuilder(use_context=True)
        logger.info("Prompt构建器初始化完成")

        # 4.7 成本追踪器
        cost_tracker = CostTracker(db_manager=db_manager)
        logger.info("成本追踪器初始化完成")

        # 4.8 监控调度器
        scheduler = MonitorScheduler(
            screenshot_capture=screenshot_capture,
            window_listener=window_listener,
            dedup_checker=dedup_checker,
            blacklist_checker=blacklist_checker,
            interval_minutes=config_manager.get("screenshot.interval_minutes", 10)
        )

        # 设置截图回调
        def on_screenshot_taken(screenshot_path, timestamp, window, trigger_type):
            """截图完成回调 - 调用API分析截图"""
            try:
                # 构建Prompt
                prompt = prompt_builder.build_analysis_prompt()

                # 调用API分析截图
                logger.info(f"正在分析截图: {screenshot_path}")
                analysis_result = api_client.analyze_image(screenshot_path, prompt)

                if analysis_result:
                    # 提取分析结果
                    app_name = analysis_result.get('app', window.process_name if window else '')
                    life_category = analysis_result.get('life_category', '')
                    activity_form = analysis_result.get('activity_form', '')
                    description = analysis_result.get('description', '')
                    keywords = analysis_result.get('keywords', [])

                    # 保存到数据库
                    db_manager.insert_screenshot(
                        timestamp=timestamp,
                        screenshot_path=screenshot_path,
                        app_name=app_name,
                        window_title=window.title if window else None,
                        life_category=life_category,
                        activity_form=activity_form,
                        description=description,
                        keywords=keywords,
                        api_called=True
                    )

                    # 记录成本（估算）
                    # 注意：这里使用估算值，实际应从API响应中获取
                    input_tokens = cost_tracker.estimate_tokens(prompt)
                    output_tokens = cost_tracker.estimate_tokens(str(analysis_result))

                    cost_tracker.record_api_call(
                        provider=api_config.get('provider', 'custom'),
                        model=api_config.get('model', ''),
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        success=True
                    )

                    logger.info(
                        f"截图分析完成: {description} "
                        f"[{life_category}/{activity_form}]"
                    )
                else:
                    # API调用失败，仍保存基础信息
                    db_manager.insert_screenshot(
                        timestamp=timestamp,
                        screenshot_path=screenshot_path,
                        app_name=window.process_name if window else None,
                        window_title=window.title if window else None,
                        api_called=False
                    )

                    cost_tracker.record_api_call(
                        provider=api_config.get('provider', 'custom'),
                        model=api_config.get('model', ''),
                        input_tokens=0,
                        output_tokens=0,
                        success=False,
                        error_message="API分析失败"
                    )

                    logger.warning("API分析失败，仅保存基础信息")

            except Exception as e:
                logger.error(f"处理截图失败: {e}", exc_info=True)
                # 记录失败
                cost_tracker.record_api_call(
                    provider=api_config.get('provider', 'custom'),
                    model=api_config.get('model', ''),
                    input_tokens=0,
                    output_tokens=0,
                    success=False,
                    error_message=str(e)
                )

        scheduler.on_screenshot_taken = on_screenshot_taken

        # 5. 注册信号处理（优雅退出）
        def signal_handler(signum, frame):
            logger.info("接收到退出信号，正在关闭...")
            if scheduler:
                scheduler.stop()
            if db_manager:
                db_manager.close()
            logger.info("ScreenTrace 已退出")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # 6. 启动监控
        scheduler.start()
        logger.info("=" * 50)
        logger.info("ScreenTrace 运行中...")
        logger.info(f"截图间隔: {config_manager.get('screenshot.interval_minutes')} 分钟")
        logger.info(f"相似度阈值: {config_manager.get('screenshot.similarity_threshold')}")
        logger.info("按 Ctrl+C 退出")
        logger.info("=" * 50)

        # 7. 主循环
        while scheduler.is_running():
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("用户中断")
    except Exception as e:
        logger.error(f"启动失败: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # 清理资源
        if scheduler:
            scheduler.stop()
        if db_manager:
            db_manager.close()
        logger.info("ScreenTrace 已关闭")


if __name__ == "__main__":
    main()
