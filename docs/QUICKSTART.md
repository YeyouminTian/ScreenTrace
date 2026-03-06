# ScreenTrace 5分钟快速上手

## 🚀 快速开始

### 步骤1: 安装依赖 (2分钟)

```bash
pip install -r requirements.txt
```

### 步骤2: 配置API (2分钟)

**选项A：使用免费本地模型（推荐）**

```bash
# 安装Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 下载模型
ollama pull llava

# 启动服务
ollama serve
```

创建 `.env` 文件：
```bash
SCREENTRACE_API_PROVIDER=custom
SCREENTRACE_API_BASE_URL=http://localhost:11434/v1
SCREENTRACE_API_MODEL=llava
SCREENTRACE_API_COMPATIBILITY=openai
SCREENTRACE_API_KEY=ollama
```

**选项B：使用云端API**

```bash
# OpenAI示例
SCREENTRACE_API_KEY=sk-xxx
SCREENTRACE_API_PROVIDER=openai
SCREENTRACE_API_MODEL=gpt-4o-mini

# Claude示例
SCREENTRACE_API_KEY=sk-ant-xxx
SCREENTRACE_API_PROVIDER=claude
SCREENTRACE_API_MODEL=claude-3-5-sonnet-20241022

# Gemini示例
SCREENTRACE_API_KEY=xxx
SCREENTRACE_API_PROVIDER=gemini
SCREENTRACE_API_MODEL=gemini-1.5-flash
```

### 步骤3: 测试连接 (30秒)

```bash
python test_api.py
```

看到 "✅ API连接成功" 即可。

### 步骤4: 启动监控 (30秒)

```bash
python main.py
```

程序开始自动截图和分析！

---

## 📊 查看统计

**实时Web面板**：
```bash
python run_dashboard.py
```
访问 http://localhost:8080

**生成报告**：
```bash
# 生成所有报告（最近7天）
python generate_reports.py --type all --days 7
```

---

## 🎯 使用建议

### 工作日（收集数据）
```bash
# 早上启动
python main.py

# 程序会自动：
# - 每10分钟截图
# - 窗口切换时截图
# - AI分析活动
# - 保存到数据库
```

### 周末（查看统计）
```bash
# 查看实时统计
python run_dashboard.py

# 生成周报
python generate_reports.py --type narrative --days 7
```

---

## ⚙️ 常用配置

### 调整截图频率

编辑 `config/settings.json`：
```json
{
  "screenshot": {
    "interval_minutes": 15  // 改为15分钟
  }
}
```

### 添加黑名单

```json
{
  "privacy": {
    "blacklist_apps": [
      "1Password.exe",
      "YourApp.exe"
    ],
    "blacklist_title_keywords": [
      "密码", "私密"
    ]
  }
}
```

---

## 🔧 故障排查

### 问题1：API连接失败

```bash
# 重新测试
python test_api.py

# 检查配置
cat .env

# 检查网络
ping api.openai.com
```

### 问题2：没有截图记录

```bash
# 检查数据库
sqlite3 data/screenTrace.db "SELECT COUNT(*) FROM screenshots;"

# 查看日志
tail -f logs/screentrace.log
```

### 问题3：Web面板打不开

```bash
# 检查端口
netstat -ano | findstr :8080

# 修改端口
# 编辑 config/settings.json
{
  "dashboard": {
    "port": 9090
  }
}
```

---

## 📖 更多文档

- **完整配置**: `docs/api-configuration.md`
- **测试指南**: `docs/complete-testing-guide.md`
- **项目总览**: `docs/PROJECT_SUMMARY.md`

---

## 💡 最佳实践

### 1. 使用本地模型
- 完全免费
- 隐私保护
- 无网络延迟

### 2. 合理设置截图间隔
- 高频工作：5-10分钟
- 正常使用：10-15分钟
- 低频使用：15-30分钟

### 3. 定期查看统计
- 每日查看Web面板
- 每周生成报告
- 每月分析趋势

### 4. 调整黑名单
- 添加敏感应用
- 添加关键词过滤
- 定期审查

---

## 🎉 开始使用

```bash
# 1. 启动监控
python main.py

# 2. 正常工作
# 程序会在后台自动记录

# 3. 查看统计
python run_dashboard.py

# 4. 生成报告
python generate_reports.py --type all --days 7
```

享受智能时间管理！ 🚀
