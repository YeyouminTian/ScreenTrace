"""
API连接测试脚本
验证API配置是否正确
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.config import ConfigManager
from src.api.client import APIClient


def main():
    """测试API连接"""
    print("\n" + "=" * 50)
    print("ScreenTrace API连接测试")
    print("=" * 50 + "\n")

    # 加载环境变量
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)
        print("✅ 找到 .env 文件")
    else:
        print("⚠️  未找到 .env 文件")
        print("提示：可以复制 .env.example 为 .env 并填写配置\n")

    # 加载配置
    config_manager = ConfigManager()
    config_manager.load()

    # 显示配置信息
    api_config = config_manager.config.get("api", {})

    print("\n当前API配置：")
    print(f"  提供商: {api_config.get('provider', '未设置')}")
    print(f"  基础URL: {api_config.get('base_url', '未设置')}")
    print(f"  模型: {api_config.get('model', '未设置')}")
    print(f"  兼容模式: {api_config.get('compatibility', '未设置')}")

    # 检查API密钥
    api_key = api_config.get("api_key", "")
    if api_key:
        # 隐藏部分密钥
        masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        print(f"  API密钥: {masked_key}")
    else:
        print("  API密钥: 未设置")
        print("\n❌ 错误：API密钥未设置")
        print("\n请通过以下方式之一设置API密钥：")
        print("  1. 在 .env 文件中设置 SCREENTRACE_API_KEY")
        print("  2. 运行配置向导: python main.py")
        return

    # 创建API客户端
    print("\n正在测试API连接...")
    client = APIClient(api_config)

    # 测试连接
    if client.test_connection():
        print("\n" + "=" * 50)
        print("✅ API连接成功！")
        print("=" * 50)
        print("\nScreenTrace 已准备就绪，可以开始使用。")
    else:
        print("\n" + "=" * 50)
        print("❌ API连接失败")
        print("=" * 50)
        print("\n故障排查建议：")
        print("  1. 检查API密钥是否正确")
        print("  2. 检查API基础URL是否正确")
        print("  3. 检查网络连接")
        print("  4. 检查模型名称是否支持")
        print("  5. 确认兼容模式设置正确")
        print("\n详细配置说明请参考: docs/api-configuration.md")


if __name__ == "__main__":
    main()
