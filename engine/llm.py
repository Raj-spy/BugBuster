"""LLM client with failover chain, retry, and caching.

Chain: GLM-5.3 (NVIDIA) -> Groq Llama 3.3 70B -> Gemini Flash
Timeout: 20s | temperature: 0-0.2 | cache: on
"""

import os

PROVIDERS = [
    {"name": "nvidia-glm", "base_url": os.getenv("NVIDIA_BASE_URL", ""), "model": "glm-5.3"},
    {"name": "groq-llama", "base_url": os.getenv("GROQ_BASE_URL", ""), "model": "llama-3.3-70b"},
    {"name": "gemini-flash", "base_url": os.getenv("GEMINI_BASE_URL", ""), "model": "gemini-flash"},
]


def call_llm(prompt: str, system: str | None = None, temperature: float = 0.1) -> str:
    """Try each provider in order until one succeeds."""
    raise NotImplementedError
