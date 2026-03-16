"""
semantic_matcher.py
-------------------
Groq-based semantic matching with sentence-transformers local fallback.

Works for any industry — technology, healthcare, HR, finance, etc.
"""

import logging
import json
import re
from typing import Optional
from groq import Groq

logger = logging.getLogger(__name__)

# sentence-transformers optional import — deterministic local fallback when Groq unavailable
try:
    from sentence_transformers import SentenceTransformer, util as st_util
    _st_model = SentenceTransformer("all-MiniLM-L6-v2")
    _ST_AVAILABLE = True
    logger.info("✅ sentence-transformers loaded — local semantic fallback active")
except Exception:
    _ST_AVAILABLE = False


class SemanticMatcher:
    def __init__(self, groq_client: Optional[Groq] = None):
        self._groq = groq_client
        logger.info("✅ SemanticMatcher (Groq-powered) ready")

    @property
    def available(self) -> bool:
        return self._groq is not None

    async def similarity(self, text_a: str, text_b: str) -> float:
        """
        Compute conceptual similarity between resume and job description.
        Returns a float in [0.0, 1.0].

        Priority:
        1. Groq LLM (structured rubric, 4 criteria)
        2. sentence-transformers (local, deterministic)
        3. Neutral fallback 0.5
        """
        if self.available:
            score = await self._groq_similarity(text_a, text_b)
            if score is not None:
                return score

        if _ST_AVAILABLE:
            try:
                import asyncio
                def _encode():
                    embs = _st_model.encode(
                        [text_a[:2000], text_b[:2000]], convert_to_tensor=True
                    )
                    return float(st_util.cos_sim(embs[0], embs[1]))
                score = await asyncio.to_thread(_encode)
                return max(0.0, min(1.0, score))
            except Exception as e:
                logger.warning(f"sentence-transformers fallback failed: {e}")

        return 0.5  # neutral fallback

    async def _groq_similarity(self, text_a: str, text_b: str) -> Optional[float]:
        """Groq-based structured semantic scoring. Returns None on failure."""
        prompt = f"""You are an expert technical recruiter. Score how well this candidate fits the job description based on their actual skills and experience — NOT just their job title.

Evaluate these four criteria and produce a SINGLE overall score:
1. Skills coverage — Does the candidate's skill set cover the core technical requirements of the role? (A full-stack developer with front-end skills fits a front-end role well.)
2. Domain relevance — Does the candidate have experience working in the same problem domain the role operates in?
3. Experience level — Does the candidate's years and depth of experience match the seniority implied by the JD?
4. Achievement signals — Does the resume show measurable impact (scale, shipped products, performance gains) relevant to the role?

Score bands:
0.9–1.0: Excellent fit — skills cover the requirements well, right domain and level.
0.7–0.89: Strong fit — covers most requirements, minor gaps in level or one criterion.
0.5–0.69: Moderate fit — relevant background but notable skill or experience gaps.
0.3–0.49: Weak fit — some transferable experience but significant gaps.
0.0–0.29: Poor fit — wrong domain entirely or very early career for a senior role.

Return ONLY valid JSON with a single 'score' key. No markdown, no explanation.

Resume (first 3000 chars):
{text_a[:3000]}

Job Description (first 3000 chars):
{text_b[:3000]}

JSON: {{ "score": 0.0 }}"""

        try:
            import asyncio
            completion = await asyncio.to_thread(
                self._groq.chat.completions.create,
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.0,
            )
            raw = completion.choices[0].message.content or ""
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if m:
                data = json.loads(m.group())
                return float(max(0.0, min(1.0, data.get("score", 0.0))))
        except Exception as e:
            logger.error(f"Groq semantic similarity error: {e}")

        return None
