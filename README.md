# ScreenTrace

**智能屏幕活动追踪与时间管理工具**

## 项目简介

ScreenTrace 是一个个人时间管理工具，通过定期截屏和多模态大模型API分析，自动记录用户一天的活动，并生成周报和统计报告。

## 核心功能

- 📸 **智能截图采集** - 定时截图 + 窗口切换检测 + 智能去重
- 🔒 **隐私保护** - 三层黑名单过滤机制
- 🤖 **AI分析** - 多模态大模型自动分析活动内容
- 📊 **多维度报告** - 时间线、统计、叙述式报告
- 📈 **Web统计面板** - 交互式数据可视化

## 技术栈

- **语言**: Python 3.9+
- **数据库**: SQLite
- **Web框架**: Flask
- **可视化**: Plotly
- **API**: OpenAI / Claude / Gemini

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置

**方式一：使用配置向导（推荐）**

首次运行会自动启动配置向导：
```bash
python main.py
```

**方式二：使用环境变量**

1. 复制环境变量模板：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，设置必要的环境变量：
```bash
# API配置
SCREENTRACE_API_KEY=your_api_key_here
SCREENTRACE_API_PROVIDER=openai
SCREENTRACE_API_BASE_URL=https://api.openai.com/v1
SCREENTRACE_API_MODEL=gpt-4-vision-preview
SCREENTRACE_API_COMPATIBILITY=openai
```

**支持自定义API服务：**
- 可以使用任意兼容OpenAI格式的API服务
- 支持本地部署的服务（如Ollama）
- 只需设置 `SCREENTRACE_API_BASE_URL` 和 `SCREENTRACE_API_COMPATIBILITY`

### 运行

**启动监控**：
```bash
python main.py
```

首次运行会启动配置向导，帮助您完成初始设置。

**查看统计面板**：
```bash
python run_dashboard.py
```
访问 http://localhost:8080 查看实时统计

**生成报告**：
```bash
# 生成所有报告（最近7天）
python generate_reports.py --type all --days 7

# 使用AI生成叙述式报告
python generate_reports.py --type narrative --days 7 --ai
```

## 项目结构

```
ScreenTrace/
├── src/                  # 源代码
│   ├── core/            # 核心监控功能
│   ├── privacy/         # 隐私保护
│   ├── api/             # API集成
│   ├── storage/         # 数据存储
│   ├── report/          # 报告生成
│   ├── dashboard/       # Web统计面板
│   └── utils/           # 工具函数
├── config/              # 配置文件
├── tests/               # 测试文件
├── docs/                # 文档
├── data/                # 数据存储
└── logs/                # 日志文件
```

## 配置说明

### 截图设置
- `interval_minutes`: 截图间隔（分钟）
- `similarity_threshold`: 相似度阈值（0-1）

### 隐私设置
- `blacklist_apps`: 应用黑名单
- `blacklist_title_keywords`: 窗口标题关键词黑名单

### API设置
- `provider`: API提供商（openai/claude/gemini/custom）
- `api_key`: API密钥（可通过环境变量设置）
- `base_url`: API基础URL（支持自定义）
- `compatibility`: API兼容模式（openai/claude/gemini）

**自定义URL示例：**
```bash
# 使用Ollama本地服务
SCREENTRACE_API_BASE_URL=http://localhost:11434/v1
SCREENTRACE_API_COMPATIBILITY=openai

# 使用第三方兼容服务
SCREENTRACE_API_BASE_URL=https://your-service.com/v1
SCREENTRACE_API_COMPATIBILITY=openai
```

详细配置说明请参考 [用户手册](docs/user-guide.md)

## 开发指南

### 运行测试

```bash
pytest tests/
```

### 打包发布

```bash
pyinstaller --onefile --windowed --name ScreenTrace main.py
```

## 路线图

### v1.0（当前）
- ✅ 核心截图和分析功能
- ✅ 黑名单隐私保护
- ✅ 多维度报告生成
- ✅ Web统计面板

### v1.1（计划中）
- 🔄 数据加密存储
- 🔄 实时仪表盘
- 🔄 性能优化

### v2.0（未来）
- 📅 macOS支持
- 📅 Electron UI重构
- 📅 云端同步

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

如有问题或建议，请创建Issue。
