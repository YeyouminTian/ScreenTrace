"""
配置管理模块
负责加载、验证和管理应用配置
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器"""

    DEFAULT_CONFIG = {
        "screenshot": {
            "interval_minutes": 10,
            "similarity_threshold": 0.85,
            "skip_if_last_within_minutes": 2,
            "image_quality": 85,
            "max_resolution": [1920, 1080]
        },
        "privacy": {
            "blacklist_apps": [
                "1Password.exe",
                "Bitwarden.exe",
                "KeePass.exe"
            ],
            "blacklist_title_keywords": [
                "密码", "银行", "支付", "private", "password"
            ],
            "blacklist_content_keywords": [
                "password", "secret", "token", "key"
            ],
            "enable_content_ocr": False
        },
        "api": {
            "provider": "openai",
            "api_key": "",
            "model": "gpt-4-vision-preview",
            "base_url": "https://api.openai.com/v1",
            "max_tokens": 500,
            "timeout_seconds": 30,
            "retry_times": 3
        },
        "storage": {
            "database_path": "./data/screenTrace.db",
            "screenshot_path": "./data/screenshots",
            "retention_days": 90,
            "auto_cleanup": True,
            "cleanup_time": "03:00"
        },
        "report": {
            "default_time_range": "week",
            "output_format": "markdown",
            "include_screenshots": False
        },
        "dashboard": {
            "port": 8080,
            "auto_open_browser": False,
            "theme": "light"
        }
    }

    def __init__(self, config_path: str = "config/settings.json"):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self._encryption_key: Optional[bytes] = None

    def load(self) -> Dict[str, Any]:
        """加载配置文件"""
        # 加载.env文件
        env_path = Path(".env")
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(f"环境变量文件加载成功: {env_path}")

        if not self.config_path.exists():
            logger.info(f"配置文件不存在: {self.config_path}")
            logger.info("使用默认配置")
            self.config = self.DEFAULT_CONFIG.copy()
            # 从环境变量加载API配置
            self._load_api_from_env()
            return self.config

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)

            # 从环境变量加载API配置（优先级更高）
            self._load_api_from_env()

            logger.info(f"配置文件加载成功: {self.config_path}")
            return self.config

        except json.JSONDecodeError as e:
            logger.error(f"配置文件格式错误: {e}")
            raise
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            raise

    def save(self, config: Optional[Dict[str, Any]] = None) -> None:
        """保存配置文件"""
        if config:
            self.config = config

        # 确保配置目录存在
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # 加密敏感字段
        config_to_save = self.config.copy()
        if config_to_save.get("api", {}).get("api_key"):
            config_to_save["api"]["api_key"] = self._encrypt(
                config_to_save["api"]["api_key"]
            )

        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)
            logger.info(f"配置文件保存成功: {self.config_path}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            raise

    def validate(self) -> bool:
        """验证配置有效性"""
        errors = []

        # 检查必需字段
        if not self.config:
            errors.append("配置为空")

        # 验证截图配置
        screenshot = self.config.get("screenshot", {})
        if not (1 <= screenshot.get("interval_minutes", 0) <= 60):
            errors.append("截图间隔必须在1-60分钟之间")

        if not (0 <= screenshot.get("similarity_threshold", 0) <= 1):
            errors.append("相似度阈值必须在0-1之间")

        # 验证API配置
        api = self.config.get("api", {})
        if not api.get("api_key"):
            errors.append("API密钥不能为空")

        # 验证API提供商（可选，因为可以用自定义URL）
        provider = api.get("provider")
        if provider and provider not in ["openai", "claude", "gemini", "custom"]:
            errors.append("不支持的API提供商")

        # 验证API兼容模式
        compatibility = api.get("compatibility", provider or "openai")
        if compatibility not in ["openai", "claude", "gemini"]:
            errors.append("不支持的API兼容模式")

        # 验证存储配置
        storage = self.config.get("storage", {})
        if storage.get("retention_days", 0) < 1:
            errors.append("数据保留天数必须大于0")

        if errors:
            for error in errors:
                logger.error(f"配置验证失败: {error}")
            return False

        logger.info("配置验证通过")
        return True

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值（支持嵌套键）"""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

        return value if value is not None else default

    def set(self, key: str, value: Any) -> None:
        """设置配置值（支持嵌套键）"""
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def _encrypt(self, plaintext: str) -> str:
        """加密敏感数据"""
        if not self._encryption_key:
            self._encryption_key = Fernet.generate_key()

        f = Fernet(self._encryption_key)
        encrypted = f.encrypt(plaintext.encode())
        return f"encrypted:{encrypted.decode()}"

    def _decrypt(self, ciphertext: str) -> str:
        """解密敏感数据"""
        if not ciphertext.startswith("encrypted:"):
            return ciphertext

        if not self._encryption_key:
            raise ValueError("加密密钥未初始化")

        f = Fernet(self._encryption_key)
        encrypted = ciphertext.replace("encrypted:", "")
        decrypted = f.decrypt(encrypted.encode())
        return decrypted.decode()

    def _decrypt_sensitive_fields(self) -> None:
        """解密配置中的敏感字段"""
        if self.config.get("api", {}).get("api_key", "").startswith("encrypted:"):
            try:
                # 如果没有密钥，无法解密，需要重新输入
                if not self._encryption_key:
                    logger.warning("加密密钥未设置，无法解密API密钥")
                    return

                self.config["api"]["api_key"] = self._decrypt(
                    self.config["api"]["api_key"]
                )
            except Exception as e:
                logger.error(f"解密API密钥失败: {e}")

    def _load_api_from_env(self) -> None:
        """从环境变量加载API配置"""
        # API密钥
        api_key = os.getenv("SCREENTRACE_API_KEY")
        if api_key:
            self.config.setdefault("api", {})["api_key"] = api_key
            logger.info("从环境变量加载API密钥")

        # API提供商
        provider = os.getenv("SCREENTRACE_API_PROVIDER")
        if provider:
            self.config.setdefault("api", {})["provider"] = provider
            logger.info(f"从环境变量加载API提供商: {provider}")

        # API基础URL（自定义）
        base_url = os.getenv("SCREENTRACE_API_BASE_URL")
        if base_url:
            self.config.setdefault("api", {})["base_url"] = base_url
            logger.info(f"从环境变量加载API基础URL: {base_url}")

        # API模型
        model = os.getenv("SCREENTRACE_API_MODEL")
        if model:
            self.config.setdefault("api", {})["model"] = model
            logger.info(f"从环境变量加载API模型: {model}")

        # API兼容模式（决定如何构造请求）
        compatibility = os.getenv("SCREENTRACE_API_COMPATIBILITY")
        if compatibility:
            self.config.setdefault("api", {})["compatibility"] = compatibility
            logger.info(f"从环境变量加载API兼容模式: {compatibility}")


    def set_encryption_key(self, key: bytes) -> None:
        """设置加密密钥"""
        self._encryption_key = key

    def setup_encryption_key_from_password(self, password: str) -> None:
        """从用户密码派生加密密钥"""
        import hashlib
        # 使用PBKDF2从密码派生密钥
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            b'ScreenTrace',  # salt
            100000
        )
        # Fernet需要32字节的密钥
        self._encryption_key = Fernet(base64.urlsafe_b64encode(key))


class ConfigWizard:
    """配置向导"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager

    def run(self) -> None:
        """运行配置向导"""
        print("\n" + "=" * 50)
        print("ScreenTrace 配置向导")
        print("=" * 50 + "\n")

        print("欢迎使用 ScreenTrace！")
        print("这是您第一次运行，需要进行初始配置。\n")

        # 1. API配置
        print("步骤 1/5: API配置")
        print("-" * 50)
        print("\n您可以使用预设API提供商或自定义API服务\n")

        print("选项：")
        print("1. OpenAI")
        print("2. Claude (Anthropic)")
        print("3. Gemini (Google)")
        print("4. 自定义URL")

        choice = self._input_with_default("请选择 (1-4)", "1")

        # 根据选择设置提供商
        provider_map = {
            "1": ("openai", "https://api.openai.com/v1"),
            "2": ("claude", "https://api.anthropic.com/v1"),
            "3": ("gemini", "https://generativelanguage.googleapis.com/v1"),
            "4": ("custom", None)
        }

        provider, default_url = provider_map.get(choice, ("openai", "https://api.openai.com/v1"))
        self.config_manager.set("api.provider", provider)

        # 如果选择自定义，让用户输入URL
        if provider == "custom":
            base_url = input("请输入API基础URL (如: http://localhost:11434/v1): ").strip()
            if not base_url:
                print("错误：自定义URL不能为空")
                raise ValueError("自定义URL不能为空")
            self.config_manager.set("api.base_url", base_url)

            # 让用户选择兼容模式
            print("\n选择API兼容模式：")
            print("1. OpenAI格式（推荐，适用于大多数兼容服务）")
            print("2. Claude格式")
            print("3. Gemini格式")

            compat_choice = self._input_with_default("请选择 (1-3)", "1")
            compat_map = {"1": "openai", "2": "claude", "3": "gemini"}
            compatibility = compat_map.get(compat_choice, "openai")
            self.config_manager.set("api.compatibility", compatibility)
            print(f"API兼容模式: {compatibility}")
        else:
            # 使用默认URL
            self.config_manager.set("api.base_url", default_url)
            # 兼容模式默认与提供商一致
            self.config_manager.set("api.compatibility", provider)

        # API密钥
        print(f"\n配置 {provider.upper()} API密钥：")
        print("提示：也可以在 .env 文件中设置 SCREENTRACE_API_KEY 环境变量\n")

        api_key = input("请输入API密钥 (留空则使用.env配置): ").strip()
        if api_key:
            self.config_manager.set("api.api_key", api_key)
        else:
            print("将在启动时从环境变量加载API密钥")

        # 模型名称
        model_defaults = {
            "openai": "gpt-4-vision-preview",
            "claude": "claude-3-5-sonnet-20241022",
            "gemini": "gemini-1.5-flash",
            "custom": "gpt-4-vision-preview"
        }
        default_model = model_defaults.get(provider, "gpt-4-vision-preview")

        model = self._input_with_default(
            f"模型名称",
            default_model
        )
        self.config_manager.set("api.model", model)

        # 2. 截图配置
        print("\n步骤 2/5: 截图配置")
        print("-" * 50)

        interval = self._input_int_with_default(
            "截图间隔（分钟，1-60）",
            10
        )
        self.config_manager.set("screenshot.interval_minutes", interval)

        similarity = self._input_float_with_default(
            "相似度阈值（0-1，越高越严格）",
            0.85
        )
        self.config_manager.set("screenshot.similarity_threshold", similarity)

        # 3. 数据存储配置
        print("\n步骤 3/5: 数据存储配置")
        print("-" * 50)

        retention = self._input_int_with_default(
            "数据保留天数",
            90
        )
        self.config_manager.set("storage.retention_days", retention)

        auto_cleanup = self._input_yes_no("是否自动清理旧数据", True)
        self.config_manager.set("storage.auto_cleanup", auto_cleanup)

        # 4. Web面板配置
        print("\n步骤 4/5: Web面板配置")
        print("-" * 50)

        port = self._input_int_with_default(
            "Web面板端口",
            8080
        )
        self.config_manager.set("dashboard.port", port)

        auto_open = self._input_yes_no("启动时自动打开浏览器", False)
        self.config_manager.set("dashboard.auto_open_browser", auto_open)

        # 5. 创建.env文件提示
        print("\n步骤 5/5: 环境变量配置")
        print("-" * 50)
        print("您可以创建 .env 文件来管理敏感配置")
        print("示例：")
        print("  SCREENTRACE_API_KEY=your_key_here")
        print("  SCREENTRACE_API_BASE_URL=http://localhost:11434/v1")
        print("\n参考 .env.example 文件获取完整配置说明")

        # 保存配置
        print("\n配置完成！正在保存...")
        self.config_manager.save()
        print("配置已保存到: config/settings.json")

    def _input_with_default(self, prompt: str, default: str) -> str:
        """带默认值的输入"""
        value = input(f"{prompt} (默认: {default}): ").strip()
        return value if value else default

    def _input_int_with_default(self, prompt: str, default: int) -> int:
        """带默认值的整数输入"""
        while True:
            value = input(f"{prompt} (默认: {default}): ").strip()
            if not value:
                return default
            try:
                return int(value)
            except ValueError:
                print("请输入有效的整数")

    def _input_float_with_default(self, prompt: str, default: float) -> float:
        """带默认值的浮点数输入"""
        while True:
            value = input(f"{prompt} (默认: {default}): ").strip()
            if not value:
                return default
            try:
                return float(value)
            except ValueError:
                print("请输入有效的数字")

    def _input_yes_no(self, prompt: str, default: bool) -> bool:
        """是/否输入"""
        default_str = "Y/n" if default else "y/N"
        while True:
            value = input(f"{prompt} ({default_str}): ").strip().lower()
            if not value:
                return default
            if value in ['y', 'yes', '是']:
                return True
            if value in ['n', 'no', '否']:
                return False
            print("请输入 y/yes 或 n/no")
