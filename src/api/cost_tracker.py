"""
成本控制模块
负责Token计数、API调用统计和成本追踪
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class CostTracker:
    """成本追踪器"""

    # 各API提供商的价格（美元/1000 tokens）
    # 这些是参考价格，实际价格以官方为准
    PRICING = {
        "openai": {
            "gpt-4-vision-preview": {"input": 0.01, "output": 0.03},
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        },
        "claude": {
            "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
        },
        "gemini": {
            "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
            "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
            "gemini-pro-vision": {"input": 0.00025, "output": 0.0005},
        },
        "custom": {
            # 自定义服务默认价格
            "default": {"input": 0.0, "output": 0.0}
        }
    }

    def __init__(self, db_manager=None):
        """
        初始化成本追踪器

        Args:
            db_manager: 数据库管理器
        """
        self.db_manager = db_manager
        self.stats = {
            'total_calls': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'failed_calls': 0,
            'today_calls': 0,
            'today_cost': 0.0
        }

    def estimate_tokens(self, text: str, image_size: tuple = None) -> int:
        """
        估算token数量

        Args:
            text: 文本内容
            image_size: 图像尺寸 (width, height)

        Returns:
            估算的token数量
        """
        # 文本token估算（粗略：英文约4字符=1token，中文约1.5字符=1token）
        text_tokens = len(text) // 4

        # 图像token估算（根据OpenAI的计费方式）
        # 512x512图像约255 tokens
        # 更大图像会缩放到这个尺寸计算
        image_tokens = 0
        if image_size:
            width, height = image_size
            # 缩放比例
            scale = min(512 / width, 512 / height)
            scaled_width = int(width * scale)
            scaled_height = int(height * scale)

            # 按tiles计算（每个tile约85 tokens）
            tiles = (scaled_width // 512 + 1) * (scaled_height // 512 + 1)
            image_tokens = tiles * 85

        return text_tokens + image_tokens

    def calculate_cost(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        计算API调用成本

        Args:
            provider: API提供商
            model: 模型名称
            input_tokens: 输入token数
            output_tokens: 输出token数

        Returns:
            成本（美元）
        """
        try:
            # 获取价格表
            provider_pricing = self.PRICING.get(provider, self.PRICING["custom"])
            model_pricing = provider_pricing.get(model, provider_pricing.get("default", {"input": 0, "output": 0}))

            # 计算成本
            input_cost = (input_tokens / 1000) * model_pricing["input"]
            output_cost = (output_tokens / 1000) * model_pricing["output"]

            total_cost = input_cost + output_cost

            logger.debug(
                f"成本计算: {input_tokens}+{output_tokens} tokens = ${total_cost:.6f}"
            )

            return total_cost

        except Exception as e:
            logger.error(f"计算成本失败: {e}")
            return 0.0

    def record_api_call(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        success: bool,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        记录API调用

        Args:
            provider: API提供商
            model: 模型名称
            input_tokens: 输入token数
            output_tokens: 输出token数
            success: 是否成功
            error_message: 错误信息

        Returns:
            调用统计信息
        """
        # 计算成本
        cost = self.calculate_cost(provider, model, input_tokens, output_tokens) if success else 0.0

        # 更新统计
        self.stats['total_calls'] += 1
        if success:
            self.stats['total_tokens'] += input_tokens + output_tokens
            self.stats['total_cost'] += cost
        else:
            self.stats['failed_calls'] += 1

        # 更新今日统计
        self.stats['today_calls'] += 1
        self.stats['today_cost'] += cost

        # 保存到数据库
        if self.db_manager:
            try:
                self.db_manager.insert_api_log(
                    provider=provider,
                    model=model,
                    tokens_used=input_tokens + output_tokens,
                    cost=cost,
                    success=success,
                    error_message=error_message
                )
            except Exception as e:
                logger.error(f"保存API日志失败: {e}")

        return {
            'tokens': input_tokens + output_tokens,
            'cost': cost,
            'success': success
        }

    def get_stats(self, reset_daily: bool = True) -> Dict[str, Any]:
        """
        获取统计信息

        Args:
            reset_daily: 是否重置今日统计（如果跨天）

        Returns:
            统计数据字典
        """
        stats = self.stats.copy()

        # 计算成功率
        if stats['total_calls'] > 0:
            stats['success_rate'] = (
                (stats['total_calls'] - stats['failed_calls']) /
                stats['total_calls'] * 100
            )
        else:
            stats['success_rate'] = 0.0

        # 转换为更友好的单位
        stats['total_cost_cny'] = stats['total_cost'] * 7.2  # 假设汇率
        stats['today_cost_cny'] = stats['today_cost'] * 7.2

        return stats

    def get_monthly_report(self) -> Dict[str, Any]:
        """
        获取月度报告

        Returns:
            月度统计数据
        """
        if not self.db_manager:
            return {}

        try:
            # 查询本月数据
            start_of_month = datetime.now().replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )

            cursor = self.db_manager.connection.cursor()

            # 本月总调用次数
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM api_logs
                WHERE timestamp >= ?
            """, (start_of_month.isoformat(),))
            total_calls = cursor.fetchone()['count']

            # 本月总成本
            cursor.execute("""
                SELECT SUM(cost) as total_cost
                FROM api_logs
                WHERE timestamp >= ? AND success = 1
            """, (start_of_month.isoformat(),))
            total_cost = cursor.fetchone()['total_cost'] or 0.0

            # 本月总tokens
            cursor.execute("""
                SELECT SUM(tokens_used) as total_tokens
                FROM api_logs
                WHERE timestamp >= ? AND success = 1
            """, (start_of_month.isoformat(),))
            total_tokens = cursor.fetchone()['total_tokens'] or 0

            # 按提供商统计
            cursor.execute("""
                SELECT provider, COUNT(*) as count, SUM(cost) as cost
                FROM api_logs
                WHERE timestamp >= ?
                GROUP BY provider
                ORDER BY count DESC
            """, (start_of_month.isoformat(),))
            by_provider = {row['provider']: {
                'calls': row['count'],
                'cost': row['cost'] or 0.0
            } for row in cursor.fetchall()}

            return {
                'month': start_of_month.strftime('%Y-%m'),
                'total_calls': total_calls,
                'total_cost_usd': total_cost,
                'total_cost_cny': total_cost * 7.2,
                'total_tokens': total_tokens,
                'by_provider': by_provider,
                'avg_cost_per_call': total_cost / total_calls if total_calls > 0 else 0
            }

        except Exception as e:
            logger.error(f"生成月度报告失败: {e}")
            return {}

    def check_budget_limit(
        self,
        daily_limit: float = 1.0,
        monthly_limit: float = 30.0
    ) -> Dict[str, bool]:
        """
        检查预算限制

        Args:
            daily_limit: 每日预算限制（美元）
            monthly_limit: 每月预算限制（美元）

        Returns:
            {"daily_exceeded": bool, "monthly_exceeded": bool}
        """
        # 获取今日成本
        today_cost = self.stats.get('today_cost', 0.0)

        # 获取本月成本
        monthly_report = self.get_monthly_report()
        monthly_cost = monthly_report.get('total_cost_usd', 0.0)

        return {
            'daily_exceeded': today_cost >= daily_limit,
            'monthly_exceeded': monthly_cost >= monthly_limit,
            'today_cost': today_cost,
            'monthly_cost': monthly_cost,
            'daily_limit': daily_limit,
            'monthly_limit': monthly_limit
        }

    def export_report(self, output_path: str) -> bool:
        """
        导出成本报告

        Args:
            output_path: 输出文件路径

        Returns:
            是否成功
        """
        try:
            report = {
                'generated_at': datetime.now().isoformat(),
                'stats': self.get_stats(),
                'monthly_report': self.get_monthly_report()
            }

            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            logger.info(f"成本报告已导出: {output_path}")
            return True

        except Exception as e:
            logger.error(f"导出成本报告失败: {e}")
            return False
