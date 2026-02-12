"""
LLM service with multi-provider support.
Supports Google Gemini and OpenAI with automatic fallback.
"""

from abc import ABC, abstractmethod

from loguru import logger

from app.config import settings


SYSTEM_PROMPT = """You are a knowledgeable assistant that answers questions based ONLY on the provided context.

Rules:
1. Answer the question using ONLY the information from the context below.
2. If the context does not contain enough information to answer the question, say so clearly.
3. Be precise and concise in your answers.
4. When possible, quote the relevant parts from the context.
5. Answer in the same language as the question."""

USER_PROMPT_TEMPLATE = """Context:
{context}

---

Question: {question}

Provide a precise answer based on the context above. Include relevant quotes as references."""


def _build_context(context_chunks: list[dict]) -> str:
    """Build a context string from retrieved chunks."""
    parts = []
    for i, chunk in enumerate(context_chunks, 1):
        source = chunk["metadata"].get("source", "unknown")
        page = chunk["metadata"].get("page", "?")
        parts.append(
            f"[Source {i}: {source}, Page {page}]\n{chunk['text']}"
        )
    return "\n\n".join(parts)


# ── Provider Implementations ────────────────────────────────────────────────


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    name: str = "base"

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a response from the LLM."""
        ...

    def is_available(self) -> bool:
        """Check if this provider is configured."""
        return True


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider."""

    name = "gemini"

    def __init__(self):
        self._client = None

    def is_available(self) -> bool:
        return bool(settings.gemini_api_key)

    def _get_client(self):
        if self._client is None:
            from google import genai

            self._client = genai.Client(api_key=settings.gemini_api_key)
        return self._client

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        from google import genai

        client = self._get_client()
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=user_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=settings.llm_temperature,
                max_output_tokens=settings.llm_max_tokens,
            ),
        )
        return response.text.strip()


class OpenAIProvider(LLMProvider):
    """OpenAI GPT LLM provider."""

    name = "openai"

    def __init__(self):
        self._client = None

    def is_available(self) -> bool:
        return bool(settings.openai_api_key)

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(api_key=settings.openai_api_key)
        return self._client

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        client = self._get_client()
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )
        return response.choices[0].message.content.strip()


# ── Main LLM Service ────────────────────────────────────────────────────────


class LLMService:
    """
    Multi-provider LLM service with fallback.

    Tries the primary provider first. If it fails, falls back to the
    secondary provider automatically.
    """

    def __init__(self):
        self._providers: list[LLMProvider] = []
        self._init_providers()

    def _init_providers(self):
        """Initialize available providers in priority order."""
        candidates = [
            GeminiProvider(),
            OpenAIProvider(),
        ]
        self._providers = [p for p in candidates if p.is_available()]

        if not self._providers:
            logger.warning(
                "No LLM providers configured! "
                "Set GEMINI_API_KEY or OPENAI_API_KEY in .env"
            )
        else:
            names = [p.name for p in self._providers]
            logger.info(f"LLM providers available: {names}")

    def generate_answer(
        self,
        question: str,
        context_chunks: list[dict],
        provider: str | None = None,
    ) -> dict:
        """
        Generate an answer using available LLM providers with fallback.

        Args:
            question: User's question.
            context_chunks: Retrieved chunks from vector store.
            provider: Optional provider name ('gemini' or 'openai').
                      If set, only that provider is used (no fallback).

        Returns:
            Dict with 'answer' and 'references' keys.
        """
        if not context_chunks:
            return {
                "answer": (
                    "No relevant documents found to answer this question. "
                    "Please upload relevant documents first."
                ),
                "references": [],
            }

        if not self._providers:
            raise RuntimeError(
                "No LLM providers configured. "
                "Set GEMINI_API_KEY or OPENAI_API_KEY in .env"
            )

        # Determine which providers to try
        if provider:
            providers = [
                p for p in self._providers if p.name == provider
            ]
            if not providers:
                raise RuntimeError(
                    f"Provider '{provider}' is not available. "
                    f"Check that its API key is set in .env"
                )
        else:
            providers = self._providers

        # Build prompt
        context = _build_context(context_chunks)
        user_prompt = USER_PROMPT_TEMPLATE.format(
            context=context, question=question
        )

        # Try each provider with fallback
        last_error = None
        for provider in providers:
            try:
                logger.info(
                    f"Trying LLM provider: {provider.name}"
                )
                answer = provider.generate(SYSTEM_PROMPT, user_prompt)
                references = [c["text"] for c in context_chunks]

                logger.info(
                    f"Answer generated via {provider.name}"
                )
                return {
                    "answer": answer,
                    "references": references,
                }

            except Exception as e:
                logger.warning(
                    f"Provider {provider.name} failed: {e}"
                )
                last_error = e
                continue

        raise RuntimeError(
            f"All LLM providers failed. Last error: {last_error}"
        )
