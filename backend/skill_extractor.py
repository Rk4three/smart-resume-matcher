"""
skill_extractor.py
------------------
Groq-based skill extraction with keyword fallback.
"""

import asyncio
import logging
import json
import re
from typing import List, Dict, Optional

import groq as groq_module
from groq import Groq

logger = logging.getLogger(__name__)

# Fallback-only: used when Groq is unavailable
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "frontend": [
        "javascript", "typescript", "react", "vue", "angular", "svelte",
        "html", "css", "sass", "scss", "tailwind", "bootstrap", "material ui",
        "next.js", "nuxt", "vite", "webpack", "ui/ux", "figma", "responsive design",
    ],
    "backend": [
        "python", "node.js", "express", "fastapi", "django", "flask",
        "java", "spring", "spring boot", "ruby on rails", "golang", "php", "laravel",
        "c#", ".net", "asp.net", "microservices", "rest api", "graphql", "grpc",
    ],
    "database": [
        "sql", "postgresql", "mysql", "mongodb", "redis", "nosql",
        "sqlite", "supabase", "firebase", "database design", "orm",
    ],
    "devops": [
        "docker", "kubernetes", "aws", "azure", "gcp", "google cloud",
        "ci/cd", "jenkins", "github actions", "gitlab ci", "terraform",
        "ansible", "linux", "nginx", "load balancing",
    ],
    "data_ai": [
        "machine learning", "data science", "nlp", "ai", "llm",
        "pandas", "numpy", "pytorch", "tensorflow", "scikit-learn",
        "langchain", "data analysis", "deep learning",
    ],
    "methodologies": [
        "agile", "scrum", "kanban", "tdd", "bdd", "oop",
        "design patterns", "solid", "mvc", "serverless",
    ],
    "tools": [
        "git", "github", "gitlab", "jira", "postman", "vscode",
        "testing", "npm", "yarn", "jest", "cypress", "pytest",
    ],
}


async def _groq_call(groq_client: Groq, messages: list, temperature: float = 0.1) -> str:
    """
    Run a Groq chat completion with one automatic retry on RateLimitError.
    Raises groq_module.RateLimitError if it fails twice.
    """
    for attempt in range(2):
        try:
            completion = await asyncio.to_thread(
                groq_client.chat.completions.create,
                messages=messages,
                model="llama-3.1-8b-instant",
                temperature=temperature,
            )
            return completion.choices[0].message.content or ""
        except groq_module.RateLimitError:
            if attempt == 0:
                logger.warning("Groq rate limit hit — retrying in 2s…")
                await asyncio.sleep(2)
            else:
                raise  # re-raise on second failure


def _keyword_fallback(text: str) -> List[str]:
    """Extract skills from text using CATEGORY_KEYWORDS when Groq is unavailable."""
    text_lower = text.lower()
    found: List[str] = []
    seen: set = set()
    for keywords in CATEGORY_KEYWORDS.values():
        for kw in keywords:
            if kw not in seen and kw in text_lower:
                found.append(kw)
                seen.add(kw)
    return found


class SkillExtractor:
    def __init__(self, groq_client: Optional[Groq] = None):
        self._groq = groq_client
        logger.info("✅ SkillExtractor (Groq-powered) ready")

    async def extract_resume(self, text: str) -> List[str]:
        """
        Extract technical skills from resume text.
        Falls back to keyword scanning if Groq is unavailable.
        """
        if not self._groq:
            return _keyword_fallback(text)

        prompt = f"""Extract ALL technical skills, tools, and methodologies from this resume text.
Return ONLY a valid JSON array of strings. Do not include soft skills.

Rules:
- Include skills explicitly listed in a Skills section.
- Also include skills DEMONSTRATED through work experience bullets, even if not in the Skills section.
  Examples: "rebuilt app across multiple devices" → include "responsive design"; "optimized for 600k+ requests/month" → include "web performance optimization"; "integrated third-party APIs" → include "api integration"; "automated internal processes" → include "automation".
- Do NOT include generic business skills (communication, teamwork, leadership).

Text:
{text[:5000]}"""

        try:
            raw = await _groq_call(self._groq, [{"role": "user", "content": prompt}], temperature=0.1)
            match = re.search(r"\[.*\]", raw, re.DOTALL)
            if match:
                return [s.lower().strip() for s in json.loads(match.group())]
        except groq_module.RateLimitError:
            raise  # handled by caller
        except Exception as e:
            logger.error(f"Groq resume skill extraction error: {e}")

        return _keyword_fallback(text)

    async def extract_job_with_categories(self, job_text: str) -> Dict:
        """
        Single Groq call that extracts job skills, splits them into required/preferred,
        AND returns each skill's domain category.

        Returns:
            {
              "required":   ["skill1", ...],
              "preferred":  ["skill2", ...],
              "categories": {"skill1": "backend", "skill2": "frontend", ...}
            }
        """
        fallback = {"required": [], "preferred": [], "categories": {}}
        if not self._groq:
            skills = _keyword_fallback(job_text)
            fallback["required"] = skills
            fallback["categories"] = {s: self._categorize_one(s) for s in skills}
            return fallback

        prompt = f"""Analyse this job description. Extract every technical skill, tool, and methodology mentioned.
Classify each skill as REQUIRED or PREFERRED using these strict rules:

REQUIRED: A skill is required if it appears in a Requirements, Qualifications, or Technical Skills section.
  - If the JD lists OR alternatives for the SAME requirement (e.g. "React, Angular, or Vue.js"), emit them as ONE entry using slash notation: "react/angular/vue.js". Do NOT emit them as separate entries.
  - Apply the same rule to equivalent tools for the same purpose (e.g. "Figma, Sketch, or Adobe XD" → "figma/sketch/adobe xd"; "Webpack or Vite" → "webpack/vite").
  - This keeps the required list concise — one slot per distinct requirement, not one slot per alternative.

PREFERRED: A skill is preferred ONLY if the JD explicitly uses words like "nice to have", "bonus", "plus", "preferred", or groups them under a "Preferred Skills" heading.

Also assign each skill a domain category from this list ONLY:
  frontend, backend, database, devops, data_ai, methodologies, tools
For slash-notation skills, use the category of the first option.

Return ONLY valid JSON — no markdown, no extra text:
{{
  "required":   ["skill1", "react/angular/vue.js"],
  "preferred":  ["skill3"],
  "categories": {{"skill1": "backend", "react/angular/vue.js": "frontend", "skill3": "devops"}}
}}

Job Description:
{job_text[:5000]}"""

        try:
            raw = await _groq_call(self._groq, [{"role": "user", "content": prompt}], temperature=0.1)
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
                required = [s.lower().strip() for s in parsed.get("required", [])]
                preferred = [s.lower().strip() for s in parsed.get("preferred", [])]
                categories = {k.lower().strip(): v for k, v in parsed.get("categories", {}).items()}

                # Ensure every extracted skill is assigned somewhere
                all_classified = set(required + preferred)
                for s in list(categories.keys()):
                    if s not in all_classified:
                        required.append(s)

                return {
                    "required": list(dict.fromkeys(required)),
                    "preferred": list(dict.fromkeys(preferred)),
                    "categories": categories,
                }
        except groq_module.RateLimitError:
            raise
        except Exception as e:
            logger.error(f"Groq job extraction error: {e}")

        # Fallback: keyword scan, treat all as required
        skills = _keyword_fallback(job_text)
        return {
            "required": skills,
            "preferred": [],
            "categories": {s: self._categorize_one(s) for s in skills},
        }

    def _categorize_one(self, skill: str) -> str:
        """Assign a single skill to a category using CATEGORY_KEYWORDS fallback."""
        skill_lower = skill.lower()
        for cat, keywords in CATEGORY_KEYWORDS.items():
            if any(kw in skill_lower or skill_lower in kw for kw in keywords):
                return cat
        return "tools"

    def compute_category_scores_from_map(
        self,
        resume_skills: List[str],
        required_skills: List[str],
        categories: Dict[str, str],
    ) -> Dict[str, int]:
        """
        Compute per-category match scores using the Groq-provided category map.
        Falls back to CATEGORY_KEYWORDS for skills not in the map.
        """
        # Group required skills by category
        required_by_cat: Dict[str, List[str]] = {}
        for skill in required_skills:
            cat = categories.get(skill.lower(), self._categorize_one(skill))
            required_by_cat.setdefault(cat, []).append(skill)

        # Group resume skills by category
        resume_by_cat: Dict[str, List[str]] = {}
        for skill in resume_skills:
            cat = categories.get(skill.lower(), self._categorize_one(skill))
            resume_by_cat.setdefault(cat, []).append(skill)

        scores: Dict[str, int] = {}
        for cat, req_list in required_by_cat.items():
            res_list = resume_by_cat.get(cat, [])
            matched = sum(
                1 for r in req_list
                if any(r in rs or rs in r for rs in res_list)
            )
            scores[cat] = round((matched / len(req_list)) * 100)

        return scores
