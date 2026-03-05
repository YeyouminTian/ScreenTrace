"""
监控调度器
负责协调截图触发时机，整合所有核心组件
"""

import threading
import time
from datetime import datetime
from typing import Optional, Callable
import logging

from .screenshot import ScreenshotCapture
from .window_listener import WindowListener, WindowBlacklistChecker, WindowInfo
from .deduplication import DeduplicationChecker

logger = logging.getLogger(__name__)


class MonitorScheduler:
    """监控调度器"""

    def __init__(
        self,
        screenshot_capture: ScreenshotCapture,
        window_listener: WindowListener,
        dedup_checker: DeduplicationChecker,
        blacklist_checker: WindowBlacklistChecker,
        interval_minutes: int = 10
    ):
        """
        初始化监控调度器

        Args:
            screenshot_capture: 截图采集器
            window_listener: 窗口监听器
            dedup_checker: 去重检查器
            blacklist_checker: 黑名单检查器
            interval_minutes: 定时截图间隔（分钟）
        """
        self.screenshot_capture = screenshot_capture
        self.window_listener = window_listener
        self.dedup_checker = dedup_checker
        self.blacklist_checker = blacklist_checker
        self.interval_minutes = interval_minutes

        # 回调函数
        self.on_screenshot_taken: Optional[Callable] = None

        # 状态
        self._running = False
        self._timer_thread: Optional[threading.Thread] = None
        self._pause_event = threading.Event()

        # 统计信息
        self.stats = {
            'total_screenshots': 0,
            'skipped_by_blacklist': 0,
            'skipped_by_dedup': 0,
            'start_time': None
        }

    def start(self) -> None:
        """启动监控"""
        if self._running:
            logger.warning("监控调度器已在运行")
            return

        self._running = True
        self.stats['start_time'] = datetime.now()

        # 启动窗口监听器
        self.window_listener.set_callback(self._on_window_change)
        self.window_listener.start_polling(interval=0.5)

        # 启动定时器线程
        self._timer_thread = threading.Thread(
            target=self._timer_loop,
            daemon=True
        )
        self._timer_thread.start()

        logger.info(
            f"监控调度器启动 - 定时间隔: {self.interval_minutes}分钟, "
            f"窗口切换: 启用"
        )

    def stop(self) -> None:
        """停止监控"""
        if not self._running:
            return

        self._running = False
        self._pause_event.set()

        # 停止窗口监听器
        self.window_listener.stop()

        # 等待定时器线程结束
        if self._timer_thread:
            self._timer_thread.join(timeout=2)

        logger.info("监控调度器已停止")

    def pause(self) -> None:
        """暂停监控"""
        self._pause_event.set()
        logger.info("监控已暂停")

    def resume(self) -> None:
        """恢复监控"""
        self._pause_event.clear()
        logger.info("监控已恢复")

    def _timer_loop(self) -> None:
        """定时器循环"""
        while self._running:
            try:
                # 等待指定时间
                for _ in range(self.interval_minutes * 60):
                    if not self._running:
                        return
                    time.sleep(1)

                # 检查是否暂停
                if self._pause_event.is_set():
                    continue

                # 触发定时截图
                self._trigger_screenshot("timer")

            except Exception as e:
                logger.error(f"定时器循环错误: {e}")
                time.sleep(1)

    def _on_window_change(self, window: WindowInfo) -> None:
        """
        窗口切换回调

        Args:
            window: 新窗口信息
        """
        if self._pause_event.is_set():
            return

        # 延迟一小段时间，让窗口完全切换
        time.sleep(0.3)

        # 触发窗口切换截图
        self._trigger_screenshot("window_change", window)

    def _trigger_screenshot(
        self,
        trigger_type: str,
        window: Optional[WindowInfo] = None
    ) -> None:
        """
        触发截图

        Args:
            trigger_type: 触发类型（timer/window_change）
            window: 窗口信息（可选）
        """
        try:
            current_time = datetime.now()

            # 获取当前窗口信息（如果未提供）
            if not window:
                window = self.window_listener.get_active_window()

            if not window:
                logger.warning("无法获取窗口信息，跳过截图")
                return

            # 检查黑名单
            if self.blacklist_checker.is_blacklisted(window):
                self.stats['skipped_by_blacklist'] += 1
                logger.info(
                    f"窗口在黑名单中，跳过截图: {window.title}"
                )
                return

            # 先截图（后续根据去重决定是否保存）
            screenshot_path, actual_time = self.screenshot_capture.capture(
                current_time
            )

            # 检查去重（窗口切换时不检查时间间隔）
            check_time_interval = (trigger_type == "timer")
            should_skip, reason = self.dedup_checker.should_skip(
                current_time,
                screenshot_path,
                check_time_interval=check_time_interval
            )

            if should_skip:
                self.stats['skipped_by_dedup'] += 1
                logger.info(f"去重检查: {reason}")

                # 删除重复截图
                self.screenshot_capture.delete_screenshot(screenshot_path)
                return

            # 更新去重缓存
            self.dedup_checker.update_last_screenshot(
                actual_time,
                screenshot_path
            )

            # 更新统计
            self.stats['total_screenshots'] += 1

            # 触发回调
            if self.on_screenshot_taken:
                try:
                    self.on_screenshot_taken(
                        screenshot_path=screenshot_path,
                        timestamp=actual_time,
                        window=window,
                        trigger_type=trigger_type
                    )
                except Exception as e:
                    logger.error(f"截图回调执行失败: {e}")

            logger.info(
                f"截图成功 [{trigger_type}]: {window.title} "
                f"({window.process_name}) - {screenshot_path}"
            )

        except Exception as e:
            logger.error(f"触发截图失败: {e}", exc_info=True)

    def force_screenshot(self) -> Optional[str]:
        """
        强制截图（忽略去重和黑名单）

        Returns:
            截图路径，失败返回None
        """
        try:
            current_time = datetime.now()
            screenshot_path, actual_time = self.screenshot_capture.capture(
                current_time
            )

            window = self.window_listener.get_active_window()

            logger.info(f"强制截图成功: {screenshot_path}")

            # 触发回调
            if self.on_screenshot_taken and window:
                self.on_screenshot_taken(
                    screenshot_path=screenshot_path,
                    timestamp=actual_time,
                    window=window,
                    trigger_type="manual"
                )

            return screenshot_path

        except Exception as e:
            logger.error(f"强制截图失败: {e}")
            return None

    def get_stats(self) -> dict:
        """
        获取统计信息

        Returns:
            统计数据字典
        """
        uptime = None
        if self.stats['start_time']:
            uptime = (
                datetime.now() - self.stats['start_time']
            ).total_seconds()

        return {
            **self.stats,
            'uptime_seconds': uptime,
            'is_running': self._running,
            'is_paused': self._pause_event.is_set()
        }

    def is_running(self) -> bool:
        """检查是否在运行"""
        return self._running

    def is_paused(self) -> bool:
        """检查是否暂停"""
        return self._pause_event.is_set()
