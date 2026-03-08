"""
Prompt模板模块
提供标准化的截图分析提示词
"""

from typing import Dict, Any


class PromptTemplates:
    """Prompt模板集合"""

    @staticmethod
    def get_screenshot_analysis_prompt() -> str:
        """
        获取截图分析的Prompt模板

        Returns:
            标准化的提示词
        """
        return """# 角色
你是 ScreenTrace 活动记录助手，负责分析用户的屏幕截图，结构化提取当前活动信息。

# 输入上下文
- 当前截图时间：{{timestamp}}
- 上一次截图的分析结果（可能为空）：{{previous_result}}

# 分析规则

## Step 1：屏幕状态判断
首先判断截图是否可分析：
- 如果是锁屏、黑屏、息屏、系统加载画面、截图模糊无法识别，则直接返回 `"status": "unrecognizable"`
- 如果可分析，返回 `"status": "ok"` 并继续以下步骤
- **聚焦前景窗口**，忽略被遮挡的背景窗口

## Step 2：结构化提取

### 2.1 应用名称（app）
- 识别当前前景应用或网站名称
- 如果是浏览器，请同时标注浏览器名称和当前网站，如 "Chrome - YouTube"

### 2.2 生活维度（life_category）
从以下枚举中选择 **最匹配的一项**：

| 枚举值 | 含义 |
|---|---|
| work | 职业相关：编程、文档、项目管理、邮件处理等 |
| study | 学习提升：教程、课程、技术文档阅读、刷题等 |
| leisure | 休闲娱乐：影视、游戏、社交媒体浏览、漫画等 |
| life | 日常生活：购物、理财、出行规划、健康管理等 |
| social | 社交沟通：非工作性质的即时聊天、社交平台互动 |
| other | 无法归入以上类别 |

### 2.3 活动形式（activity_form）
从以下枚举中选择 **最匹配的一项**：

| 枚举值 | 含义 |
|---|---|
| creating | 创作/操作：编写代码、设计图形、编辑文档等 |
| consuming | 阅读/观看：看视频、读文章、浏览文档等 |
| communicating | 沟通协作：会议、聊天、邮件、评论等 |
| browsing | 浏览检索：搜索引擎、商品浏览、信息流等 |
| operating | 系统操作：文件管理、设置调整、安装软件等 |
| other | 无法归入以上类别 |

### 2.4 详细描述（description）
- 格式：`<动词> + <内容主题> + <具体细节>`
- 控制在 15-40 个字
- **不得包含截图中可见的个人隐私信息**（姓名、账号、密码、私人对话内容等），用通用描述替代
- 示例："观看 Python 异步编程教程视频"、"在电商平台浏览数码产品"

### 2.5 关键词（keywords）
- 提取 3-5 个关键词，用于后续聚合统计
- 偏向**主题和工具**，避免动词

### 2.6 置信度（confidence）
- 对本次分析结果的整体置信度评分：high / medium / low
- 如果画面模糊、信息量少、难以判断，应如实标注 low

### 2.7 活动连续性（is_continuation）
- 对比 `{{previous_result}}`，判断当前活动是否是上一次的延续
- `true`：同一应用、同一任务的继续
- `false`：切换了新活动
- `null`：无上一次记录或无法判断

# 输出格式
严格输出以下 JSON，不要添加任何额外文字：

{
  "status": "ok | unrecognizable",
  "app": "string",
  "life_category": "work | study | leisure | life | social | other",
  "activity_form": "creating | consuming | communicating | browsing | operating | other",
  "description": "string",
  "keywords": ["string"],
  "confidence": "high | medium | low",
  "is_continuation": true | false | null,
  "sensitive_flag": false
}

# 特殊说明
- 如果截图中包含明显的隐私/敏感内容（密码输入框、私密聊天等），将 `sensitive_flag` 设为 `true`，并在 description 中进行脱敏处理
- 如果 status 为 "unrecognizable"，其他字段全部填 null"""

    @staticmethod
    def get_context_aware_prompt(
        previous_result: str,
        timestamp: str
    ) -> str:
        """
        获取带上下文的Prompt模板

        Args:
            previous_result: 上一次截图的完整分析结果（JSON格式）
            timestamp: 当前截图的时间戳

        Returns:
            带上下文的提示词
        """
        base_prompt = PromptTemplates.get_screenshot_analysis_prompt()

        # 替换占位符
        base_prompt = base_prompt.replace("{{timestamp}}", timestamp)
        base_prompt = base_prompt.replace("{{previous_result}}", previous_result or "无")

        return base_prompt

    @staticmethod
    def get_narrative_report_prompt(
        screenshots_data: list,
        time_range: str
    ) -> str:
        """
        获取叙述式报告生成的Prompt

        Args:
            screenshots_data: 截图数据列表
            time_range: 时间范围描述

        Returns:
            报告生成提示词
        """
        # 格式化截图数据
        formatted_data = []
        for i, data in enumerate(screenshots_data, 1):
            formatted_data.append(
                f"{i}. [{data['time']}] {data['description']} ({data['app']})"
            )

        data_str = "\n".join(formatted_data)

        return f"""请根据以下活动记录，生成一份{time_range}的工作总结报告。

【活动记录】
{data_str}

【要求】
1. 用叙述性语言总结主要工作内容
2. 按工作类型分组描述
3. 突出重要成果和关键任务
4. 语言简洁、专业，类似工作周报风格
5. 字数控制在300-500字

【输出格式】
直接输出报告文本，不要包含额外的JSON或格式标记。"""

    @staticmethod
    def get_task_classification_prompt() -> str:
        """
        获取任务分类的辅助Prompt

        Returns:
            任务分类提示词
        """
        return """请对以下活动进行任务分类和重要性评估。

【分类标准】
- 核心工作：主要职责相关，创造价值的工作
- 辅助工作：支持性工作，如邮件、会议
- 学习成长：技能提升、知识学习
- 休息放松：娱乐、社交、休息

请以JSON格式输出：
{
  "task_priority": "高/中/低",
  "task_category": "核心工作/辅助工作/学习成长/休息放松",
  "estimated_duration_minutes": 预估时长（整数）
}"""


class PromptBuilder:
    """Prompt构建器"""

    def __init__(self, use_context: bool = True):
        """
        初始化Prompt构建器

        Args:
            use_context: 是否使用上下文信息
        """
        self.use_context = use_context
        self.templates = PromptTemplates()

    def build_analysis_prompt(
        self,
        previous_data: Dict[str, Any] = None,
        timestamp: str = None
    ) -> str:
        """
        构建截图分析Prompt

        Args:
            previous_data: 上一次的截图分析数据（字典格式）
            timestamp: 当前截图的时间戳

        Returns:
            完整的提示词
        """
        import json

        # 如果启用上下文且有历史数据
        if self.use_context and previous_data:
            # 将上一次结果转换为JSON字符串
            previous_json = json.dumps(previous_data, ensure_ascii=False)
            return self.templates.get_context_aware_prompt(
                previous_result=previous_json,
                timestamp=timestamp or ""
            )

        # 否则返回基础Prompt（不带上下文）
        base_prompt = self.templates.get_screenshot_analysis_prompt()
        # 替换占位符
        base_prompt = base_prompt.replace("{{timestamp}}", timestamp or "")
        base_prompt = base_prompt.replace("{{previous_result}}", "无")
        return base_prompt

    def build_report_prompt(
        self,
        screenshots_data: list,
        time_range: str = "本周"
    ) -> str:
        """
        构建报告生成Prompt

        Args:
            screenshots_data: 截图数据列表
            time_range: 时间范围

        Returns:
            报告生成提示词
        """
        return self.templates.get_narrative_report_prompt(
            screenshots_data,
            time_range
        )
