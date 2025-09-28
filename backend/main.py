import os, io, json, logging, re
from typing import List, Dict, Set, Tuple
import httpx, PyPDF2
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
from supabase import create_client, Client
import skills_dictionary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI(title="Smart Resume Matcher API", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

supabase: Client = None
model: SentenceTransformer = None
gemini_api_key: str = None

@app.on_event("startup")
async def startup_event():
    global supabase, model, gemini_api_key
    try:
        SUPABASE_URL = os.environ.get("SUPABASE_URL")
        SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
        if not SUPABASE_KEY:
            SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")
            logger.warning("Using ANON KEY for Supabase. Secrets may not be accessible.")

        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Successfully connected to Supabase.")
        
        response = supabase.table('secrets').select('value').eq('key', 'GEMINI_API_KEY').single().execute()
        if response.data: 
            gemini_api_key = response.data['value']
            logger.info("Successfully loaded Gemini API Key.")
        else:
            logger.error("Could not find GEMINI_API_KEY in the secrets table.")

    except Exception as e: 
        logger.error(f"DB/API Key Error: {e}")

    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("SentenceTransformer model loaded.")
    except Exception as e: 
        logger.error(f"Model loading error: {e}")

def extract_text_from_pdf(file_content: bytes) -> str:
    try:
        text = "".join(page.extract_text() or "" for page in PyPDF2.PdfReader(io.BytesIO(file_content)).pages)
        return " ".join(text.split())
    except Exception as e: 
        raise HTTPException(status_code=400, detail=f"Could not process PDF: {e}")

async def extract_skills_with_gemini(text: str) -> List[str]:
    if not gemini_api_key: 
        logger.warning("Gemini API key not found. Skipping Gemini skill extraction.")
        return []
    
    prompt = f'Extract all key skills, technologies, and qualifications from the following text. Return the result as a clean JSON array of strings, like ["Skill A", "Skill B", "Technology C"]. Text: "{text}"'
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={gemini_api_key}"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(api_url, json={"contents": [{"parts": [{"text": prompt}]}]})
            response.raise_for_status()
            
            result_text = response.json()['candidates'][0]['content']['parts'][0]['text']
            json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                logger.warning(f"Could not find a JSON array in Gemini response: {result_text}")
                return []
    except Exception as e: 
        logger.error(f"Gemini API call failed: {e}")
        return []

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
    gemini_skills_raw = await extract_skills_with_gemini(text)
    
    gemini_normalized = set()
    for skill in gemini_skills_raw:
        normalized = skills_dictionary.find_standard_skill(skill)
        if normalized:
            gemini_normalized.add(normalized)
        else:
            gemini_normalized.add(skill.strip().lower())
            
    return sorted(list(dict_skills.union(gemini_normalized)))

async def classify_skills_with_gemini(job_description: str, skills: List[str]) -> Dict[str, List[str]]:
    if not gemini_api_key:
        logger.warning("Gemini API key not found. Skipping skill classification.")
        return {"required": skills, "preferred": [], "soft": []}

    prompt = f"""
    Given the following job description and list of extracted skills, please classify each skill into one of three categories: "required", "preferred", or "soft".

    - "required": Essential skills explicitly stated as mandatory (e.g., "must have," "required," "strong experience in").
    - "preferred": Skills that are advantageous but not mandatory (e.g., "plus," "bonus," "nice to have," "familiarity with").
    - "soft": Interpersonal and non-technical skills (e.g., "communication," "teamwork," "problem-solving").

    Job Description:
    "{job_description}"

    Skills:
    {json.dumps(skills)}

    Return the result as a single JSON object with three keys: "required", "preferred", and "soft", each containing a list of the classified skills.
    Example format: {{"required": ["Java", "Spring Boot"], "preferred": ["Docker", "Kubernetes"], "soft": ["Communication", "Teamwork"]}}
    """
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={gemini_api_key}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(api_url, json={"contents": [{"parts": [{"text": prompt}]}]})
            response.raise_for_status()
            
            result_text = response.json()['candidates'][0]['content']['parts'][0]['text']
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                logger.warning(f"Could not find a JSON object in Gemini response for skill classification: {result_text}")
                return {"required": skills, "preferred": [], "soft": []}
    except Exception as e:
        logger.error(f"Gemini API call for skill classification failed: {e}")
        return {"required": skills, "preferred": [], "soft": []}

def calculate_weighted_similarity(resume_skills: List[str], classified_skills: Dict[str, List[str]]) -> Dict:
    if not model: 
        raise HTTPException(status_code=503, detail="AI model not available.")

    required_skills = classified_skills.get("required", [])
    preferred_skills = classified_skills.get("preferred", [])
    soft_skills = classified_skills.get("soft", [])

    all_job_skills = required_skills + preferred_skills + soft_skills
    if not all_job_skills:
        return {"score": 0, "matched_skills": [], "missing_skills": []}
    if not resume_skills:
        return {"score": 0, "matched_skills": [], "missing_skills": all_job_skills}

    resume_emb = model.encode(resume_skills)
    job_emb = model.encode(all_job_skills)
    
    cos_scores = cos_sim(resume_emb, job_emb)
    
    matched_skills = set()
    job_skill_max_similarity = {}
    for i, job_skill in enumerate(all_job_skills):
        max_similarity = max(cos_scores[:, i]).item()
        job_skill_max_similarity[job_skill] = max_similarity
        if max_similarity > 0.65:
            matched_skills.add(job_skill)

    weights = {"required": 3.0, "preferred": 1.0, "soft": 0.5}
    
    total_weighted_score = 0
    total_weight = 0

    for skill in required_skills:
        weight = weights["required"]
        total_weight += weight
        if skill in matched_skills:
            total_weighted_score += weight
    
    for skill in preferred_skills:
        weight = weights["preferred"]
        total_weight += weight
        if skill in matched_skills:
            total_weighted_score += weight

    for skill in soft_skills:
        weight = weights["soft"]
        total_weight += weight
        if skill in matched_skills:
            total_weighted_score += weight

    score = (total_weighted_score / total_weight) * 100 if total_weight > 0 else 0
    missing_skills = set(all_job_skills) - matched_skills
    
    return {
        "score": round(score, 2), 
        "matched_skills": sorted(list(matched_skills)), 
        "missing_skills": sorted(list(missing_skills))
    }

@app.post("/api/calculate-match")
async def create_match_from_upload(file: UploadFile = File(...), job_description: str = Form(...)):
    if not supabase:
        raise HTTPException(status_code=503, detail="Database connection not available.")

    resume_content = await file.read()
    resume_text = extract_text_from_pdf(resume_content)
    
    resume_skills = await extract_skills_hybrid(resume_text)
    job_skills = await extract_skills_hybrid(job_description)

    classified_skills = await classify_skills_with_gemini(job_description, job_skills)
    
    match_results = calculate_weighted_similarity(resume_skills, classified_skills)

    return match_results