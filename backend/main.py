import os
import io
import json
import logging
import re
import asyncio
from typing import List, Dict, Set, Optional

import PyPDF2
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from rapidfuzz import fuzz
import groq as groq_module
from groq import Groq
from dotenv import load_dotenv

from skill_extractor import SkillExtractor
from semantic_matcher import SemanticMatcher

# ============================================================================
# CONFIGURATION
# ============================================================================
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Smart Resume Matcher API", version="14.0.0")

# Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.onrender.com"]
)

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "https://smart-resume-matcher-h1kd.onrender.com",
    "https://rion-portfolio.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if os.getenv("ENV") == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Global singletons — initialised on startup
groq_client: Optional[Groq] = None
skill_extractor: Optional[SkillExtractor] = None
semantic_matcher: Optional[SemanticMatcher] = None


# ============================================================================
# STARTUP
# ============================================================================
@app.on_event("startup")
async def startup_event():
    global groq_client, skill_extractor, semantic_matcher

    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        groq_client = Groq(api_key=api_key)
        logger.info("✅ Groq AI initialised")
    else:
        logger.warning("⚠️  No Groq API key — running without AI narrative")

    def _load_nlp():
        global skill_extractor, semantic_matcher
        try:
            skill_extractor = SkillExtractor(groq_client)
        except Exception as e:
            logger.error(f"SkillExtractor init failed: {e}")
        try:
            semantic_matcher = SemanticMatcher(groq_client)
        except Exception as e:
            logger.error(f"SemanticMatcher init failed: {e}")

    await asyncio.to_thread(_load_nlp)


# ============================================================================
# ROOT & HEALTH
# ============================================================================
@app.get("/")
async def root():
    return {
        "message": "Smart Resume Matcher API",
        "version": "14.0.0",
        "status": "running",
        "endpoints": {
            "calculate_match": "POST /api/calculate-match",
            "health": "GET /health",
        },
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "groq_enabled": groq_client is not None,
        "skillner_enabled": skill_extractor is not None,
        "semantic_enabled": semantic_matcher is not None,
    }


# ============================================================================
# PDF EXTRACTION
# ============================================================================
def extract_text_from_pdf(file_content: bytes) -> str:
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return " ".join(text.split())
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        raise HTTPException(status_code=400, detail="Invalid or corrupted PDF file")


# ============================================================================
# GROQ AI — NARRATIVE GENERATION
# ============================================================================
async def generate_ai_analysis(
    resume_text: str,
    job_text: str,
    score: float,
    matched: List[str],
    missing: List[str],
) -> Dict:
    fallback = {"summary": None, "matched_areas": [], "career_tips": []}
    if not groq_client:
        return fallback

    matched_str = ", ".join(matched[:15]) if matched else "none"
    missing_str = ", ".join(missing[:10]) if missing else "none"

    prompt = f"""You are an expert career coach. Analyse this resume-vs-job-description match and respond ONLY with valid JSON.

Resume excerpt (first 1500 chars):
{resume_text[:1500]}

Job Description excerpt (first 1500 chars):
{job_text[:1500]}

Match Score: {score}%
Matched Skills: {matched_str}
Missing Skills: {missing_str}

Return ONLY this JSON (no markdown, no extra text):
{{
  "summary": "2-3 sentence plain-English summary of how well this candidate fits the role",
  "matched_areas": ["Strong area 1", "Strong area 2", "Strong area 3"],
  "career_tips": ["Actionable tip 1", "Actionable tip 2", "Actionable tip 3", "Actionable tip 4"]
}}"""

    try:
        from skill_extractor import _groq_call
        raw = await _groq_call(groq_client, [{"role": "user", "content": prompt}], temperature=0.3)
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
            return {
                "summary": parsed.get("summary"),
                "matched_areas": parsed.get("matched_areas", []),
                "career_tips": parsed.get("career_tips", []),
            }
    except groq_module.RateLimitError:
        raise
    except Exception as e:
        logger.error(f"Groq AI analysis error: {e}")

    return fallback


# ============================================================================
# SCORE LABEL
# ============================================================================
def score_label(score: float) -> str:
    if score >= 80:
        return "Excellent"
    if score >= 55:
        return "Good"
    if score >= 38:
        return "Fair"
    return "Poor"


# ============================================================================
# SKILL MATCHING — RapidFuzz
# ============================================================================
_FUZZY_THRESHOLD = 82  # partial_ratio threshold (0–100)


def _skills_match(skill_a: str, skill_b: str) -> bool:
    """True if two skill strings are similar enough via RapidFuzz partial_ratio."""
    a, b = skill_a.lower().strip(), skill_b.lower().strip()
    return fuzz.partial_ratio(a, b) >= _FUZZY_THRESHOLD


def find_matches(resume_skills: List[str], target_skills: List[str]) -> tuple[List[str], List[str]]:
    """
    Returns (matched_display, unmatched_display).

    Slash-notation skills like "webpack/vite" or "react/angular/vue.js" are treated
    as OR alternatives — satisfied if ANY alternative is found in the resume.
    Uses RapidFuzz partial_ratio for fuzzy matching within each alternative.
    """
    matched = []
    unmatched = []
    resume_lower = [s.lower().strip() for s in resume_skills]

    for ts in target_skills:
        ts_norm = ts.lower().strip()
        # Explicit OR handling: split "webpack/vite" → ["webpack", "vite"]
        alternatives = [alt.strip() for alt in ts_norm.split("/")]
        found = any(
            _skills_match(alt, rs)
            for alt in alternatives
            for rs in resume_lower
        )
        display = ts.title() if ts == ts.lower() else ts
        if found:
            matched.append(display)
        else:
            unmatched.append(display)

    return matched, unmatched


# ============================================================================
# MAIN SCORING ENGINE
# ============================================================================
def calculate_score(
    resume_skills: List[str],
    required: List[str],
    preferred: List[str],
    semantic_sim: float,
) -> Dict:
    matched_req,  missing_req  = find_matches(resume_skills, required)
    matched_pref, missing_pref = find_matches(resume_skills, preferred)

    req_ratio  = len(matched_req)  / len(required)  if required  else 0.0
    pref_ratio = len(matched_pref) / len(preferred) if preferred else 0.0

    required_score  = req_ratio  * 50
    preferred_score = pref_ratio * 15
    semantic_score  = semantic_sim * 35

    total = round(min(required_score + preferred_score + semantic_score, 100.0), 1)

    if required and req_ratio >= 0.8:
        total = round(min(total * 1.05, 100.0), 1)

    suggestions: List[str] = []
    req_pct = req_ratio * 100
    if req_pct >= 90:
        suggestions.append("Excellent match! You meet almost all required skills.")
    elif req_pct >= 70:
        suggestions.append("Strong match! You meet most required skills.")
    elif req_pct >= 50:
        suggestions.append("Moderate match. Focus on the missing required skills.")
    elif semantic_sim >= 0.75:
        suggestions.append("Strong overall experience match. Consider learning the missing tools listed below.")
    else:
        suggestions.append("More skill-building needed for this role.")

    if matched_pref:
        suggestions.append(f"Bonus: {len(matched_pref)} preferred skill(s) matched — that's a plus!")

    if semantic_sim >= 0.75:
        suggestions.append("Your overall experience profile aligns strongly with this role.")
    elif semantic_sim >= 0.5:
        suggestions.append("Your background shows reasonable conceptual alignment with this role.")

    return {
        "score": total,
        "breakdown": {
            "required_match": f"{len(matched_req)}/{len(required)}",
            "preferred_match": f"{len(matched_pref)}/{len(preferred)}",
            "required_pct": round(req_ratio * 100),
            "preferred_pct": round(pref_ratio * 100),
        },
        "matched_skills": sorted(matched_req),
        "matched_preferred": sorted(matched_pref),
        "missing_critical": sorted(missing_req),
        "missing_preferred": sorted(missing_pref),
        "suggestions": suggestions,
    }


# ============================================================================
# API ENDPOINT
# ============================================================================
@app.post("/api/calculate-match")
async def calculate_match(
    file: UploadFile = File(...),
    job_description: str = Form(...),
):
    """Main endpoint: resume PDF + job description → match analysis."""

    # 1. Extract resume text
    resume_content = await file.read()
    resume_text = extract_text_from_pdf(resume_content)

    if len(resume_text) < 100:
        raise HTTPException(status_code=400, detail="Resume text too short or unreadable")

    try:
        # 2. Detect domain first (fast single call) — drives category generation
        domain = "general"
        if skill_extractor:
            domain = await skill_extractor.detect_domain(job_description)
            logger.info(f"Detected domain: {domain}")

        # 3. Parallel: resume skill extraction + job extraction+categorisation + semantic similarity
        async def extract_resume():
            if skill_extractor:
                return await skill_extractor.extract_resume(resume_text, domain=domain)
            return []

        async def extract_job():
            if skill_extractor:
                return await skill_extractor.extract_job_with_categories(job_description, domain=domain)
            return {"required": [], "preferred": [], "categories": {}}

        async def semantic_sim():
            if semantic_matcher and semantic_matcher.available:
                return await semantic_matcher.similarity(resume_text, job_description)
            return 0.0

        resume_skills, job_reqs, sem_score = await asyncio.gather(
            extract_resume(), extract_job(), semantic_sim()
        )

    except groq_module.RateLimitError:
        raise HTTPException(
            status_code=429,
            detail="AI service rate limit reached. Please wait a moment and try again.",
        )

    required  = job_reqs["required"]
    preferred = job_reqs["preferred"]
    categories = job_reqs["categories"]

    logger.info(f"Resume skills ({len(resume_skills)}): {resume_skills[:10]}")
    logger.info(f"Required ({len(required)}): {required[:10]}")
    logger.info(f"Preferred ({len(preferred)}): {preferred[:5]}")
    logger.info(f"Semantic similarity: {sem_score:.3f}")

    # 3. Calculate blended score
    result = calculate_score(resume_skills, required, preferred, sem_score)

    # 4. Per-category scores (uses Groq-provided category map)
    # Only include categories with at least one matched skill (score > 0) to avoid noise.
    category_scores: Dict[str, int] = {}
    if skill_extractor:
        raw_category_scores = await asyncio.to_thread(
            skill_extractor.compute_category_scores_from_map,
            resume_skills,
            required,
            categories,
        )
        category_scores = {cat: score for cat, score in raw_category_scores.items() if score > 0}

    # 5. Groq narrative (summary, matched_areas, career_tips)
    try:
        ai_analysis = await generate_ai_analysis(
            resume_text,
            job_description,
            result["score"],
            result["matched_skills"],
            result["missing_critical"],
        )
    except groq_module.RateLimitError:
        raise HTTPException(
            status_code=429,
            detail="AI service rate limit reached. Please wait a moment and try again.",
        )

    # 6. Score label
    label = score_label(result["score"])

    logger.info(f"Final score: {result['score']}% ({label})")

    return {
        **result,
        "score_label": label,
        "semantic_similarity": round(sem_score * 100, 1),
        "category_scores": category_scores,
        "ai_analysis": ai_analysis,
        "domain": domain,
    }
