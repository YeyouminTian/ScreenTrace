"""
窗口监听器
负责检测窗口切换、获取窗口信息
"""

import win32gui
import win32process
import psutil
from typing import Optional, Callable, Dict
import threading
import time
import logging

logger = logging.getLogger(__name__)


class WindowInfo:
    """窗口信息"""

    def __init__(
        self,
        hwnd: int,
        title: str,
        process_name: str,
        process_id: int
    ):
        self.hwnd = hwnd
        self.title = title
        self.process_name = process_name
        self.process_id = process_id

    def __repr__(self):
        return f"WindowInfo(title='{self.title}', process='{self.process_name}')"

    def to_dict(self) -> Dict[str, any]:
        """转换为字典"""
        return {
            'hwnd': self.hwnd,
            'title': self.title,
            'process_name': self.process_name,
            'process_id': self.process_id
        }


class WindowListener:
    """窗口监听器"""

    def __init__(self):
        self.current_window: Optional[WindowInfo] = None
        self.on_window_change: Optional[Callable[[WindowInfo], None]] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def get_active_window(self) -> Optional[WindowInfo]:
        """
        获取当前活动窗口信息

        Returns:
            WindowInfo 对象，如果获取失败返回 None
        """
        try:
            # 获取活动窗口句柄
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None

            # 获取窗口标题
            title = win32gui.GetWindowText(hwnd)

            # 获取进程ID
            _, process_id = win32process.GetWindowThreadProcessId(hwnd)

            # 获取进程名
            process_name = self._get_process_name(process_id)

            return WindowInfo(
                hwnd=hwnd,
                title=title,
                process_name=process_name,
                process_id=process_id
            )

        except Exception as e:
            logger.error(f"获取窗口信息失败: {e}")
            return None

    def _get_process_name(self, process_id: int) -> str:
        """
        根据进程ID获取进程名

        Args:
            process_id: 进程ID

        Returns:
            进程名（如 "chrome.exe"）
        """
        try:
            process = psutil.Process(process_id)
            return process.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return "unknown"

    def start_polling(self, interval: float = 1.0) -> None:
        """
        启动轮询监听模式

        Args:
            interval: 轮询间隔（秒）
        """
        if self._running:
            logger.warning("窗口监听器已在运行")
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._poll_window_changes,
            args=(interval,),
            daemon=True
        )
        self._thread.start()
        logger.info(f"窗口监听器启动（轮询模式，间隔{interval}秒）")

    def stop(self) -> None:
        """停止监听"""
        if not self._running:
            return

        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("窗口监听器已停止")

    def _poll_window_changes(self, interval: float) -> None:
        """
        轮询检测窗口变化

        Args:
            interval: 轮询间隔（秒）
        """
        while self._running:
            try:
                window = self.get_active_window()

                # 检查窗口是否变化
                if window and self._is_window_changed(window):
                    # 判断变化类型
                    change_type = self._get_change_type(window)

                    self.current_window = window

                    # 日志输出
                    if change_type == "window":
                        logger.info(f"窗口切换: {window.title} ({window.process_name})")
                    else:  # tab
                        logger.info(f"标签页切换: {window.title} ({window.process_name})")

                    # 触发回调
                    if self.on_window_change:
                        try:
                            self.on_window_change(window)
                        except Exception as e:
                            logger.error(f"窗口切换回调执行失败: {e}")

                time.sleep(interval)

            except Exception as e:
                logger.error(f"轮询窗口变化失败: {e}")
                time.sleep(interval)

    def _get_change_type(self, new_window: WindowInfo) -> str:
        """
        获取变化类型

        Args:
            new_window: 新窗口信息

        Returns:
            "window" 表示窗口切换，"tab" 表示标签页切换
        """
        if not self.current_window:
            return "window"

        # 如果窗口句柄或进程ID变化，则为窗口切换
        if (new_window.hwnd != self.current_window.hwnd or
            new_window.process_id != self.current_window.process_id):
            return "window"

        # 如果只是标题变化，则为标签页切换
        if new_window.title != self.current_window.title:
            return "tab"

        return "window"

    def _is_window_changed(self, new_window: WindowInfo) -> bool:
        """
        判断窗口是否变化（包括窗口切换和标签页切换）

        Args:
            new_window: 新窗口信息

        Returns:
            是否变化
        """
        if not self.current_window:
            return True

        # 比较窗口句柄或进程ID（窗口切换）
        window_changed = (
            new_window.hwnd != self.current_window.hwnd or
            new_window.process_id != self.current_window.process_id
        )

        # 比较窗口标题（标签页切换）
        title_changed = (
            new_window.title != self.current_window.title
        )

        # 窗口切换或标题变化都视为变化
        return window_changed or title_changed

    def set_callback(self, callback: Callable[[WindowInfo], None]) -> None:
        """
        设置窗口切换回调函数

        Args:
            callback: 回调函数，接收 WindowInfo 参数
        """
        self.on_window_change = callback

    def get_current_window(self) -> Optional[WindowInfo]:
        """
        获取当前缓存的窗口信息

        Returns:
            当前窗口信息
        """
        return self.current_window

    def is_running(self) -> bool:
        """检查监听器是否在运行"""
        return self._running


class WindowBlacklistChecker:
    """窗口黑名单检查器"""

    def __init__(
        self,
        blacklist_apps: list = None,
        blacklist_title_keywords: list = None
    ):
        self.blacklist_apps = blacklist_apps or []
        self.blacklist_title_keywords = blacklist_title_keywords or []

    def is_blacklisted(self, window: WindowInfo) -> bool:
        """
        检查窗口是否在黑名单中

        Args:
            window: 窗口信息

        Returns:
            是否在黑名单中
        """
        # 检查应用黑名单
        if window.process_name.lower() in [app.lower() for app in self.blacklist_apps]:
            logger.info(f"窗口在应用黑名单中: {window.process_name}")
            return True

        # 检查标题关键词黑名单
        title_lower = window.title.lower()
        for keyword in self.blacklist_title_keywords:
            if keyword.lower() in title_lower:
                logger.info(f"窗口标题包含黑名单关键词: {keyword}")
                return True

        return False

    def add_app_to_blacklist(self, app_name: str) -> None:
        """添加应用到黑名单"""
        if app_name not in self.blacklist_apps:
            self.blacklist_apps.append(app_name)
            logger.info(f"添加应用到黑名单: {app_name}")

    def add_keyword_to_blacklist(self, keyword: str) -> None:
        """添加关键词到黑名单"""
        if keyword not in self.blacklist_title_keywords:
            self.blacklist_title_keywords.append(keyword)
            logger.info(f"添加关键词到黑名单: {keyword}")

    def remove_app_from_blacklist(self, app_name: str) -> None:
        """从黑名单移除应用"""
        if app_name in self.blacklist_apps:
            self.blacklist_apps.remove(app_name)
            logger.info(f"从黑名单移除应用: {app_name}")

    def remove_keyword_from_blacklist(self, keyword: str) -> None:
        """从黑名单移除关键词"""
        if keyword in self.blacklist_title_keywords:
            self.blacklist_title_keywords.remove(keyword)
            logger.info(f"从黑名单移除关键词: {keyword}")
