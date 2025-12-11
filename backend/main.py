import os
import io
import json
import logging
import re
import asyncio
from typing import List, Dict, Set, Optional, Tuple
import PyPDF2
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from dotenv import load_dotenv
import skills_dictionary

# ============================================================================
# CONFIGURATION
# ============================================================================
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Smart Resume Matcher API", version="12.0.0-CategoryMatching")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

groq_client: Optional[Groq] = None

# ============================================================================
# INITIALIZATION
# ============================================================================
@app.on_event("startup")
async def startup_event():
    global groq_client
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        groq_client = Groq(api_key=api_key)
        logger.info("✅ Groq AI initialized successfully")
    else:
        logger.warning("⚠️ No Groq API key found - running in dictionary-only mode")

# ============================================================================
# ROOT ENDPOINT
# ============================================================================
@app.get("/")
async def root():
    return {
        "message": "Smart Resume Matcher API",
        "version": "12.0.0-CategoryMatching",
        "status": "running",
        "endpoints": {
            "calculate_match": "POST /api/calculate-match",
            "health": "GET /health"
        },
        "docs": "/docs"
    }

# ============================================================================
# SKILL CATEGORY AND EQUIVALENCE MATCHING
# ============================================================================
def format_skill_display(skill: str) -> str:
    """Convert snake_case or lowercase to proper display format"""
    special_cases = {
        "html": "HTML",
        "css": "CSS",
        "sql": "SQL",
        "api": "API",
        "rest": "REST API",
        "graphql": "GraphQL",
        "postgresql": "PostgreSQL",
        "mysql": "MySQL",
        "mongodb": "MongoDB",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "nodejs": "Node.js",
        "react": "React",
        "vue": "Vue.js",
        "fastapi": "FastAPI",
        "github": "GitHub",
        "digitalocean": "DigitalOcean",
        "vscode": "VS Code",
        "ui": "UI",
        "ux": "UX",
        "git": "Git",
        "docker": "Docker",
        "vite": "Vite",
        "vercel": "Vercel",
        "railway": "Railway",
        "supabase": "Supabase",
        "groq": "Groq AI",
        "tailwind": "Tailwind CSS",
        "oop": "OOP",
        "aws": "AWS",
        "azure": "Azure",
        "gcp": "GCP",
        "tdd": "TDD",
        "bdd": "BDD",
        "mvc": "MVC",
        "seo": "SEO",
        "http": "HTTP",
        "https": "HTTPS",
        "ssl": "SSL/TLS",
        "cdn": "CDN",
        "dns": "DNS",
    }
    
    skill_lower = skill.lower().strip()
    
    if skill_lower in special_cases:
        return special_cases[skill_lower]
    
    # Convert underscore to space and title case
    return skill.replace("_", " ").replace("-", " ").title()

def get_skill_equivalents(skill: str) -> Set[str]:
    """Get equivalent skills based on categories."""
    canonical = skills_dictionary.find_standard_skill(skill)
    if not canonical:
        return set()
    
    equivalents = set()
    equivalents.add(canonical)
    
    # Add category-based equivalents
    category = skills_dictionary.get_skill_category(canonical)
    if category:
        skills_in_category = skills_dictionary.get_skills_in_category(category)
        equivalents.update(skills_in_category)
    
    return equivalents

def find_category_match(job_skill: str, resume_skills: Set[str]) -> bool:
    """Check if a job skill matches any resume skill in the same category."""
    job_canonical = skills_dictionary.find_standard_skill(job_skill)
    if not job_canonical:
        return False
    
    job_category = skills_dictionary.get_skill_category(job_canonical)
    if not job_category:
        return False
    
    # Check if any resume skill is in the same category
    for resume_skill in resume_skills:
        resume_canonical = skills_dictionary.find_standard_skill(resume_skill)
        if not resume_canonical:
            continue
        
        resume_category = skills_dictionary.get_skill_category(resume_canonical)
        if resume_category == job_category:
            return True
    
    return False

# ============================================================================
# PDF EXTRACTION
# ============================================================================
def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract and clean text from PDF"""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        # Clean up text
        text = " ".join(text.split())
        return text
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        raise HTTPException(status_code=400, detail="Invalid or corrupted PDF file")

# ============================================================================
# AI INTERACTION
# ============================================================================
async def call_groq_api(prompt: str, temperature: float = 0.1) -> str:
    """Call Groq API with error handling"""
    if not groq_client:
        return ""

    try:
        completion = await asyncio.to_thread(
            groq_client.chat.completions.create,
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=temperature,
        )
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return ""

# ============================================================================
# ENHANCED SKILL EXTRACTION
# ============================================================================
def extract_skills_from_text_precise(text: str) -> Set[str]:
    """Precise dictionary-based skill extraction with context validation"""
    skills_found = set()
    text_lower = text.lower()
    
    # Check each canonical skill
    for canonical, synonyms in skills_dictionary.SKILL_SYNONYMS.items():
        # Check canonical name
        if canonical in text_lower:
            # Validate it's not part of another word
            pattern = r'\b' + re.escape(canonical) + r'\b'
            if re.search(pattern, text_lower):
                skills_found.add(canonical)
                continue
        
        # Check all synonyms
        for synonym in synonyms:
            if " " in synonym:
                # For multi-word synonyms, check exact phrase
                if synonym in text_lower:
                    skills_found.add(canonical)
                    break
            else:
                # For single words, check word boundaries
                pattern = r'\b' + re.escape(synonym) + r'\b'
                if re.search(pattern, text_lower):
                    skills_found.add(canonical)
                    break
    
    return skills_found

async def extract_resume_skills_hybrid(resume_text: str) -> Set[str]:
    """Hybrid extraction: Dictionary + AI with category awareness"""
    
    # Step 1: Fast dictionary extraction
    dict_skills = extract_skills_from_text_precise(resume_text)
    
    # Step 2: AI extraction with enhanced understanding of categories
    ai_skills = set()
    
    if groq_client:
        prompt = f"""Extract ALL technical skills from this resume. Include:
        1. Specific technologies (Python, React, PostgreSQL, etc.)
        2. Programming paradigms (OOP, functional programming, etc.)
        3. Web development concepts (responsive design, SEO, etc.)
        4. Methodologies (Agile, TDD, etc.)
        5. Tools and platforms (Git, Docker, Vercel, etc.)
        
        Be comprehensive but accurate. Only include skills that are explicitly mentioned or clearly implied.
        
        Return ONLY a JSON array of skill strings:
        ["skill1", "skill2", "skill3"]
        
        Resume text:
        {resume_text[:4000]}"""
        
        response = await call_groq_api(prompt, temperature=0.1)
        
        try:
            # Extract JSON array from response
            match = re.search(r"\[.*?\]", response, re.DOTALL)
            if match:
                ai_extracted = json.loads(match.group())
                for skill in ai_extracted:
                    skill_clean = skill.lower().strip()
                    # Try to find canonical skill
                    canonical = skills_dictionary.find_standard_skill(skill_clean)
                    if canonical:
                        ai_skills.add(canonical)
                    else:
                        # Also include non-canonical skills that might be important
                        # But only if they look like technical skills (not soft skills)
                        if len(skill_clean) > 2 and not any(soft in skill_clean for soft in 
                            ["communication", "teamwork", "leadership", "problem solving", 
                             "collaboration", "time management", "adaptability"]):
                            ai_skills.add(skill_clean)
        except Exception as e:
            logger.error(f"AI skill extraction parsing error: {e}")
    
    # Combine all skills
    all_skills = dict_skills.union(ai_skills)
    
    return all_skills

async def analyze_job_requirements_precise(job_text: str) -> Dict[str, any]:
    """Enhanced job analysis with category awareness"""
    
    # Step 1: Dictionary extraction
    dict_skills = extract_skills_from_text_precise(job_text)
    
    # Step 2: AI analysis with enhanced understanding
    if groq_client:
        prompt = f"""Analyze this job description thoroughly and extract technical skills.
        
        Categorize skills into:
        1. **required_technical**: MUST-HAVE technical skills and concepts
        2. **preferred_technical**: Nice-to-have technical skills mentioned as preferred or "bonus"
        
        IMPORTANT GUIDELINES:
        - Include programming languages, frameworks, databases, tools, platforms
        - Include concepts like OOP, RDBMS, web security, responsive design, etc.
        - Include methodologies like Agile, TDD, etc.
        - Include web development concepts like SEO, web performance, etc.
        - DO NOT include soft skills (communication, teamwork, leadership, etc.)
        - DO NOT include generic business terms
        - Be specific: "relational databases" should be included as a concept
        - "web applications" should be interpreted as web development skills
        
        Return ONLY valid JSON:
        {{
          "required_technical": ["skill1", "skill2"],
          "preferred_technical": ["skill3", "skill4"]
        }}
        
        Job Description:
        {job_text[:4000]}"""
        
        response = await call_groq_api(prompt, temperature=0.1)
        
        try:
            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
                
                # Normalize all skills
                normalized = {
                    "required_technical": [],
                    "preferred_technical": []
                }
                
                # Soft skills to exclude
                soft_skill_indicators = [
                    "communication", "teamwork", "leadership", "problem solving", 
                    "collaboration", "time management", "adaptability", "creativity",
                    "critical thinking", "work ethic", "interpersonal", "presentation",
                    "organizational", "business acumen", "thrive", "learn rapidly",
                    "master", "diagnosis", "creative", "aggressive", "budgets"
                ]
                
                for key in ["required_technical", "preferred_technical"]:
                    for skill in parsed.get(key, []):
                        skill_lower = skill.lower().strip()
                        
                        # Skip soft skills
                        if any(soft in skill_lower for soft in soft_skill_indicators):
                            continue
                            
                        # Try to find canonical skill
                        canonical = skills_dictionary.find_standard_skill(skill_lower)
                        if canonical:
                            normalized[key].append(canonical)
                        else:
                            # Keep important conceptual skills
                            conceptual_skills = [
                                "rdbms", "relational database", "relational databases",
                                "web applications", "web development", "web programming",
                                "session management", "network diagnostics", "network analytics",
                                "search engine optimization", "object oriented programming",
                                "security", "diagnostics", "analytics", "best practices"
                            ]
                            if any(concept in skill_lower for concept in conceptual_skills):
                                # Map conceptual skills to canonical ones
                                if "rdbms" in skill_lower or "relational database" in skill_lower:
                                    normalized[key].append("sql")  # Represent RDBMS with SQL
                                elif "object oriented" in skill_lower or "oop" in skill_lower:
                                    normalized[key].append("oop")
                                elif "web" in skill_lower and ("development" in skill_lower or "programming" in skill_lower):
                                    normalized[key].append("javascript")  # Represent web dev
                                elif "seo" in skill_lower or "search engine" in skill_lower:
                                    normalized[key].append("seo")
                                elif "network" in skill_lower and ("diagnostics" in skill_lower or "analytics" in skill_lower):
                                    normalized[key].append("http")  # Represent networking
                
                # Remove duplicates
                normalized["required_technical"] = list(set(normalized["required_technical"]))
                normalized["preferred_technical"] = list(set(normalized["preferred_technical"]))
                
                # Add dictionary findings if not already categorized
                all_categorized = set(normalized["required_technical"] + normalized["preferred_technical"])
                for ds in dict_skills:
                    if ds not in all_categorized:
                        normalized["required_technical"].append(ds)
                
                return normalized
        except Exception as e:
            logger.error(f"AI job analysis error: {e}")
    
    # Fallback
    return {
        "required_technical": list(dict_skills),
        "preferred_technical": []
    }

# ============================================================================
# ENHANCED SCORING ENGINE WITH CATEGORY MATCHING
# ============================================================================
def calculate_enhanced_match_score(resume_skills: Set[str], job_requirements: Dict) -> Dict:
    """Enhanced scoring with category-based matching"""
    
    resume_set = set(s.lower() for s in resume_skills)
    
    required_tech = set(s.lower() for s in job_requirements.get("required_technical", []))
    preferred_tech = set(s.lower() for s in job_requirements.get("preferred_technical", []))
    
    # Direct matches
    matched_required = required_tech.intersection(resume_set)
    matched_preferred = preferred_tech.intersection(resume_set)
    
    # Category-based matches for remaining required skills
    remaining_required = required_tech - matched_required
    category_matched = set()
    
    for job_skill in remaining_required:
        if find_category_match(job_skill, resume_set):
            category_matched.add(job_skill)
    
    # Add category matches to direct matches
    matched_required = matched_required.union(category_matched)
    
    # Calculate scores
    required_score = 0
    preferred_score = 0
    
    if required_tech:
        required_score = (len(matched_required) / len(required_tech)) * 70  # 70 points max
    
    if preferred_tech:
        preferred_score = (len(matched_preferred) / len(preferred_tech)) * 30  # 30 points max
    
    # Calculate total score
    total_score = required_score + preferred_score
    
    # Apply bonus for strong matches
    if required_tech and (len(matched_required) / len(required_tech)) >= 0.8:
        total_score = min(total_score * 1.1, 100.0)
    
    # Round to 1 decimal place
    final_score = round(min(total_score, 100.0), 1)
    
    # Build suggestions
    suggestions = []
    
    if required_tech:
        req_percentage = (len(matched_required) / len(required_tech)) * 100
        if req_percentage >= 90:
            suggestions.append("Excellent match! You meet almost all required skills.")
        elif req_percentage >= 70:
            suggestions.append("Strong match! You meet most required skills.")
        elif req_percentage >= 50:
            suggestions.append("Good match! You meet about half of required skills.")
        
        # Mention category matches
        if category_matched:
            cat_skills = [format_skill_display(s) for s in category_matched]
            suggestions.append(f"Note: Your experience in related areas covers: {', '.join(cat_skills[:3])}")
    
    if matched_preferred:
        suggestions.append(f"Bonus: You have {len(matched_preferred)} preferred skill(s).")
    
    # Missing skills
    truly_missing = required_tech - matched_required
    
    # Format matched skills for display
    display_matched = sorted([format_skill_display(s) for s in matched_required])
    display_preferred = sorted([format_skill_display(s) for s in matched_preferred])
    display_missing = sorted([format_skill_display(s) for s in truly_missing])
    
    # Identify which matches were category-based vs direct
    direct_matches = matched_required.intersection(resume_set.intersection(required_tech))
    category_matches = matched_required - direct_matches
    
    return {
        "score": final_score,
        "breakdown": {
            "required_match": f"{len(matched_required)}/{len(required_tech)}",
            "preferred_match": f"{len(matched_preferred)}/{len(preferred_tech)}",
            "direct_matches": len(direct_matches),
            "category_matches": len(category_matches)
        },
        "matched_skills": display_matched,
        "matched_preferred": display_preferred,
        "missing_critical": display_missing,
        "suggestions": suggestions
    }

# ============================================================================
# API ENDPOINTS
# ============================================================================
@app.post("/api/calculate-match")
async def calculate_match(
    file: UploadFile = File(...),
    job_description: str = Form(...)
):
    """Main endpoint for resume matching"""

    try:
        # Extract resume text
        resume_content = await file.read()
        resume_text = extract_text_from_pdf(resume_content)

        if len(resume_text) < 100:
            raise HTTPException(status_code=400, detail="Resume text too short or unreadable")

        # Parallel processing
        resume_skills, job_requirements = await asyncio.gather(
            extract_resume_skills_hybrid(resume_text),
            analyze_job_requirements_precise(job_description)
        )

        logger.info(f"Extracted {len(resume_skills)} skills from resume")
        logger.info(f"Job requires: {job_requirements.get('required_technical', [])}")
        logger.info(f"Job prefers: {job_requirements.get('preferred_technical', [])}")

        # Calculate match
        result = calculate_enhanced_match_score(resume_skills, job_requirements)
        
        logger.info(f"Final score: {result['score']}%")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Match calculation error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "groq_enabled": groq_client is not None
    }