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
        return """你是一个活动记录助手。请分析这张屏幕截图，提取以下信息：

1. 【应用名称】：当前使用的应用或网站

2. 【生活维度】：从以下分类中选择最匹配的
   - 工作（职业相关活动）
   - 学习（自我提升、教育相关）
   - 休闲（娱乐、放松）
   - 生活（日常事务）
   - 其他（请注明）

3. 【活动形式】：从以下分类中选择
   - 创作/操作（编写、设计、操作软件）
   - 阅读/观看（文档、视频、文章）
   - 沟通协作（会议、聊天、邮件）
   - 浏览检索（搜索、浏览网页）
   - 其他（请注明）

4. 【详细描述】：描述具体在做什么（包含内容主题+具体活动）
   格式：<活动动词> + <内容主题> + <具体细节>
   示例：
   - "观看 Python 多线程教程视频"
   - "阅读《海贼王》漫画"
   - "编写用户认证模块代码"
   - "浏览京东购物网站"

5. 【关键词】：提取3-5个关键词
   示例：Python, 多线程, 教程 或 漫画, 海贼王, 休闲

请以JSON格式输出：
{
  "app": "应用名称",
  "life_category": "生活维度",
  "activity_form": "活动形式",
  "description": "详细描述",
  "keywords": ["关键词1", "关键词2"]
}"""

    @staticmethod
    def get_context_aware_prompt(
        previous_description: str,
        previous_app: str,
        time_gap_minutes: float
    ) -> str:
        """
        获取带上下文的Prompt模板

        Args:
            previous_description: 上一个任务描述
            previous_app: 上一个应用名
            time_gap_minutes: 距离上次截图的时间（分钟）

        Returns:
            带上下文的提示词
        """
        base_prompt = PromptTemplates.get_screenshot_analysis_prompt()

        context = f"""

【上下文信息】
- 上次活动：{previous_description}
- 上次应用：{previous_app}
- 时间间隔：{time_gap_minutes:.1f}分钟

如果当前截图与上次活动相同或延续，请在描述中体现连续性。
例如："继续编写用户认证模块代码" 而非 "编写用户认证模块代码"
"""

        return base_prompt + context

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
        time_gap_minutes: float = None
    ) -> str:
        """
        构建截图分析Prompt

        Args:
            previous_data: 上一次的截图分析数据
            time_gap_minutes: 时间间隔（分钟）

        Returns:
            完整的提示词
        """
        # 如果启用上下文且有历史数据
        if (self.use_context and
            previous_data and
            time_gap_minutes is not None):

            return self.templates.get_context_aware_prompt(
                previous_description=previous_data.get('description', ''),
                previous_app=previous_data.get('app', ''),
                time_gap_minutes=time_gap_minutes
            )

        # 否则返回基础Prompt
        return self.templates.get_screenshot_analysis_prompt()

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
