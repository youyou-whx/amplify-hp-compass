"""HP Compass — LLM 客户端（多厂商 OpenAI 兼容接口）

通过 HTTP 调用各厂商 chat completions 接口（OpenAI 兼容格式）。
使用 requests，Python 3.8 兼容。

- 温度：提取/判定类调用用 0（近似确定），文案类用 0.3
- response_format json_object 强制 JSON 输出
- 失败自动重试 2 次
"""

from __future__ import annotations

import json
import re
import time
from typing import Any

import requests

MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 2.0
TIMEOUT_SECONDS = 120


class LLMError(RuntimeError):
    """LLM 调用失败（网络、鉴权、余额不足等）。"""


# ═══════════════════════════════════════════════════════════════
#  厂商配置（OpenAI 兼容端点）
# ═══════════════════════════════════════════════════════════════

PROVIDERS: dict[str, dict[str, Any]] = {
    "DeepSeek": {
        "base_url": "https://api.deepseek.com/chat/completions",
        "models": ["deepseek-chat", "deepseek-reasoner"],
    },
    "OpenAI": {
        "base_url": "https://api.openai.com/v1/chat/completions",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini"],
    },
    "Google Gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "models": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"],
    },
    "Anthropic Claude": {
        "base_url": "https://api.anthropic.com/v1/chat/completions",
        "models": ["claude-opus-4-8", "claude-sonnet-4-6", "claude-haiku-4-5"],
    },
    "Moonshot Kimi": {
        "base_url": "https://api.moonshot.cn/v1/chat/completions",
        "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
    },
    "智谱 GLM": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "models": ["glm-4-plus", "glm-4-air", "glm-4-flash"],
    },
    "阿里通义千问": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "models": ["qwen-plus", "qwen-max", "qwen-turbo"],
    },
    "百度文心": {
        "base_url": "https://qianfan.baidubce.com/v2/chat/completions",
        "models": ["ernie-4.0-8k", "ernie-4.0-turbo-8k", "ernie-3.5-8k"],
    },
    "腾讯混元": {
        "base_url": "https://api.hunyuan.cloud.tencent.com/v1/chat/completions",
        "models": ["hunyuan-turbo", "hunyuan-pro", "hunyuan-lite"],
    },
    "MiniMax": {
        "base_url": "https://api.minimax.chat/v1/text/chatcompletion_v2",
        "models": ["MiniMax-Text-01", "abab6.5s-chat"],
    },
    "讯飞星火": {
        "base_url": "https://spark-api-open.xf-yun.com/v1/chat/completions",
        "models": ["generalv3.5", "generalv4.0", "4.0Ultra"],
    },
    "xAI Grok": {
        "base_url": "https://api.x.ai/v1/chat/completions",
        "models": ["grok-3", "grok-3-mini", "grok-2"],
    },
}

CUSTOM_PROVIDER = "自定义（OpenAI 兼容）"


def provider_names() -> list[str]:
    return list(PROVIDERS.keys()) + [CUSTOM_PROVIDER]


def resolve_endpoint(provider: str, custom_base_url: str = "") -> tuple[str, list[str]]:
    """返回 (endpoint, models)。自定义厂商需提供 base URL。"""
    if provider == CUSTOM_PROVIDER:
        url = (custom_base_url or "").strip().rstrip("/")
        if url:
            url = url + "/chat/completions" if not url.endswith("/chat/completions") else url
        return url, []
    info = PROVIDERS.get(provider, {})
    return info.get("base_url", ""), list(info.get("models", []))


_INVALID_ESCAPE_RE = re.compile(r'\\(?!["\\/bfnrtu])')


def _parse_json_lenient(content: str) -> dict[str, Any]:
    """解析 LLM 返回的 JSON，容忍常见格式瑕疵。

    - 非法转义序列 → 双反斜杠转义为字面量
    - 被 markdown 代码块包裹 → 剥离 ```json ... ```
    """
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 把非法转义序列变成字面反斜杠后重试
        repaired = _INVALID_ESCAPE_RE.sub(r"\\\\", text)
        return json.loads(repaired)


def chat_json(
    messages: list[dict[str, str]],
    api_key: str,
    temperature: float = 0.0,
    endpoint: str = "https://api.deepseek.com/chat/completions",
    model: str = "deepseek-chat",
) -> dict[str, Any]:
    """调用 OpenAI 兼容 chat 接口，要求 JSON 输出，返回解析后的 dict。

    重试 2 次；最终失败抛 LLMError。
    """
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = requests.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "response_format": {"type": "json_object"},
                },
                timeout=TIMEOUT_SECONDS,
            )
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                return _parse_json_lenient(content)
            # 非 200：记录错误，重试（401/402 之类鉴权错误重试无意义，直接抛）
            last_error = LLMError(
                f"API 返回 {response.status_code}: {response.text[:300]}"
            )
            if response.status_code in (401, 402, 403):
                raise last_error
        except LLMError:
            raise
        except Exception as exc:  # 网络异常或 JSON 解析失败
            last_error = exc

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY_SECONDS * (attempt + 1))

    raise LLMError(f"LLM API 调用失败（重试 {MAX_RETRIES} 次后）: {last_error}")
