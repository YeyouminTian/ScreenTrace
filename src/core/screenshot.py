"""
截图采集器
负责屏幕截图、图像压缩和文件管理
"""

import io
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
import pyautogui
import logging

logger = logging.getLogger(__name__)


class ScreenshotCapture:
    """截图采集器"""

    def __init__(
        self,
        screenshot_dir: str = "./data/screenshots",
        image_quality: int = 85,
        max_resolution: Tuple[int, int] = (1920, 1080)
    ):
        self.screenshot_dir = Path(screenshot_dir)
        self.image_quality = image_quality
        self.max_resolution = max_resolution

        # 确保截图目录存在
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    def capture(self, timestamp: Optional[datetime] = None) -> Tuple[str, datetime]:
        """
        截取当前屏幕

        Args:
            timestamp: 时间戳，用于文件命名

        Returns:
            (截图文件路径, 实际截图时间)
        """
        if timestamp is None:
            timestamp = datetime.now()

        try:
            # 截取全屏
            screenshot = pyautogui.screenshot()

            # 压缩图像
            compressed_image = self._compress_image(screenshot)

            # 生成文件路径
            file_path = self._generate_file_path(timestamp)

            # 保存文件
            compressed_image.save(
                file_path,
                'PNG',
                optimize=True,
                quality=self.image_quality
            )

            logger.info(f"截图成功: {file_path}")
            return str(file_path), timestamp

        except Exception as e:
            logger.error(f"截图失败: {e}")
            raise

    def _compress_image(self, image: Image.Image) -> Image.Image:
        """
        压缩图像到指定分辨率

        Args:
            image: 原始图像

        Returns:
            压缩后的图像
        """
        # 获取原始尺寸
        original_width, original_height = image.size
        max_width, max_height = self.max_resolution

        # 如果已经小于最大分辨率，直接返回
        if original_width <= max_width and original_height <= max_height:
            return image

        # 计算缩放比例
        scale = min(max_width / original_width, max_height / original_height)
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)

        # 缩放图像
        resized_image = image.resize(
            (new_width, new_height),
            Image.Resampling.LANCZOS
        )

        logger.debug(
            f"图像压缩: {original_width}x{original_height} -> "
            f"{new_width}x{new_height}"
        )

        return resized_image

    def _generate_file_path(self, timestamp: datetime) -> Path:
        """
        生成截图文件路径

        格式: screenshots/YYYY-MM-DD/HH-MM-SS.png

        Args:
            timestamp: 时间戳

        Returns:
            文件路径对象
        """
        # 按日期创建子目录
        date_dir = self.screenshot_dir / timestamp.strftime("%Y-%m-%d")
        date_dir.mkdir(exist_ok=True)

        # 生成文件名
        filename = timestamp.strftime("%H-%M-%S.png")
        file_path = date_dir / filename

        return file_path

    def get_image_bytes(self, file_path: str) -> bytes:
        """
        读取截图文件的字节数据

        Args:
            file_path: 截图文件路径

        Returns:
            图像字节数据
        """
        with open(file_path, 'rb') as f:
            return f.read()

    def delete_screenshot(self, file_path: str) -> bool:
        """
        删除截图文件

        Args:
            file_path: 截图文件路径

        Returns:
            是否删除成功
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.debug(f"删除截图: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"删除截图失败: {e}")
            return False

    def get_screenshots_by_date(self, date: str) -> list:
        """
        获取指定日期的所有截图

        Args:
            date: 日期字符串 (YYYY-MM-DD)

        Returns:
            截图文件路径列表
        """
        date_dir = self.screenshot_dir / date
        if not date_dir.exists():
            return []

        screenshots = sorted(date_dir.glob("*.png"))
        return [str(p) for p in screenshots]

    def get_storage_stats(self) -> dict:
        """
        获取存储统计信息

        Returns:
            {
                'total_files': 总文件数,
                'total_size_mb': 总大小(MB),
                'oldest_date': 最早日期,
                'newest_date': 最新日期
            }
        """
        total_files = 0
        total_size = 0
        dates = []

        for date_dir in self.screenshot_dir.iterdir():
            if date_dir.is_dir():
                dates.append(date_dir.name)
                for screenshot in date_dir.glob("*.png"):
                    total_files += 1
                    total_size += screenshot.stat().st_size

        return {
            'total_files': total_files,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'oldest_date': min(dates) if dates else None,
            'newest_date': max(dates) if dates else None
        }
