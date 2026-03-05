"""
多模态API客户端基础框架
支持OpenAI、Claude、Gemini以及自定义兼容服务
"""

import base64
import json
import requests
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class APIClient:
    """多模态API客户端"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化API客户端

        Args:
            config: API配置字典，包含：
                - api_key: API密钥
                - base_url: API基础URL
                - model: 模型名称
                - compatibility: 兼容模式 (openai/claude/gemini)
                - max_tokens: 最大token数
                - timeout_seconds: 超时时间
                - retry_times: 重试次数
        """
        self.api_key = config.get("api_key", "")
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        self.model = config.get("model", "gpt-4-vision-preview")
        self.compatibility = config.get("compatibility", "openai")
        self.max_tokens = config.get("max_tokens", 500)
        self.timeout = config.get("timeout_seconds", 30)
        self.retry_times = config.get("retry_times", 3)

        # 智能处理base_url，移除多余的endpoint
        self._normalize_base_url()

        # 根据兼容模式设置请求构建器
        self._request_builders = {
            "openai": self._build_openai_request,
            "claude": self._build_claude_request,
            "gemini": self._build_gemini_request
        }

    def _normalize_base_url(self) -> None:
        """
        标准化base_url，移除多余的endpoint后缀
        例如：https://api.example.com/v1/chat/completions -> https://api.example.com/v1
        """
        # 需要移除的后缀
        suffixes_to_remove = [
            "/chat/completions",
            "/completions",
            "/messages",
            "/generateContent"
        ]

        for suffix in suffixes_to_remove:
            if self.base_url.endswith(suffix):
                self.base_url = self.base_url[:-len(suffix)]
                logger.info(f"自动移除base_url中的endpoint后缀: {suffix}")
                break

    def analyze_image(
        self,
        image_path: str,
        prompt: str
    ) -> Optional[Dict[str, Any]]:
        """
        分析图像

        Args:
            image_path: 图像文件路径
            prompt: 提示词

        Returns:
            解析后的JSON结果，失败返回None
        """
        try:
            # 读取图像
            image_data = self._read_image(image_path)

            # 构建请求
            build_request = self._request_builders.get(
                self.compatibility,
                self._build_openai_request
            )
            request_data = build_request(image_data, prompt)

            # 发送请求
            response = self._send_request(request_data)

            if response:
                # 解析响应
                return self._parse_response(response)

            return None

        except Exception as e:
            logger.error(f"分析图像失败: {e}")
            return None

    def _read_image(self, image_path: str) -> str:
        """
        读取图像并转换为base64

        Args:
            image_path: 图像路径

        Returns:
            base64编码的图像数据
        """
        with open(image_path, "rb") as f:
            image_data = f.read()

        return base64.b64encode(image_data).decode("utf-8")

    def _build_openai_request(
        self,
        image_data: str,
        prompt: str
    ) -> Dict[str, Any]:
        """
        构建OpenAI格式的请求

        Args:
            image_data: base64编码的图像
            prompt: 提示词

        Returns:
            请求数据字典
        """
        return {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": self.max_tokens
        }

    def _build_claude_request(
        self,
        image_data: str,
        prompt: str
    ) -> Dict[str, Any]:
        """
        构建Claude格式的请求

        Args:
            image_data: base64编码的图像
            prompt: 提示词

        Returns:
            请求数据字典
        """
        return {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            "max_tokens": self.max_tokens
        }

    def _build_gemini_request(
        self,
        image_data: str,
        prompt: str
    ) -> Dict[str, Any]:
        """
        构建Gemini格式的请求

        Args:
            image_data: base64编码的图像
            prompt: 提示词

        Returns:
            请求数据字典
        """
        return {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        },
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": image_data
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": self.max_tokens
            }
        }

    def _send_request(self, request_data: Dict[str, Any]) -> Optional[Dict]:
        """
        发送API请求

        Args:
            request_data: 请求数据

        Returns:
            响应数据，失败返回None
        """
        # 根据兼容模式确定endpoint
        if self.compatibility == "gemini":
            endpoint = f"{self.base_url}/models/{self.model}:generateContent"
            params = {"key": self.api_key}
            headers = {"Content-Type": "application/json"}
        elif self.compatibility == "claude":
            endpoint = f"{self.base_url}/messages"
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"
            }
            params = None
        else:  # openai
            endpoint = f"{self.base_url}/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            params = None

        # 发送请求（带重试）
        for attempt in range(self.retry_times):
            try:
                response = requests.post(
                    endpoint,
                    json=request_data,
                    headers=headers,
                    params=params,
                    timeout=self.timeout
                )

                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"API请求失败 (尝试 {attempt + 1}/{self.retry_times}): {e}"
                )
                if attempt == self.retry_times - 1:
                    logger.error(f"API请求最终失败: {e}")
                    return None

        return None

    def _parse_response(self, response: Dict) -> Optional[Dict[str, Any]]:
        """
        解析API响应

        Args:
            response: API响应数据

        Returns:
            解析后的结果字典
        """
        try:
            if self.compatibility == "gemini":
                # Gemini格式
                text = response["candidates"][0]["content"]["parts"][0]["text"]
            elif self.compatibility == "claude":
                # Claude格式
                text = response["content"][0]["text"]
            else:
                # OpenAI格式
                text = response["choices"][0]["message"]["content"]

            # 尝试解析JSON
            # 移除可能的markdown代码块标记
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            return json.loads(text)

        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"解析API响应失败: {e}")
            logger.debug(f"原始响应: {response}")
            return None

    def test_connection(self) -> bool:
        """
        测试API连接

        Returns:
            连接是否成功
        """
        try:
            # 创建一个简单的测试图像
            from PIL import Image
            import io

            # 创建1x1像素的测试图像
            test_image = Image.new('RGB', (1, 1), color='white')
            img_byte_arr = io.BytesIO()
            test_image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()

            # 转换为base64
            image_data = base64.b64encode(img_byte_arr).decode("utf-8")

            # 发送测试请求
            request_data = self._build_openai_request(
                image_data,
                "这是一个测试，请回复'OK'"
            )

            response = self._send_request(request_data)

            if response:
                logger.info("API连接测试成功")
                return True
            else:
                logger.error("API连接测试失败")
                return False

        except Exception as e:
            logger.error(f"API连接测试异常: {e}")
            return False
