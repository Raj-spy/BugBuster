"""LLM client with failover chain, retry, and caching.

Chain: GLM-5.3 (NVIDIA) -> Groq Llama 3.3 70B -> Gemini Flash
Timeout: 20s | temperature: 0-0.2 | cache: on
"""

import os
from hashlib import sha256
from pathlib import Path

from openai import OpenAI

def _load_env():
    env_path = Path(".env")
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip("'\"")
                if k and k not in os.environ:
                    os.environ[k] = v


def get_providers():
    _load_env()
    return [
        {
            "name": "groq",
            "base_url": os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
            "model": os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            "key_env": "GROQ_API_KEY",
        },
        {
            "name": "nvidia-glm",
            "base_url": os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"),
            "model": os.getenv("NVIDIA_MODEL", "z-ai/glm-5.3"),
            "key_env": "NVIDIA_API_KEY",
        },
        {
            "name": "gemini-flash",
            "base_url": os.getenv("GEMINI_BASE_URL", ""),
            "model": os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            "key_env": "GEMINI_API_KEY",
        },
    ]


def call_llm(prompt: str, system: str | None = None, temperature: float = 0.1) -> str:
    """Try each provider in order until one succeeds."""
    cache = Path("cache")
    cache.mkdir(exist_ok=True)
    key = sha256((system or "").encode() + prompt.encode()).hexdigest()
    cached = cache / f"{key}.txt"
    if cached.exists():
        return cached.read_text(encoding="utf-8")
    errors = []
    for provider in get_providers():
        api_key = os.getenv(provider["key_env"])
        if not api_key or not provider["base_url"]:
            continue
        try:
            client = OpenAI(api_key=api_key, base_url=provider["base_url"], timeout=20)
            response = client.chat.completions.create(
                model=provider["model"],
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system or "You are a precise security engineer."},
                    {"role": "user", "content": prompt},
                ],
            )
            answer = response.choices[0].message.content or ""
            cached.write_text(answer, encoding="utf-8")
            return answer
        except Exception as exc:  # Provider errors are expected in a failover chain.
            errors.append(f"{provider['name']}: {exc}")
    raise RuntimeError("No configured LLM provider succeeded: " + "; ".join(errors or ["missing API keys/base URLs"]))
