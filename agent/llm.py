"""
Universal LLM Client supporting:
- Ollama native streaming & tool calling
- OpenAI-compatible endpoints (LM Studio, OpenRouter, DeepSeek, OpenAI, Groq, vLLM)
- Auto-detection of local servers (Ollama on 11434, LM Studio on 1234, vLLM on 8000, LocalAI on 8080)
- Real-time token usage & financial cost calculation ($ per 1M tokens)
- Real-time thinking/reasoning stream & tool calling
"""
import json
from typing import Any, Callable, Dict, List, Optional
import httpx

from agent.config import OLLAMA_URL, DEFAULT_MODEL


class ModelConfig:
    def __init__(
        self,
        id: str,
        name: str,
        provider: str,  # "ollama" or "openai_compatible"
        base_url: str,
        model_name: str,
        api_key: Optional[str] = None,
        input_cost_per_1m: float = 0.0,
        output_cost_per_1m: float = 0.0,
        is_local: bool = True,
    ):
        self.id = id
        self.name = name
        self.provider = provider
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.api_key = api_key
        self.input_cost_per_1m = input_cost_per_1m
        self.output_cost_per_1m = output_cost_per_1m
        self.is_local = is_local

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "base_url": self.base_url,
            "model_name": self.model_name,
            "api_key": "***" if self.api_key else None,
            "input_cost_per_1m": self.input_cost_per_1m,
            "output_cost_per_1m": self.output_cost_per_1m,
            "is_local": self.is_local,
        }


def detect_local_providers() -> List[ModelConfig]:
    """
    Scans local ports to discover active LLM servers:
    - Ollama on 11434
    - LM Studio on 1234
    - vLLM on 8000
    - LocalAI on 8080
    """
    discovered: List[ModelConfig] = []

    # 1. Check Ollama (11434)
    try:
        with httpx.Client(timeout=1.5) as client:
            resp = client.get("http://127.0.0.1:11434/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                for m in data.get("models", []):
                    m_name = m.get("name", "")
                    if m_name:
                        discovered.append(
                            ModelConfig(
                                id=f"ollama:{m_name}",
                                name=f"{m_name} (Ollama)",
                                provider="ollama",
                                base_url="http://127.0.0.1:11434",
                                model_name=m_name,
                                input_cost_per_1m=0.0,
                                output_cost_per_1m=0.0,
                                is_local=True,
                            )
                        )
    except Exception:
        pass

    # 2. Check LM Studio (1234)
    try:
        with httpx.Client(timeout=1.5) as client:
            resp = client.get("http://127.0.0.1:1234/v1/models")
            if resp.status_code == 200:
                data = resp.json()
                for m in data.get("data", []):
                    m_id = m.get("id", "")
                    if m_id:
                        discovered.append(
                            ModelConfig(
                                id=f"lmstudio:{m_id}",
                                name=f"{m_id} (LM Studio)",
                                provider="openai_compatible",
                                base_url="http://127.0.0.1:1234/v1",
                                model_name=m_id,
                                input_cost_per_1m=0.0,
                                output_cost_per_1m=0.0,
                                is_local=True,
                            )
                        )
    except Exception:
        pass

    # 3. Check vLLM / LocalAI (8000)
    try:
        with httpx.Client(timeout=1.5) as client:
            resp = client.get("http://127.0.0.1:8000/v1/models")
            if resp.status_code == 200:
                data = resp.json()
                for m in data.get("data", []):
                    m_id = m.get("id", "")
                    if m_id:
                        discovered.append(
                            ModelConfig(
                                id=f"vllm:{m_id}",
                                name=f"{m_id} (vLLM)",
                                provider="openai_compatible",
                                base_url="http://127.0.0.1:8000/v1",
                                model_name=m_id,
                                input_cost_per_1m=0.0,
                                output_cost_per_1m=0.0,
                                is_local=True,
                            )
                        )
    except Exception:
        pass

    return discovered


class UniversalLLMClient:
    def __init__(
        self,
        base_url: str = OLLAMA_URL,
        model: str = DEFAULT_MODEL,
        provider: str = "ollama",
        api_key: Optional[str] = None,
        input_cost_per_1m: float = 0.0,
        output_cost_per_1m: float = 0.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.provider = provider
        self.api_key = api_key
        self.input_cost_per_1m = input_cost_per_1m
        self.output_cost_per_1m = output_cost_per_1m

    def set_config(
        self,
        model: str,
        base_url: Optional[str] = None,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        input_cost_per_1m: Optional[float] = None,
        output_cost_per_1m: Optional[float] = None,
    ):
        self.model = model
        if base_url:
            self.base_url = base_url.rstrip("/")
        if provider:
            self.provider = provider
        if api_key is not None:
            self.api_key = api_key
        if input_cost_per_1m is not None:
            self.input_cost_per_1m = input_cost_per_1m
        if output_cost_per_1m is not None:
            self.output_cost_per_1m = output_cost_per_1m

    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        cost = (prompt_tokens / 1_000_000.0 * self.input_cost_per_1m) + (
            completion_tokens / 1_000_000.0 * self.output_cost_per_1m
        )
        return round(cost, 6)

    def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        on_thinking_chunk: Optional[Callable[[str], None]] = None,
        on_content_chunk: Optional[Callable[[str], None]] = None,
        temperature: float = 0.2,
        timeout: float = 180.0,
    ) -> Dict[str, Any]:
        if self.provider == "openai_compatible":
            return self._chat_openai_stream(
                messages, tools, on_thinking_chunk, on_content_chunk, temperature, timeout
            )
        else:
            return self._chat_ollama_stream(
                messages, tools, on_thinking_chunk, on_content_chunk, temperature, timeout
            )

    def _chat_ollama_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        on_thinking_chunk: Optional[Callable[[str], None]] = None,
        on_content_chunk: Optional[Callable[[str], None]] = None,
        temperature: float = 0.2,
        timeout: float = 180.0,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "keep_alive": -1,
            "options": {
                "temperature": temperature,
            },
        }
        if tools:
            payload["tools"] = tools

        url = f"{self.base_url}/api/chat"
        accumulated_content = []
        accumulated_thinking = []
        accumulated_tool_calls: List[Dict[str, Any]] = []
        last_raw = {}
        prompt_tokens = 0
        completion_tokens = 0

        try:
            with httpx.Client(timeout=timeout) as client:
                with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            last_raw = data
                            msg = data.get("message", {})

                            if "prompt_eval_count" in data:
                                prompt_tokens = data["prompt_eval_count"]
                            if "eval_count" in data:
                                completion_tokens = data["eval_count"]

                            # Streaming thinking
                            th_delta = msg.get("thinking", "")
                            if th_delta:
                                accumulated_thinking.append(th_delta)
                                if on_thinking_chunk:
                                    on_thinking_chunk(th_delta)

                            # Streaming content
                            content_delta = msg.get("content", "")
                            if content_delta:
                                accumulated_content.append(content_delta)
                                if on_content_chunk:
                                    on_content_chunk(content_delta)

                            # Tool calls
                            tcs = msg.get("tool_calls", None)
                            if tcs:
                                for tc in tcs:
                                    fn = tc.get("function", {})
                                    fn_name = fn.get("name")
                                    fn_args = fn.get("arguments", {})
                                    if isinstance(fn_args, str):
                                        try:
                                            fn_args = json.loads(fn_args)
                                        except Exception:
                                            pass
                                    accumulated_tool_calls.append(
                                        {
                                            "id": tc.get("id", f"call_{fn_name}"),
                                            "function": {
                                                "name": fn_name,
                                                "arguments": fn_args,
                                            },
                                        }
                                    )
                        except Exception:
                            continue

            full_content = "".join(accumulated_content)
            full_thinking = "".join(accumulated_thinking)

            # Fallback token estimation if server didn't report
            if prompt_tokens == 0:
                prompt_tokens = sum(len(m.get("content", "")) // 4 for m in messages)
            if completion_tokens == 0:
                completion_tokens = len(full_content) // 4 + len(full_thinking) // 4

            cost = self.calculate_cost(prompt_tokens, completion_tokens)

            return {
                "content": full_content,
                "thinking": full_thinking if full_thinking else None,
                "tool_calls": accumulated_tool_calls if accumulated_tool_calls else None,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "cost_usd": cost,
                "raw": last_raw,
            }

        except httpx.ConnectError:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. Make sure server is running."
            )
        except Exception as e:
            raise RuntimeError(f"Ollama chat error: {str(e)}")

    def _chat_openai_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        on_thinking_chunk: Optional[Callable[[str], None]] = None,
        on_content_chunk: Optional[Callable[[str], None]] = None,
        temperature: float = 0.2,
        timeout: float = 180.0,
    ) -> Dict[str, Any]:
        """
        OpenAI-compatible chat completion streaming for:
        LM Studio, OpenRouter, DeepSeek, OpenAI, Groq, vLLM
        """
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # Standard OpenAI tools payload format
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "stream_options": {"include_usage": True},
            "temperature": temperature,
        }
        if tools:
            # Format tools as OpenAI type: "function"
            openai_tools = []
            for t in tools:
                if "type" in t and "function" in t:
                    openai_tools.append(t)
                elif "function" in t:
                    openai_tools.append({"type": "function", "function": t["function"]})
                else:
                    openai_tools.append({"type": "function", "function": t})
            payload["tools"] = openai_tools

        url = f"{self.base_url}/chat/completions" if not self.base_url.endswith("/chat/completions") else self.base_url

        accumulated_content = []
        accumulated_thinking = []
        tool_call_map: Dict[int, Dict[str, Any]] = {}
        prompt_tokens = 0
        completion_tokens = 0
        last_raw = {}

        try:
            with httpx.Client(timeout=timeout) as client:
                with client.stream("POST", url, json=payload, headers=headers) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            line = line[6:].strip()
                        if line == "[DONE]":
                            break

                        try:
                            data = json.loads(line)
                            last_raw = data

                            # Check for usage
                            if "usage" in data and data["usage"]:
                                u = data["usage"]
                                prompt_tokens = u.get("prompt_tokens", prompt_tokens)
                                completion_tokens = u.get("completion_tokens", completion_tokens)

                            choices = data.get("choices", [])
                            if not choices:
                                continue
                            delta = choices[0].get("delta", {})

                            # Reasoning content (DeepSeek / OpenRouter thinking)
                            reasoning = delta.get("reasoning_content", "") or delta.get("reasoning", "")
                            if reasoning:
                                accumulated_thinking.append(reasoning)
                                if on_thinking_chunk:
                                    on_thinking_chunk(reasoning)

                            # Standard content
                            content = delta.get("content", "")
                            if content:
                                accumulated_content.append(content)
                                if on_content_chunk:
                                    on_content_chunk(content)

                            # Tool calls streaming
                            tcs = delta.get("tool_calls", [])
                            for tc in tcs:
                                idx = tc.get("index", 0)
                                if idx not in tool_call_map:
                                    tool_call_map[idx] = {
                                        "id": tc.get("id", f"call_{idx}"),
                                        "name": "",
                                        "arguments": "",
                                    }
                                if tc.get("id"):
                                    tool_call_map[idx]["id"] = tc["id"]
                                fn = tc.get("function", {})
                                if fn.get("name"):
                                    tool_call_map[idx]["name"] += fn["name"]
                                if fn.get("arguments"):
                                    tool_call_map[idx]["arguments"] += fn["arguments"]

                        except Exception:
                            continue

            full_content = "".join(accumulated_content)
            full_thinking = "".join(accumulated_thinking)

            # Build final tool calls list
            accumulated_tool_calls = []
            for idx, tc_data in sorted(tool_call_map.items()):
                fn_name = tc_data["name"]
                args_str = tc_data["arguments"]
                try:
                    args_parsed = json.loads(args_str) if args_str else {}
                except Exception:
                    args_parsed = {}
                accumulated_tool_calls.append(
                    {
                        "id": tc_data["id"],
                        "function": {
                            "name": fn_name,
                            "arguments": args_parsed,
                        },
                    }
                )

            if prompt_tokens == 0:
                prompt_tokens = sum(len(m.get("content", "")) // 4 for m in messages)
            if completion_tokens == 0:
                completion_tokens = len(full_content) // 4 + len(full_thinking) // 4

            cost = self.calculate_cost(prompt_tokens, completion_tokens)

            return {
                "content": full_content,
                "thinking": full_thinking if full_thinking else None,
                "tool_calls": accumulated_tool_calls if accumulated_tool_calls else None,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "cost_usd": cost,
                "raw": last_raw,
            }

        except httpx.ConnectError:
            raise ConnectionError(
                f"Cannot connect to OpenAI-compatible server at {self.base_url}."
            )
        except Exception as e:
            raise RuntimeError(f"OpenAI-compatible chat error: {str(e)}")

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
        timeout: float = 120.0,
    ) -> Dict[str, Any]:
        return self.chat_stream(
            messages=messages,
            tools=tools,
            temperature=temperature,
            timeout=timeout,
        )

    def list_models(self) -> List[str]:
        if self.provider == "openai_compatible":
            try:
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                with httpx.Client(timeout=8.0) as client:
                    resp = client.get(f"{self.base_url}/models", headers=headers)
                    if resp.status_code == 200:
                        return [m.get("id", "") for m in resp.json().get("data", [])]
            except Exception:
                pass
            return [self.model]
        else:
            try:
                with httpx.Client(timeout=8.0) as client:
                    resp = client.get(f"{self.base_url}/api/tags")
                    if resp.status_code == 200:
                        return [m.get("name", "") for m in resp.json().get("models", [])]
            except Exception:
                pass
            return [self.model]


# Backwards compatibility alias
OllamaClient = UniversalLLMClient
