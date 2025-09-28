import os, io, json, logging, re, asyncio
from typing import List, Dict, Set, Any
import httpx, PyPDF2
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client
import skills_dictionary
from groq import Groq, APIError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI(title="Smart Resume Matcher API", version="6.0.0-groq")

# Correct CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins for simplicity, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

supabase: Client = None
model: SentenceTransformer = None
groq_client: Groq = None
skill_to_category: Dict[str, str] = {}

@app.on_event("startup")
async def startup_event():
    global supabase, model, groq_client, skill_to_category
    try:
        SUPABASE_URL = os.environ.get("SUPABASE_URL")
        SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
        if not SUPABASE_KEY:
            SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")
            logger.warning("Using ANON KEY for Supabase. Secrets may not be accessible.")

        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Successfully connected to Supabase.")
        
        # Fetch the Groq API key instead of Gemini
        response = supabase.table('secrets').select('value').eq('key', 'GROQ_API_KEY').single().execute()
        if response.data and response.data.get('value'):
            GROQ_API_KEY = response.data['value']
            groq_client = Groq(api_key=GROQ_API_KEY)
            logger.info("Successfully loaded Groq API Key and initialized client.")
        else:
            logger.error("Could not find GROQ_API_KEY in the secrets table.")

    except Exception as e: 
        logger.error(f"DB/API Key Error: {e}")

    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("SentenceTransformer model loaded.")
    except Exception as e: 
        logger.error(f"Model loading error: {e}")

    # Create a reverse mapping from skill to category
    for category, skills in skills_dictionary.SKILL_SYNONYMS.items():
        for skill in skills:
            skill_to_category[skill] = category
        skill_to_category[category] = category

def extract_text_from_pdf(file_content: bytes) -> str:
    try:
        text = "".join(page.extract_text() or "" for page in PyPDF2.PdfReader(io.BytesIO(file_content)).pages)
        return " ".join(text.split())
    except Exception as e: 
        raise HTTPException(status_code=400, detail=f"Could not process PDF: {e}")

async def call_groq_api(prompt: str, retries: int = 3, delay: int = 2) -> str:
    if not groq_client:
        logger.error("Groq client not initialized.")
        return ""

    for attempt in range(retries):
        try:
            chat_completion = await asyncio.to_thread(
                groq_client.chat.completions.create,
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192", # Or another model like "mixtral-8x7b-32768"
            )
            return chat_completion.choices[0].message.content
        except APIError as e:
            logger.error(f"Groq API Error (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                await asyncio.sleep(delay * (2 ** attempt))
        except Exception as e:
            logger.error(f"An unexpected error occurred during Groq API call: {e}")
            break
    return ""

def extract_skills_from_dictionary(text: str) -> Set[str]:
    text_lower = text.lower()
    found_skills = set()
    for canonical, synonyms in skills_dictionary.SKILL_SYNONYMS.items():
        all_variants = [canonical] + synonyms
        for variant in all_variants:
            if re.search(r'\b' + re.escape(variant) + r'\b', text_lower):
                found_skills.add(canonical)
                break
    return found_skills

async def extract_skills_hybrid(text: str) -> List[str]:
    dict_skills = extract_skills_from_dictionary(text)
    
    prompt = f'Extract all key skills, technologies, and qualifications from the following text. Respond ONLY with a valid JSON array of strings, like ["Skill A", "Skill B", "Technology C"]. Text: "{text}"'
    
    response_text = await call_groq_api(prompt)
    gemini_skills_raw = []
    if response_text:
        try:
            # Groq is good at returning just the JSON, but we clean it just in case
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                gemini_skills_raw = json.loads(json_match.group())
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Groq response for skill extraction: {e}")

    gemini_normalized = set()
    for skill in gemini_skills_raw:
        normalized = skills_dictionary.find_standard_skill(skill)
        if normalized:
            gemini_normalized.add(normalized)
        else:
            gemini_normalized.add(skill.strip().lower())
            
    return sorted(list(dict_skills.union(gemini_normalized)))

async def classify_job_skills(job_description: str, skills: List[str]) -> Dict[str, List[str]]:
    prompt = f"""
    Analyze the job description and classify the given skills into "required", "preferred", and "soft".
    - "required": Essential skills, usually mentioned with terms like "must have", "required", "proficient in", "strong experience".
    - "preferred": Skills that are a "plus", "nice to have", or a "bonus".
    - "soft": Interpersonal skills.

    Job Description: "{job_description}"
    Skills: {json.dumps(skills)}

    Respond ONLY with a single valid JSON object with "required", "preferred", and "soft" as keys.
    """
    response_text = await call_groq_api(prompt)
    if not response_text:
        return {"required": skills, "preferred": [], "soft": []}
    
    try:
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            logger.warning(f"Could not find JSON object in Groq response for skill classification: {response_text}")
            return {"required": skills, "preferred": [], "soft": []}
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing Groq response for skill classification: {e}")
        return {"required": skills, "preferred": [], "soft": []}

def calculate_final_score(resume_skills: List[str], classified_skills: Dict[str, List[str]]) -> Dict:
    required = classified_skills.get("required", [])
    preferred = classified_skills.get("preferred", [])
    soft = classified_skills.get("soft", [])
    
    resume_skills_set = set(resume_skills)
    has_soft_skills_in_resume = any(s in resume_skills_set for s in soft)

    weights = {"required": 3.0, "preferred": 0.5, "soft": 0.2, "synergy": 0.25}
    
    score = 0
    max_score = 0
    
    all_job_skills = set(required + preferred + (soft if has_soft_skills_in_resume else []))
    matched_skills = resume_skills_set.intersection(all_job_skills)
    missing_skills = set(required) - matched_skills

    for skill in required:
        max_score += weights["required"]
        if skill in matched_skills:
            score += weights["required"]
    
    for skill in preferred:
        max_score += weights["preferred"]
        if skill in matched_skills:
            score += weights["preferred"]

    if has_soft_skills_in_resume:
        for skill in soft:
            max_score += weights["soft"]
            if skill in matched_skills:
                score += weights["soft"]
                
    matched_categories = {}
    for skill in matched_skills:
        category = skill_to_category.get(skill)
        if category:
            matched_categories[category] = matched_categories.get(category, 0) + 1
    
    for count in matched_categories.values():
        if count > 1:
            synergy_bonus = (count - 1) * weights["synergy"]
            score += synergy_bonus
            max_score += synergy_bonus

    final_score = (score / max_score) * 100 if max_score > 0 else 0

    suggestions = []
    for missing in missing_skills:
        missing_category = skill_to_category.get(missing)
        if missing_category:
            related_matched = [s for s in matched_skills if skill_to_category.get(s) == missing_category]
            if related_matched:
                suggestions.append(f"Highlight transferable skills: You lack '{missing.replace('_', ' ')}', but your experience with '{related_matched[0].replace('_', ' ')}' is a strong related asset.")

    return {
        "score": round(min(final_score, 100), 2),
        "matched_skills": sorted(list(matched_skills)),
        "missing_skills": sorted(list(missing_skills)),
        "suggestions": suggestions
    }

@app.post("/api/calculate-match")
async def create_match_from_upload(file: UploadFile = File(...), job_description: str = Form(...)):
    if not groq_client:
        raise HTTPException(status_code=503, detail="Groq API client not available. Check API key.")

    resume_content = await file.read()
    resume_text = extract_text_from_pdf(resume_content)
    
    resume_skills = await extract_skills_hybrid(resume_text)
    job_skills = await extract_skills_hybrid(job_description)

    classified_skills = await classify_job_skills(job_description, job_skills)
    
    match_results = calculate_final_score(resume_skills, classified_skills)

    return match_results