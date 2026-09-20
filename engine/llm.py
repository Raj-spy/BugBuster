"""LLM client with failover chain, retry, and caching.

Chain: GLM-5.3 (NVIDIA) -> Groq Llama 3.3 70B -> Gemini Flash
Timeout: 20s | temperature: 0-0.2 | cache: on
"""

import os
from hashlib import sha256
from pathlib import Path

from openai import OpenAI

PROVIDERS = [
    {"name": "nvidia-glm", "base_url": os.getenv("NVIDIA_BASE_URL", ""), "model": "glm-5.3"},
    {"name": "groq-llama", "base_url": os.getenv("GROQ_BASE_URL", ""), "model": "llama-3.3-70b"},
    {"name": "gemini-flash", "base_url": os.getenv("GEMINI_BASE_URL", ""), "model": "gemini-flash"},
]


def call_llm(prompt: str, system: str | None = None, temperature: float = 0.1) -> str:
    """Try each provider in order until one succeeds."""
    cache = Path("cache")
    cache.mkdir(exist_ok=True)
    key = sha256((system or "") .encode() + prompt.encode()).hexdigest()
    cached = cache / f"{key}.txt"
    if cached.exists():
        return cached.read_text(encoding="utf-8")
    errors = []
    for provider in PROVIDERS:
        api_key = os.getenv(f"{provider['name'].split('-')[0].upper()}_API_KEY")
        if not api_key or not provider["base_url"]:
            continue
        try:
            client = OpenAI(api_key=api_key, base_url=provider["base_url"], timeout=20)
            response = client.chat.completions.create(model=provider["model"], temperature=temperature,
                messages=[{"role": "system", "content": system or "You are a precise security engineer."},
                          {"role": "user", "content": prompt}])
            answer = response.choices[0].message.content or ""
            cached.write_text(answer, encoding="utf-8")
            return answer
        except Exception as exc:  # Provider errors are expected in a failover chain.
            errors.append(f"{provider['name']}: {exc}")
    raise RuntimeError("No configured LLM provider succeeded: " + "; ".join(errors or ["missing API keys/base URLs"]))
