"""
智能去重模块
负责检测图像相似度和时间间隔判断
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
import imagehash
import logging

logger = logging.getLogger(__name__)


class DeduplicationChecker:
    """去重检查器"""

    def __init__(
        self,
        similarity_threshold: float = 0.85,
        skip_if_last_within_minutes: int = 2
    ):
        """
        初始化去重检查器

        Args:
            similarity_threshold: 相似度阈值 (0-1)
            skip_if_last_within_minutes: 距离上次截图的时间阈值（分钟）
        """
        self.similarity_threshold = similarity_threshold
        self.skip_threshold = timedelta(minutes=skip_if_last_within_minutes)

        # 缓存上一次的信息
        self.last_screenshot_time: Optional[datetime] = None
        self.last_screenshot_path: Optional[str] = None
        self.last_screenshot_hash: Optional[imagehash.ImageHash] = None

    def should_skip(
        self,
        current_time: datetime,
        current_screenshot_path: Optional[str] = None,
        check_time_interval: bool = True
    ) -> Tuple[bool, str]:
        """
        判断是否应该跳过当前截图

        Args:
            current_time: 当前时间
            current_screenshot_path: 当前截图路径（如果已截图）
            check_time_interval: 是否检查时间间隔（窗口切换时为False）

        Returns:
            (是否跳过, 原因说明)
        """
        # 如果是第一次截图，不跳过
        if not self.last_screenshot_time:
            return False, ""

        # 检查时间间隔（仅定时截图时检查）
        if check_time_interval:
            time_diff = current_time - self.last_screenshot_time
            if time_diff < self.skip_threshold:
                reason = f"距离上次截图仅 {time_diff.total_seconds():.1f} 秒，跳过"
                logger.debug(reason)
                return True, reason

        # 如果提供了当前截图，检查相似度
        if current_screenshot_path and self.last_screenshot_path:
            similarity = self._calculate_similarity(
                current_screenshot_path,
                self.last_screenshot_path
            )

            if similarity > self.similarity_threshold:
                reason = f"图像相似度 {similarity:.2%} 超过阈值，跳过"
                logger.debug(reason)
                return True, reason

        return False, ""

    def _calculate_similarity(
        self,
        image_path1: str,
        image_path2: str
    ) -> float:
        """
        计算两张图片的相似度

        Args:
            image_path1: 图片1路径
            image_path2: 图片2路径

        Returns:
            相似度 (0-1)
        """
        try:
            # 计算图片哈希
            hash1 = self._get_image_hash(image_path1)
            hash2 = self._get_image_hash(image_path2)

            if not hash1 or not hash2:
                return 0.0

            # 计算汉明距离并转换为相似度
            distance = hash1 - hash2
            max_distance = len(hash1.hash) ** 2  # 最大可能距离
            similarity = 1 - (distance / max_distance)

            logger.debug(
                f"图像相似度: {similarity:.2%} "
                f"(距离: {distance}/{max_distance})"
            )

            return similarity

        except Exception as e:
            logger.error(f"计算图像相似度失败: {e}")
            return 0.0

    def _get_image_hash(
        self,
        image_path: str,
        use_cache: bool = True
    ) -> Optional[imagehash.ImageHash]:
        """
        获取图像的感知哈希

        Args:
            image_path: 图像路径
            use_cache: 是否使用缓存

        Returns:
            图像哈希对象
        """
        # 检查缓存
        if use_cache and self.last_screenshot_path == image_path:
            return self.last_screenshot_hash

        try:
            # 使用phash算法（感知哈希）
            image = Image.open(image_path)
            img_hash = imagehash.phash(image)

            # 更新缓存
            if use_cache:
                self.last_screenshot_path = image_path
                self.last_screenshot_hash = img_hash

            return img_hash

        except Exception as e:
            logger.error(f"计算图像哈希失败: {e}")
            return None

    def update_last_screenshot(
        self,
        screenshot_time: datetime,
        screenshot_path: str
    ) -> None:
        """
        更新上一次截图信息

        Args:
            screenshot_time: 截图时间
            screenshot_path: 截图路径
        """
        self.last_screenshot_time = screenshot_time
        self.last_screenshot_path = screenshot_path

        # 预计算哈希
        self._get_image_hash(screenshot_path, use_cache=False)

        logger.debug(
            f"更新上次截图信息: {screenshot_time.strftime('%H:%M:%S')}"
        )

    def reset(self) -> None:
        """重置缓存"""
        self.last_screenshot_time = None
        self.last_screenshot_path = None
        self.last_screenshot_hash = None
        logger.debug("去重缓存已重置")

    def get_stats(self) -> dict:
        """
        获取统计信息

        Returns:
            统计数据字典
        """
        return {
            'last_screenshot_time': (
                self.last_screenshot_time.isoformat()
                if self.last_screenshot_time else None
            ),
            'last_screenshot_path': self.last_screenshot_path,
            'similarity_threshold': self.similarity_threshold,
            'skip_threshold_seconds': self.skip_threshold.total_seconds()
        }


class QuickSimilarityChecker:
    """快速相似度检查器（用于实时判断）"""

    def __init__(self, hash_size: int = 16):
        """
        初始化快速相似度检查器

        Args:
            hash_size: 哈希大小，越大越精确但越慢
        """
        self.hash_size = hash_size
        self.last_hash: Optional[imagehash.ImageHash] = None

    def is_similar(
        self,
        image: Image.Image,
        threshold: float = 0.85
    ) -> bool:
        """
        快速判断图像是否与上一张相似

        Args:
            image: PIL图像对象
            threshold: 相似度阈值

        Returns:
            是否相似
        """
        try:
            # 计算当前图像哈希
            current_hash = imagehash.phash(image, hash_size=self.hash_size)

            # 如果没有上一张图像的哈希，不相似
            if not self.last_hash:
                self.last_hash = current_hash
                return False

            # 计算相似度
            distance = current_hash - self.last_hash
            max_distance = self.hash_size ** 2
            similarity = 1 - (distance / max_distance)

            # 更新哈希
            self.last_hash = current_hash

            return similarity > threshold

        except Exception as e:
            logger.error(f"快速相似度检查失败: {e}")
            return False

    def reset(self) -> None:
        """重置缓存"""
        self.last_hash = None
