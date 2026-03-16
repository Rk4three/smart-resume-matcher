"""
semantic_matcher.py
-------------------
Groq-based semantic matching.

Replaces the local sentence-transformers setup with a Groq-powered
semantic similarity assessment. This is much faster than running local
embeddings on Python 3.14 and provides excellent conceptual alignment scores.
"""

import logging
import json
import re
from typing import Optional
from groq import Groq

logger = logging.getLogger(__name__)

class SemanticMatcher:
    def __init__(self, groq_client: Optional[Groq] = None):
        self._groq = groq_client
        logger.info("✅ SemanticMatcher (Groq-powered) ready")

    @property
    def available(self) -> bool:
        return self._groq is not None

    async def similarity(self, text_a: str, text_b: str) -> float:
        """
        Compute conceptual similarity using Groq.
        Returns a float in [0.0, 1.0].
        """
        if not self.available:
            return 0.0

        prompt = f"""Assess the semantic similarity between this Resume and Job Description.
Consider conceptual alignment, experience level, and domain expertise.
Return ONLY a valid JSON object with a 'score' between 0 and 1.

Resume:
{text_a[:1500]}

Job Description:
{text_b[:1500]}

JSON:
{{ "score": 0.0 }}"""

        try:
            import asyncio
            completion = await asyncio.to_thread(
                self._groq.chat.completions.create,
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.0,
            )
            raw = completion.choices[0].message.content or ""
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                data = json.loads(match.group())
                return float(max(0.0, min(1.0, data.get("score", 0.0))))
        except Exception as e:
            logger.error(f"Groq semantic similarity error: {e}")
        
        return 0.5  # Neutral fallback
