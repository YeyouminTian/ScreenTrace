"""
实时查看最近的截图分析结果
每5秒自动刷新显示最新的10条记录
"""

import sys
import time
import os
from pathlib import Path
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.storage.database import DatabaseManager


def clear_screen():
    """清屏"""
    os.system('cls' if os.name == 'nt' else 'clear')


def display_recent_screenshots(db_manager, limit=10):
    """显示最近的截图记录"""
    screenshots = db_manager.get_screenshots(limit=limit)

    if not screenshots:
        print("\n⚠️  暂无数据\n")
        return

    print("\n" + "=" * 100)
    print(f"📊 ScreenTrace 实时监控 - 最近 {len(screenshots)} 条记录")
    print("=" * 100)
    print(f"{'时间':<20} {'应用':<20} {'维度':<8} {'形式':<12} {'描述':<40}")
    print("-" * 100)

    for record in screenshots:
        timestamp = record['timestamp'][:19]
        app = (record['app_name'] or 'N/A')[:20]
        category = record['life_category'] or 'N/A'
        form = (record['activity_form'] or 'N/A')[:12]
        desc = (record['description'] or 'N/A')[:40]

        # 根据维度添加图标
        icon = {
            '工作': '💼',
            '学习': '📚',
            '休闲': '🎮',
            '生活': '🏠'
        }.get(category, '📌')

        print(f"{timestamp:<20} {app:<20} {icon}{category:<7} {form:<12} {desc:<40}")

    print("=" * 100)
    print(f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    """主函数"""
    print("\n🚀 ScreenTrace 实时查看器")
    print("按 Ctrl+C 退出\n")

    # 初始化数据库
    db_path = "./data/screenTrace.db"
    if not Path(db_path).exists():
        print("❌ 数据库文件不存在，请先启动监控程序: python main.py")
        return

    db_manager = DatabaseManager(db_path)
    db_manager.initialize()

    try:
        while True:
            clear_screen()
            display_recent_screenshots(db_manager, limit=10)
            print("\n⏳ 5秒后自动刷新... (Ctrl+C 退出)")
            time.sleep(5)

    except KeyboardInterrupt:
        print("\n\n👋 退出实时查看")
    finally:
        db_manager.close()


if __name__ == "__main__":
    main()
