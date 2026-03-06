# ScreenTrace 完整测试指南

## 快速测试

### 1. 环境检查

```bash
# 安装依赖
pip install -r requirements.txt

# 验证安装
python -c "import PIL, pyautogui, win32gui, imagehash, requests; print('✅ 所有依赖已安装')"
```

### 2. API配置测试

```bash
# 测试API连接
python test_api.py
```

**预期输出**：
```
✅ 找到 .env 文件
当前API配置：
  提供商: openai
  基础URL: https://api.openai.com/v1
  模型: gpt-4-vision-preview
  兼容模式: openai
  API密钥: sk-xxx...xxx

✅ API连接成功！
```

### 3. 启动完整系统

```bash
python main.py
```

---

## 功能测试清单

### ✅ 测试1：窗口切换检测

**操作**：
1. 启动程序
2. 在不同应用间切换（Chrome → VSCode → 文件管理器）
3. 在同一应用内切换标签页

**预期结果**：
```
INFO - 窗口切换: Google - Chrome (chrome.exe)
INFO - 正在分析截图: data/screenshots/...
INFO - 截图分析完成: 浏览Google首页 [休闲/浏览检索]

INFO - 标签页切换: GitHub - Chrome (chrome.exe)
INFO - 正在分析截图: ...
INFO - 截图分析完成: 浏览GitHub代码仓库 [工作/浏览检索]
```

**验证**：
- 日志显示窗口/标签页切换
- 截图文件已生成
- 数据库有记录

### ✅ 测试2：定时截图

**操作**：
1. 等待10分钟（默认间隔）
2. 不切换窗口

**预期结果**：
```
INFO - 定时器触发截图
INFO - 正在分析截图: ...
INFO - 截图分析完成: ...
```

### ✅ 测试3：智能去重

**操作**：
1. 切换窗口
2. 立即切回原窗口（< 2分钟）
3. 观察日志

**预期结果**：
```
INFO - 标签页切换: ... (chrome.exe)
INFO - 去重检查: 图像相似度 95.23% 超过阈值，跳过
```

### ✅ 测试4：黑名单过滤

**操作**：
1. 打开密码管理器（如1Password）
2. 观察日志

**预期结果**：
```
INFO - 窗口在黑名单中，跳过截图: 1Password (1Password.exe)
```

### ✅ 测试5：API分析

**操作**：
1. 触发一次截图
2. 查看数据库记录

**验证**：
```bash
sqlite3 data/screenTrace.db "SELECT * FROM screenshots WHERE api_called=1 LIMIT 1;"
```

**预期结果**：
```json
{
  "app_name": "chrome.exe",
  "window_title": "Google - Chrome",
  "life_category": "休闲",
  "activity_form": "浏览检索",
  "description": "浏览Google搜索页面",
  "keywords": ["Google", "搜索", "休闲"],
  "api_called": 1
}
```

### ✅ 测试6：成本追踪

**操作**：
1. 触发几次截图
2. 查看API日志

**验证**：
```bash
sqlite3 data/screenTrace.db "SELECT * FROM api_logs ORDER BY timestamp DESC LIMIT 5;"
```

**预期结果**：
```json
{
  "timestamp": "2026-03-05T13:10:00",
  "provider": "openai",
  "model": "gpt-4-vision-preview",
  "tokens_used": 1250,
  "cost": 0.01875,
  "success": 1
}
```

---

## 数据验证

### 查看截图文件

```bash
# 查看今日截图
ls -lh data/screenshots/$(date +%Y-%m-%d)/
```

### 查看数据库统计

```bash
# 总记录数
sqlite3 data/screenTrace.db "SELECT COUNT(*) FROM screenshots;"

# 今日记录数
sqlite3 data/screenTrace.db "
SELECT COUNT(*) FROM screenshots
WHERE date(timestamp) = date('now');
"

# 生活维度分布
sqlite3 data/screenTrace.db "
SELECT life_category, COUNT(*) as count
FROM screenshots
WHERE life_category IS NOT NULL
GROUP BY life_category
ORDER BY count DESC;
"
```

---

## 性能测试

### 内存占用

**操作**：
```bash
# Windows
tasklist /FI "IMAGENAME eq python.exe"

# Linux/Mac
ps aux | grep python
```

**预期**：
- CPU: < 5% (空闲时)
- 内存: < 200MB

### 磁盘占用

**操作**：
```bash
# 查看截图文件夹大小
du -sh data/screenshots/

# 查看数据库大小
ls -lh data/screenTrace.db
```

**预期**：
- 每张截图: 100-300KB
- 数据库: < 10MB (1000条记录)

---

## 故障排查

### 问题1：API调用失败

**症状**：
```
ERROR - API请求失败: Connection timeout
WARNING - API分析失败，仅保存基础信息
```

**检查清单**：
- [ ] 运行 `python test_api.py`
- [ ] 检查 `.env` 文件中的 `SCREENTRACE_API_KEY`
- [ ] 检查 `SCREENTRACE_API_BASE_URL`
- [ ] 检查网络连接
- [ ] 检查API余额

### 问题2：窗口监听不工作

**症状**：
```
# 切换窗口，但没有触发截图
```

**检查清单**：
- [ ] 确认安装了 `pywin32`
- [ ] 以管理员身份运行
- [ ] 检查日志：`logs/screentrace.log`
- [ ] 重启程序

### 问题3：截图权限错误

**症状**：
```
ERROR - 截图失败: [WinError 5] 拒绝访问
```

**解决方案**：
- Windows: 以管理员身份运行
- 检查杀毒软件设置
- 允许Python访问屏幕

### 问题4：数据库错误

**症状**：
```
ERROR - database disk image is malformed
```

**解决方案**：
```bash
# 备份数据库
cp data/screenTrace.db data/screenTrace.db.backup

# 重新初始化
rm data/screenTrace.db
python main.py
```

---

## 压力测试

### 测试1：长时间运行

**操作**：
```bash
# 启动程序，运行24小时
python main.py
```

**监控**：
- 内存是否泄漏
- 日志文件大小
- 磁盘占用增长

### 测试2：高频切换

**操作**：
- 每秒切换一次窗口
- 持续10分钟

**预期**：
- 程序稳定运行
- 去重机制生效
- 无崩溃

### 测试3：大量数据

**操作**：
- 运行一周，累积约1000张截图

**验证**：
- 数据库查询速度
- 磁盘空间占用
- 启动速度

---

## API测试脚本

### test_api.py（已提供）

```bash
python test_api.py
```

### 测试单个截图分析

创建 `test_single_analysis.py`：

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.config import ConfigManager
from src.api.client import APIClient
from src.api.prompts import PromptBuilder

# 加载配置
config = ConfigManager()
config.load()

# 创建客户端
client = APIClient(config.config['api'])
prompt_builder = PromptBuilder()

# 测试图片路径
test_image = "data/screenshots/test.png"  # 替换为实际路径

# 分析
prompt = prompt_builder.build_analysis_prompt()
result = client.analyze_image(test_image, prompt)

if result:
    print("✅ 分析成功")
    print(result)
else:
    print("❌ 分析失败")
```

---

## 完整测试流程

```bash
# 1. 环境准备
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env

# 2. API测试
python test_api.py

# 3. 启动系统
python main.py

# 4. 功能测试
# - 切换窗口 10次
# - 切换标签页 10次
# - 等待定时截图 1次
# - 打开黑名单应用 1次

# 5. 数据验证
sqlite3 data/screenTrace.db "SELECT COUNT(*) FROM screenshots WHERE api_called=1;"

# 6. 清理测试数据
rm -rf data/screenshots/*
rm data/screenTrace.db

# 7. 重新启动验证
python main.py
```

---

## 下一步

- ✅ 功能测试通过 → 继续开发报告生成
- ❌ 功能测试失败 → 查看故障排查或提交Issue

测试通过后，可以开始使用ScreenTrace记录你的工作活动了！🎉
