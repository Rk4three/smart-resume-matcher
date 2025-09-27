import os, io, json, logging, re
from typing import List, Dict, Set
import httpx, PyPDF2
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
from supabase import create_client, Client
import skills_dictionary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI(title="Smart Resume Matcher API", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

supabase: Client = None
model: SentenceTransformer = None
gemini_api_key: str = None

@app.on_event("startup")
async def startup_event():
    global supabase, model, gemini_api_key
    try:
        SUPABASE_URL = os.environ.get("SUPABASE_URL")
        SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Successfully connected to Supabase.")
        response = supabase.table('secrets').select('value').eq('key', 'GEMINI_API_KEY').single().execute()
        if response.data: gemini_api_key = response.data['value']; logger.info("Loaded Gemini API Key.")
    except Exception as e: logger.error(f"DB/API Key Error: {e}")
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("SentenceTransformer model loaded.")
    except Exception as e: logger.error(f"Model loading error: {e}")

def extract_text_from_pdf(file_content: bytes) -> str:
    try:
        text = "".join(page.extract_text() or "" for page in PyPDF2.PdfReader(io.BytesIO(file_content)).pages)
        return " ".join(text.split())
    except Exception as e: raise HTTPException(status_code=400, detail="Could not process PDF.")

async def extract_skills_with_gemini(text: str) -> List[str]:
    if not gemini_api_key: return []
    prompt = f'Extract key skills from the text below. Return a JSON array of strings. Text: "{text}"'
    api_url = f"[https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=](https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=){gemini_api_key}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(api_url, json={"contents": [{"parts": [{"text": prompt}]}]})
            response.raise_for_status()
            result_text = response.json()['candidates'][0]['content']['parts'][0]['text']
            json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
            return json.loads(json_match.group()) if json_match else []
    except Exception as e: logger.error(f"Gemini API call failed: {e}"); return []

def extract_skills_from_dictionary(text: str) -> Set[str]:
    text_lower = text.lower()
    found = set()
    for canonical, synonyms in skills_dictionary.SKILL_SYNONYMS.items():
        for variant in [canonical] + synonyms:
            if re.search(r'\b' + re.escape(variant) + r'\b', text_lower): found.add(canonical); break
    return found

async def extract_skills_hybrid(text: str) -> List[str]:
    dict_skills = extract_skills_from_dictionary(text)
    gemini_skills_raw = await extract_skills_with_gemini(text)
    gemini_normalized = {skills_dictionary.find_standard_skill(s) or s.strip().lower() for s in gemini_skills_raw}
    return sorted(list(dict_skills.union(gemini_normalized)))

def calculate_semantic_similarity(resume_skills: List[str], job_skills: List[str]) -> Dict:
    if not model or not job_skills: return {"score": 0, "matched_skills": [], "missing_skills": job_skills or []}
    if not resume_skills: return {"score": 0, "matched_skills": [], "missing_skills": job_skills}
    resume_emb = model.encode(resume_skills)
    job_emb = model.encode(job_skills)
    cos_scores = cos_sim(resume_emb, job_emb)
    matched = {job_skill for i, job_skill in enumerate(job_skills) if max(cos_scores[:, i]).item() > 0.65}
    score = (len(matched) / len(job_skills)) * 100
    return {"score": round(score, 2), "matched_skills": sorted(list(matched)), "missing_skills": sorted(list(set(job_skills) - matched))}

@app.post("/api/calculate-match")
async def create_match_from_upload(file: UploadFile = File(...), job_description: str = Form(...)):
    if not model: raise HTTPException(status_code=503, detail="AI model not available.")
    resume_text = extract_text_from_pdf(await file.read())
    resume_skills = await extract_skills_hybrid(resume_text)
    job_skills = await extract_skills_hybrid(job_description)
    return calculate_semantic_similarity(resume_skills, job_skills)