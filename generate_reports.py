"""
生成报告脚本
生成时间线、统计和叙述式报告
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.config import ConfigManager
from src.storage.database import DatabaseManager
from src.api.client import APIClient
from src.report.timeline import TimelineGenerator
from src.report.statistics import StatisticsAnalyzer
from src.report.narrative import NarrativeGenerator


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='ScreenTrace 报告生成工具')
    parser.add_argument('--type', choices=['timeline', 'stats', 'narrative', 'all'],
                       default='all', help='报告类型')
    parser.add_argument('--days', type=int, default=7, help='统计天数')
    parser.add_argument('--output', type=str, default='./reports', help='输出目录')
    parser.add_argument('--ai', action='store_true', help='使用AI生成叙述式报告')

    args = parser.parse_args()

    print("\n" + "=" * 50)
    print("ScreenTrace 报告生成器")
    print("=" * 50 + "\n")

    try:
        # 加载配置
        config_manager = ConfigManager()
        config_manager.load()

        # 初始化数据库
        db_path = config_manager.get("storage.database_path", "./data/screenTrace.db")
        db_manager = DatabaseManager(db_path)
        db_manager.initialize()
        print("✅ 数据库连接成功")

        # 初始化API客户端（可选）
        api_config = config_manager.config.get("api", {})
        api_client = APIClient(api_config) if args.ai and api_config.get("api_key") else None

        # 计算时间范围
        end_time = datetime.now()
        start_time = end_time - timedelta(days=args.days)

        # 创建输出目录
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 生成报告
        if args.type in ['timeline', 'all']:
            print(f"\n📝 生成时间线报告（最近{args.days}天）...")
            generator = TimelineGenerator(db_manager)
            report = generator.generate_timeline(start_time, end_time)
            output_file = output_dir / f"timeline_{timestamp}.md"
            generator.export_to_file(report, str(output_file))
            print(f"✅ 时间线报告已保存: {output_file}")

        if args.type in ['stats', 'all']:
            print(f"\n📊 生成统计分析报告（最近{args.days}天）...")
            analyzer = StatisticsAnalyzer(db_manager)
            report = analyzer.generate_summary_report(start_time, end_time)
            output_file = output_dir / f"statistics_{timestamp}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ 统计报告已保存: {output_file}")

        if args.type in ['narrative', 'all']:
            print(f"\n📄 生成叙述式报告（最近{args.days}天）...")
            generator = NarrativeGenerator(db_manager, api_client)
            report = generator.generate_narrative_report(
                start_time,
                end_time,
                use_ai=args.ai
            )
            output_file = output_dir / f"narrative_{timestamp}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ 叙述式报告已保存: {output_file}")

        print("\n" + "=" * 50)
        print("✅ 报告生成完成！")
        print(f"输出目录: {output_dir.absolute()}")
        print("=" * 50 + "\n")

    except Exception as e:
        print(f"\n❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
