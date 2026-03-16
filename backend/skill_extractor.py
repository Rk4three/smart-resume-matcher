"""
skill_extractor.py
------------------
Groq-based skill extraction with keyword fallback.
Supports any industry — technology, healthcare, HR, finance, legal, etc.
"""

import asyncio
import logging
import json
import re
from typing import List, Dict, Optional

import groq as groq_module
from groq import Groq

logger = logging.getLogger(__name__)

# SkillNer optional import — replaces keyword fallback when available
try:
    import spacy
    from skillner import SkillExtractor as _SkillNer
    _nlp = spacy.load("en_core_web_lg")
    _skill_ner = _SkillNer(nlp=_nlp)
    _SKILLNER_AVAILABLE = True
    logger.info("✅ SkillNer (spaCy) loaded — multi-domain offline fallback active")
except Exception:
    _SKILLNER_AVAILABLE = False

# Fallback keyword list — kept as last resort when both Groq and SkillNer are unavailable.
# Intentionally broad (not tech-only) so it degrades gracefully for any domain.
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    # Technology
    "programming": [
        "javascript", "typescript", "python", "java", "c#", "php", "ruby", "golang",
        "html", "css", "sass", "sql",
    ],
    "frameworks": [
        "react", "vue", "angular", "svelte", "next.js", "node.js", "express",
        "django", "flask", "fastapi", "spring", "laravel", "rails",
    ],
    "devops": [
        "docker", "kubernetes", "aws", "azure", "gcp", "ci/cd", "git", "linux",
    ],
    # Healthcare
    "clinical": [
        "patient care", "clinical trials", "diagnosis", "treatment", "surgery",
        "ehr", "emr", "hipaa", "cpr", "bls", "acls", "icd-10",
    ],
    "medical_certifications": [
        "md", "rn", "lpn", "np", "pa", "cna", "usmle", "board certified",
    ],
    # Human Resources
    "hr": [
        "recruitment", "talent acquisition", "onboarding", "hris", "workday",
        "bamboohr", "adp", "payroll", "compensation", "benefits", "shrm",
        "performance management", "employee relations",
    ],
    # Finance
    "finance": [
        "accounting", "financial analysis", "gaap", "ifrs", "excel", "bloomberg",
        "cfa", "cpa", "auditing", "tax", "forecasting", "budgeting",
    ],
    # General professional
    "methodologies": [
        "agile", "scrum", "kanban", "pmp", "six sigma", "lean", "tdd",
    ],
    "tools": [
        "microsoft office", "google workspace", "jira", "confluence", "slack",
        "salesforce", "sap", "tableau", "power bi",
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
    """
    Extract skills from text when Groq is unavailable.
    Uses SkillNer (spaCy) when available — covers all industries.
    Falls back to CATEGORY_KEYWORDS keyword scan as a last resort.
    """
    if _SKILLNER_AVAILABLE:
        try:
            doc = _nlp(text)
            annotations = _skill_ner.annotate(doc)
            full_matches = annotations.get("results", {}).get("full_matches", [])
            return [s["doc_node_value"].lower().strip() for s in full_matches]
        except Exception as e:
            logger.warning(f"SkillNer extraction failed: {e}")

    # Last-resort: keyword scan
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

    async def detect_domain(self, job_text: str) -> str:
        """
        Detect the industry/domain from a job description.
        Returns a short label like 'technology', 'healthcare', 'human_resources', etc.
        Falls back to 'general' when Groq is unavailable.
        """
        if not self._groq:
            return "general"

        prompt = f"""Identify the primary industry/domain of this job description.
Return ONLY a JSON object with a single 'domain' key.
Choose from: technology, healthcare, human_resources, finance, legal, education, marketing, sales, operations, engineering, other

Job Description (first 600 chars):
{job_text[:600]}

JSON: {{"domain": "technology"}}"""

        try:
            raw = await _groq_call(self._groq, [{"role": "user", "content": prompt}], temperature=0.0)
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if m:
                return json.loads(m.group()).get("domain", "general")
        except Exception as e:
            logger.warning(f"Domain detection failed: {e}")
        return "general"

    async def extract_resume(self, text: str, domain: str = "general") -> List[str]:
        """
        Extract professional skills, certifications, and competencies from resume text.
        Works for any industry. Falls back to SkillNer/keyword scanning if Groq is unavailable.
        """
        if not self._groq:
            return _keyword_fallback(text)

        prompt = f"""Extract ALL professional skills, competencies, tools, certifications, and methodologies from this resume.
Return ONLY a valid JSON array of strings. Do not include soft skills.

Domain context: {domain}

Rules:
- Include skills explicitly listed in any Skills section.
- Include skills DEMONSTRATED through work experience only when the evidence is DIRECT and SPECIFIC — not by loose association.

  VALID inference examples (clear, direct evidence):
    "managed clinical trials for 200+ patients" → "clinical trial management"
    "processed HR onboarding cases monthly" → "employee onboarding"
    "built or rebuilt a React/Angular/Vue application" → "webpack"
    "wrote code, built software, or performed software engineering as primary job" → "git"
    "built websites or web interfaces that adapt to screen sizes" → "responsive design"

  INVALID inference examples (do NOT do these):
    "designed lesson plans" → do NOT infer "responsive design" or any web/tech skill
    "analytical" or "problem solving" listed as skills → do NOT infer any tech tools
    "designed performance improvement plans" → do NOT infer any software tools
    any teaching, nursing, coaching, legal, accounting, or HR role → do NOT infer git, webpack, or developer tools

- CRITICAL GATE: Only infer software/web development tools (git, webpack, npm, responsive design, etc.) if the resume EXPLICITLY describes the candidate's PRIMARY job function as software engineering, web development, or programming. A teacher, nurse, coach, or accountant does NOT imply developer tools under any circumstances.
- Include certifications and professional qualifications (MD, CPA, SHRM-CP, PMP, teaching certification, etc.).
- Do NOT include soft skills (communication, teamwork, leadership, problem solving, time management, accountability).

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

    async def extract_job_with_categories(self, job_text: str, domain: str = "general") -> Dict:
        """
        Single Groq call that extracts job skills, splits them into required/preferred,
        AND returns each skill's domain category — for any industry.

        Returns:
            {
              "required":   ["skill1", ...],
              "preferred":  ["skill2", ...],
              "categories": {"skill1": "clinical_skills", "skill2": "certifications", ...}
            }
        """
        fallback = {"required": [], "preferred": [], "categories": {}}
        if not self._groq:
            skills = _keyword_fallback(job_text)
            fallback["required"] = skills
            fallback["categories"] = {s: self._categorize_one(s) for s in skills}
            return fallback

        # Domain-specific category hint so Groq generates relevant categories
        domain_hints = {
            "technology":      "e.g. programming, frameworks, databases, devops, methodologies, tools",
            "healthcare":      "e.g. clinical_skills, certifications, specializations, equipment, research, administrative",
            "human_resources": "e.g. recruitment, hr_systems, compliance, training_development, compensation, strategy",
            "finance":         "e.g. financial_analysis, certifications, regulatory, tools, methodologies, reporting",
            "legal":           "e.g. practice_areas, certifications, litigation, research, compliance, tools",
            "education":       "e.g. subject_expertise, pedagogy, certifications, technology, curriculum, assessment",
            "marketing":       "e.g. digital_marketing, analytics, content, advertising, tools, strategy",
            "sales":           "e.g. sales_methodology, crm_tools, negotiation, industry_knowledge, analytics",
            "engineering":     "e.g. mechanical, electrical, civil, cad_tools, project_management, certifications",
            "operations":      "e.g. process_management, supply_chain, logistics, erp_tools, quality, certifications",
        }
        category_hint = domain_hints.get(domain, "e.g. core_skills, certifications, tools, methodologies, domain_knowledge")

        prompt = f"""Analyse this job description. Extract concrete, verifiable skills only.

WHAT TO EXTRACT: technologies, programming languages, frameworks, libraries, tools, platforms, certifications, licenses, methodologies, and specific domain knowledge areas.

WHAT TO EXCLUDE (do NOT extract these):
- Soft skills and interpersonal traits: communication, collaboration, teamwork, leadership, attention to detail, design sense, problem-solving, time management, adaptability, creativity.
- Vague qualities that cannot be verified on a resume: "keen eye for design", "passion for learning", "good judgment".
- If a JD section is titled "Required Skills" but lists soft skills, skip those entries entirely.

Classify each concrete skill as REQUIRED or PREFERRED using these strict rules:

REQUIRED: A skill is required if it appears in a Requirements or Qualifications section.
  - If the JD lists OR alternatives for the SAME requirement (e.g. "React, Angular, or Vue.js"), emit them as ONE entry using slash notation: "react/angular/vue.js". Do NOT emit them as separate entries.
  - Apply the same rule to equivalent tools (e.g. "Webpack or Vite" → "webpack/vite"; "Workday or BambooHR" → "workday/bamboohr").
  - One slot per distinct requirement.

PREFERRED: A skill is preferred ONLY if the JD explicitly uses words like "nice to have", "bonus", "plus", "preferred", or groups them under a "Preferred Qualifications" heading.

Also assign each skill to a category appropriate for a {domain} role ({category_hint}).
Only create categories that have at least 2 skills. Use 3-5 categories maximum.
For slash-notation skills, use the category of the first option.

Return ONLY valid JSON — no markdown, no extra text:
{{
  "required":   ["skill1", "react/angular/vue.js"],
  "preferred":  ["skill3"],
  "categories": {{"skill1": "programming", "react/angular/vue.js": "frameworks", "skill3": "tools"}}
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
