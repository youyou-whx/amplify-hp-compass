"""HP Compass — DeepSeek LLM 客户端

通过 HTTP 调用 DeepSeek chat completions 接口（OpenAI 兼容格式）。
使用 requests，Python 3.8 兼容。

- 温度：调用 1/2 用 0（近似确定），调用 3 用 0.3（建议文案自然一些）
- response_format json_object 强制 JSON 输出
- 失败自动重试 2 次
"""

from __future__ import annotations

import json
import re
import time
from typing import Any

import requests

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 2.0
TIMEOUT_SECONDS = 120


class LLMError(RuntimeError):
    """LLM 调用失败（网络、鉴权、余额不足等）。"""


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
) -> dict[str, Any]:
    """调用 DeepSeek chat 接口，要求 JSON 输出，返回解析后的 dict。

    重试 2 次；最终失败抛 LLMError。
    """
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = requests.post(
                DEEPSEEK_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": DEEPSEEK_MODEL,
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
                f"DeepSeek API 返回 {response.status_code}: {response.text[:300]}"
            )
            if response.status_code in (401, 402, 403):
                raise last_error
        except LLMError:
            raise
        except Exception as exc:  # 网络异常或 JSON 解析失败
            last_error = exc

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY_SECONDS * (attempt + 1))

    raise LLMError(f"DeepSeek API 调用失败（重试 {MAX_RETRIES} 次后）: {last_error}")
