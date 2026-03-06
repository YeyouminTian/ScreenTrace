# ScreenTrace 使用示例

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt
```

### 2. 配置API

**选项A：使用预设API（推荐新手）**

首次运行会启动配置向导：
```bash
python main.py
```

按照提示选择API提供商并输入密钥。

**选项B：使用自定义API（推荐高级用户）**

创建 `.env` 文件：
```bash
cp .env.example .env
```

编辑 `.env` 文件：
```bash
# OpenAI示例
SCREENTRACE_API_KEY=sk-xxx
SCREENTRACE_API_PROVIDER=openai
SCREENTRACE_API_MODEL=gpt-4-vision-preview

# 或使用本地Ollama
SCREENTRACE_API_PROVIDER=custom
SCREENTRACE_API_BASE_URL=http://localhost:11434/v1
SCREENTRACE_API_MODEL=llava
SCREENTRACE_API_COMPATIBILITY=openai
```

### 3. 测试API连接

```bash
python test_api.py
```

如果看到 "✅ API连接成功"，说明配置正确。

### 4. 启动监控

```bash
python main.py
```

程序会自动：
- 每10分钟截图一次
- 窗口切换时自动截图
- 智能去重避免重复
- 黑名单过滤敏感窗口

### 5. 查看数据

**截图文件：**
```bash
# 按日期分文件夹存储
ls data/screenshots/2026-03-05/
```

**数据库记录：**
```bash
# 使用SQLite查看
sqlite3 data/screenTrace.db "SELECT * FROM screenshots LIMIT 5;"
```

---

## 使用场景

### 场景1：使用OpenAI API

```bash
# .env
SCREENTRACE_API_KEY=sk-xxx
SCREENTRACE_API_PROVIDER=openai
SCREENTRACE_API_MODEL=gpt-4o-mini
```

### 场景2：使用Claude API

```bash
# .env
SCREENTRACE_API_KEY=sk-ant-xxx
SCREENTRACE_API_PROVIDER=claude
SCREENTRACE_API_MODEL=claude-3-5-sonnet-20241022
```

### 场景3：使用本地Ollama（免费）

```bash
# 安装Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 下载模型
ollama pull llava

# 启动服务
ollama serve

# .env配置
SCREENTRACE_API_PROVIDER=custom
SCREENTRACE_API_BASE_URL=http://localhost:11434/v1
SCREENTRACE_API_MODEL=llava
SCREENTRACE_API_COMPATIBILITY=openai
```

### 场景4：使用第三方服务（DeepSeek示例）

```bash
# .env
SCREENTRACE_API_KEY=sk-xxx
SCREENTRACE_API_PROVIDER=custom
SCREENTRACE_API_BASE_URL=https://api.deepseek.com/v1
SCREENTRACE_API_MODEL=deepseek-chat
SCREENTRACE_API_COMPATIBILITY=openai
```

---

## 高级配置

### 调整截图频率

在 `.env` 中添加：
```bash
# 截图间隔（分钟）
SCREENTRACE_SCREENSHOT_INTERVAL=15

# 相似度阈值（0-1，越高越严格）
SCREENTRACE_SIMILARITY_THRESHOLD=0.90
```

### 自定义黑名单

编辑 `config/settings.json`：
```json
{
  "privacy": {
    "blacklist_apps": [
      "1Password.exe",
      "Bitwarden.exe",
      "YourSecretApp.exe"
    ],
    "blacklist_title_keywords": [
      "密码", "银行", "支付", "私密"
    ]
  }
}
```

---

## 故障排查

### 问题1：API连接失败

**检查步骤：**
1. 运行测试：`python test_api.py`
2. 检查 `.env` 文件配置
3. 确认API密钥有效
4. 检查网络连接

### 问题2：截图权限错误

**解决方案：**
- Windows：以管理员身份运行
- 检查是否有安全软件阻止截图

### 问题3：窗口监听不工作

**检查步骤：**
1. 确认安装了 pywin32：`pip install pywin32`
2. 检查日志文件：`logs/screentrace.log`

### 问题4：数据库错误

**解决方案：**
```bash
# 删除数据库重新初始化
rm data/screenTrace.db
python main.py
```

---

## 下一步

- 查看完整API配置：`docs/api-configuration.md`
- 查看测试指南：`docs/testing-guide.md`
- 查看实施计划：`docs/plans/2026-03-05-implementation-plan.md`
