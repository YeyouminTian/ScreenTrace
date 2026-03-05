"""
修复数据库中未分析的截图记录
对life_category为NULL的记录重新调用API分析
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from src.utils.config import ConfigManager
from src.storage.database import DatabaseManager
from src.api.client import APIClient
from src.api.prompts import PromptBuilder

def main():
    print("\n" + "=" * 60)
    print("修复未分析的截图记录")
    print("=" * 60 + "\n")

    # 加载配置
    config_manager = ConfigManager()
    config_manager.load()

    # 初始化数据库
    db_path = config_manager.get("storage.database_path", "./data/screenTrace.db")
    db_manager = DatabaseManager(db_path)
    db_manager.initialize()

    # 初始化API客户端
    api_config = config_manager.config.get("api", {})
    if not api_config.get("api_key"):
        print("❌ 错误：未配置API密钥")
        return

    api_client = APIClient(api_config)
    prompt_builder = PromptBuilder()

    # 查询未分析的记录
    cursor = db_manager.connection.cursor()
    cursor.execute("""
        SELECT id, timestamp, screenshot_path, app_name, window_title
        FROM screenshots
        WHERE life_category IS NULL
        ORDER BY timestamp DESC
    """)

    records = cursor.fetchall()

    if not records:
        print("No records need fixing")
        db_manager.close()
        return

    print(f"Found {len(records)} records to fix\n")

    # 逐个处理
    success_count = 0
    failed_count = 0

    for i, record in enumerate(records, 1):
        record_id = record['id']
        timestamp = record['timestamp']
        screenshot_path = record['screenshot_path']
        app_name = record['app_name']
        window_title = record['window_title']

        print(f"[{i}/{len(records)}] Processing: {timestamp[:19]} - {app_name}")

        # 检查截图文件是否存在
        if not Path(screenshot_path).exists():
            print(f"  Warning: Screenshot not found, skipping")
            failed_count += 1
            continue

        try:
            # 调用API分析
            prompt = prompt_builder.build_analysis_prompt()
            result = api_client.analyze_image(screenshot_path, prompt)

            if result:
                # 更新数据库
                cursor.execute("""
                    UPDATE screenshots
                    SET app_name = ?, life_category = ?, activity_form = ?,
                        description = ?, keywords = ?, api_called = 1
                    WHERE id = ?
                """, (
                    result.get('app', app_name),
                    result.get('life_category', 'Unknown'),
                    result.get('activity_form', 'Unknown'),
                    result.get('description', ''),
                    str(result.get('keywords', [])),
                    record_id
                ))

                db_manager.connection.commit()
                desc = result.get('description', '')[:40]
                print(f"  OK: {desc}")
                success_count += 1
            else:
                print(f"  ERROR: API analysis failed")
                failed_count += 1

        except Exception as e:
            print(f"  ERROR: {e}")
            failed_count += 1

    db_manager.close()

    print("\n" + "=" * 60)
    print(f"Fix completed")
    print(f"  Success: {success_count}")
    print(f"  Failed: {failed_count}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
