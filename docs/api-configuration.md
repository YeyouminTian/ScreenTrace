# API配置指南

ScreenTrace 支持多种多模态大模型API，包括预设提供商和自定义API服务。

---

## 快速开始

### 方式一：配置向导

首次运行 `python main.py` 会启动配置向导，按照提示选择API提供商并输入密钥。

### 方式二：环境变量（推荐）

创建 `.env` 文件（参考 `.env.example`），设置以下环境变量：

```bash
SCREENTRACE_API_KEY=your_api_key_here
SCREENTRACE_API_PROVIDER=openai
SCREENTRACE_API_BASE_URL=https://api.openai.com/v1
SCREENTRACE_API_MODEL=gpt-4-vision-preview
SCREENTRACE_API_COMPATIBILITY=openai
```

---

## 预设API提供商

### OpenAI

```bash
SCREENTRACE_API_PROVIDER=openai
SCREENTRACE_API_KEY=sk-xxx
SCREENTRACE_API_BASE_URL=https://api.openai.com/v1
SCREENTRACE_API_MODEL=gpt-4-vision-preview
SCREENTRACE_API_COMPATIBILITY=openai
```

**支持的模型：**
- `gpt-4-vision-preview`
- `gpt-4o`
- `gpt-4o-mini`

### Claude (Anthropic)

```bash
SCREENTRACE_API_PROVIDER=claude
SCREENTRACE_API_KEY=sk-ant-xxx
SCREENTRACE_API_BASE_URL=https://api.anthropic.com/v1
SCREENTRACE_API_MODEL=claude-3-5-sonnet-20241022
SCREENTRACE_API_COMPATIBILITY=claude
```

**支持的模型：**
- `claude-3-5-sonnet-20241022`
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`

### Gemini (Google)

```bash
SCREENTRACE_API_PROVIDER=gemini
SCREENTRACE_API_KEY=xxx
SCREENTRACE_API_BASE_URL=https://generativelanguage.googleapis.com/v1
SCREENTRACE_API_MODEL=gemini-1.5-flash
SCREENTRACE_API_COMPATIBILITY=gemini
```

**支持的模型：**
- `gemini-1.5-flash`
- `gemini-1.5-pro`
- `gemini-pro-vision`

---

## 自定义API服务

ScreenTrace 支持任何兼容 OpenAI 格式的API服务。

### 本地部署示例

#### Ollama

```bash
SCREENTRACE_API_PROVIDER=custom
SCREENTRACE_API_BASE_URL=http://localhost:11434/v1
SCREENTRACE_API_MODEL=llava
SCREENTRACE_API_COMPATIBILITY=openai
```

**安装Ollama：**
```bash
# 安装Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 下载多模态模型
ollama pull llava

# 启动服务（默认端口11434）
ollama serve
```

#### LM Studio

```bash
SCREENTRACE_API_PROVIDER=custom
SCREENTRACE_API_BASE_URL=http://localhost:1234/v1
SCREENTRACE_API_MODEL=local-model
SCREENTRACE_API_COMPATIBILITY=openai
```

### 第三方兼容服务

#### DeepSeek

```bash
SCREENTRACE_API_PROVIDER=custom
SCREENTRACE_API_KEY=sk-xxx
SCREENTRACE_API_BASE_URL=https://api.deepseek.com/v1
SCREENTRACE_API_MODEL=deepseek-chat
SCREENTRACE_API_COMPATIBILITY=openai
```

#### Moonshot (月之暗面)

```bash
SCREENTRACE_API_PROVIDER=custom
SCREENTRACE_API_KEY=sk-xxx
SCREENTRACE_API_BASE_URL=https://api.moonshot.cn/v1
SCREENTRACE_API_MODEL=moonshot-v1-8k-vision
SCREENTRACE_API_COMPATIBILITY=openai
```

#### 智谱AI (GLM)

```bash
SCREENTRACE_API_PROVIDER=custom
SCREENTRACE_API_KEY=xxx
SCREENTRACE_API_BASE_URL=https://open.bigmodel.cn/api/paas/v4
SCREENTRACE_API_MODEL=glm-4v
SCREENTRACE_API_COMPATIBILITY=openai
```

---

## API兼容模式说明

`SCREENTRACE_API_COMPATIBILITY` 决定了ScreenTrace如何构造API请求：

### `openai`（推荐）
- 适用于：OpenAI、Ollama、LM Studio、DeepSeek、Moonshot等大多数服务
- 请求格式：标准的OpenAI Vision API格式
- 兼容性最广

### `claude`
- 适用于：Anthropic Claude API
- 请求格式：Claude Messages API格式
- 包含特定的头部和处理逻辑

### `gemini`
- 适用于：Google Gemini API
- 请求格式：Gemini GenerateContent API格式
- 使用Google特有的认证方式

---

## 配置优先级

ScreenTrace 按以下优先级加载配置：

1. **环境变量**（最高优先级）
   - 从 `.env` 文件加载
   - 敏感信息推荐使用环境变量

2. **配置文件** (`config/settings.json`)
   - 非敏感配置
   - 运行时生成

3. **默认值**（最低优先级）
   - 代码中的默认配置

---

## 测试API配置

创建测试脚本 `test_api.py`：

```python
import os
from dotenv import load_dotenv
from src.api.client import APIClient
from src.utils.config import ConfigManager

# 加载环境变量
load_dotenv()

# 初始化配置
config_manager = ConfigManager()
config_manager.load()

# 创建API客户端
client = APIClient(config_manager.config['api'])

# 测试API连接
result = client.test_connection()
if result:
    print("✅ API连接成功")
else:
    print("❌ API连接失败")
```

---

## 成本优化建议

### 1. 使用本地模型
推荐使用 Ollama + LLaVA 等本地多模态模型：
- 完全免费
- 隐私保护（数据不上传）
- 无网络延迟

### 2. 调整截图频率
```bash
# 增加截图间隔（分钟）
SCREENTRACE_SCREENSHOT_INTERVAL=15
```

### 3. 提高去重阈值
```bash
# 提高相似度阈值（减少API调用）
SCREENTRACE_SIMILARITY_THRESHOLD=0.90
```

### 4. 使用更便宜的模型
- OpenAI: `gpt-4o-mini`（比 `gpt-4-vision` 便宜）
- Gemini: `gemini-1.5-flash`（免费额度较高）
- 本地: `llava`（完全免费）

---

## 故障排查

### API密钥错误
```
错误：Invalid API key
解决：检查 SCREENTRACE_API_KEY 是否正确设置
```

### 连接超时
```
错误：Connection timeout
解决：
1. 检查网络连接
2. 检查 SCREENTRACE_API_BASE_URL 是否正确
3. 增加超时时间（在 settings.json 中设置 api.timeout_seconds）
```

### 模型不支持视觉
```
错误：Model does not support vision
解决：确保使用支持图像的模型（如 gpt-4-vision-preview、llava 等）
```

### 兼容模式错误
```
错误：Unexpected response format
解决：确保 SCREENTRACE_API_COMPATIBILITY 与实际API匹配
- 大多数服务使用 openai
- Claude API 必须使用 claude
- Gemini API 必须使用 gemini
```

---

## 安全建议

1. **使用环境变量存储API密钥**
   - 不要将 `.env` 文件提交到Git
   - 已在 `.gitignore` 中排除

2. **定期轮换API密钥**
   - 定期更新密钥
   - 监控API使用情况

3. **限制API密钥权限**
   - 只授予必要的权限
   - 设置使用额度限制

4. **使用本地模型处理敏感数据**
   - 黑名单过滤的窗口截图不应发送到云端
   - 考虑使用Ollama等本地服务
