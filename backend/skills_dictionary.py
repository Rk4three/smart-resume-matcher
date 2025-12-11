"""
Skill synonym dictionary and helpers for hybrid resume-job matching.

This module exposes:
- SKILL_SYNONYMS: Dict[str, List[str]]
- SKILL_CATEGORIES: Dict[str, List[str]]
- get_all_skills() -> List[str]
- find_standard_skill(text: str) -> Optional[str]
- get_skill_synonyms(canonical: str) -> List[str]
- get_skill_category(canonical: str) -> Optional[str]
- get_skills_in_category(category: str) -> List[str]
"""

from typing import Dict, List, Optional, Set
import json


def _norm(tokens: List[str]) -> List[str]:
    """Lowercase + de-duplicate while preserving order."""
    seen = set()
    out: List[str] = []
    for t in tokens:
        s = (t or "").strip().lower()
        if not s:
            continue
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


# Canonical skill map with expanded categories
SKILL_SYNONYMS: Dict[str, List[str]] = {
    # Programming languages
    "javascript": _norm(["javascript", "js", "ecmascript", "es6", "es2015", "es2020", "vanilla js"]),
    "typescript": _norm(["typescript", "ts", "typescript developer"]),
    "python": _norm(["python", "py", "python3", "python programming"]),
    "java": _norm(["java", "java programming", "java developer"]),
    "csharp": _norm(["c#", "c sharp", "csharp", ".net", "dotnet", "asp.net", "asp.net core", "aspnet"]),
    "php": _norm(["php", "php programming", "php developer"]),
    "ruby": _norm(["ruby", "ruby programming", "ruby developer"]),
    "go": _norm(["go", "golang"]),
    "rust": _norm(["rust", "rust programming"]),
    "swift": _norm(["swift", "swift programming"]),
    "kotlin": _norm(["kotlin", "kotlin programming"]),
    
    # Frontend frameworks & libraries
    "react": _norm(["react", "reactjs", "react.js", "react native", "react developer"]),
    "angular": _norm(["angular", "angularjs", "angular.js"]),
    "vue": _norm(["vue", "vuejs", "vue.js", "nuxt.js", "nuxt"]),
    "svelte": _norm(["svelte", "sveltejs"]),
    "jquery": _norm(["jquery", "jquery ui"]),
    
    # Frontend tools & styling
    "html": _norm(["html", "html5", "hypertext markup language"]),
    "css": _norm(["css", "css3", "cascading style sheets", "sass", "scss", "less"]),
    "tailwind": _norm(["tailwind", "tailwind css", "tailwindcss"]),
    "bootstrap": _norm(["bootstrap", "twitter bootstrap"]),
    "material_ui": _norm(["material ui", "mui", "material design"]),
    "vite": _norm(["vite", "vitejs"]),
    "webpack": _norm(["webpack", "webpack bundler"]),
    
    # Backend frameworks
    "nodejs": _norm(["node.js", "nodejs", "node", "express", "express.js", "expressjs", "nestjs"]),
    "django": _norm(["django", "django python"]),
    "flask": _norm(["flask", "flask python"]),
    "fastapi": _norm(["fastapi", "fast api"]),
    "spring": _norm(["spring", "spring boot", "springboot", "spring framework"]),
    "laravel": _norm(["laravel", "laravel php"]),
    "rails": _norm(["rails", "ruby on rails", "ror"]),
    "aspnet": _norm(["asp.net", "aspnet", "asp.net core"]),
    
    # Databases
    "postgresql": _norm(["postgresql", "postgres", "postgres sql", "pg"]),
    "mysql": _norm(["mysql", "my sql", "mariadb"]),
    "mongodb": _norm(["mongodb", "mongo", "mongo db"]),
    "sqlite": _norm(["sqlite", "sqlite3"]),
    "redis": _norm(["redis", "redis cache"]),
    "sql": _norm(["sql", "structured query language"]),
    "nosql": _norm(["nosql", "non relational database"]),
    "supabase": _norm(["supabase"]),
    "firebase": _norm(["firebase", "google firebase"]),
    
    # Cloud & DevOps
    "aws": _norm(["aws", "amazon web services", "amazon aws"]),
    "azure": _norm(["azure", "microsoft azure"]),
    "gcp": _norm(["gcp", "google cloud", "google cloud platform"]),
    "vercel": _norm(["vercel"]),
    "railway": _norm(["railway", "railway app"]),
    "digitalocean": _norm(["digitalocean", "digital ocean", "do"]),
    "docker": _norm(["docker", "docker containers", "containerization"]),
    "kubernetes": _norm(["kubernetes", "k8s", "kube"]),
    "jenkins": _norm(["jenkins", "jenkins ci"]),
    "github_actions": _norm(["github actions", "github ci/cd"]),
    "gitlab": _norm(["gitlab", "gitlab ci"]),
    
    # Tools & Version Control
    "git": _norm(["git", "git version control"]),
    "github": _norm(["github"]),
    "gitlab_tool": _norm(["gitlab"]),
    "bitbucket": _norm(["bitbucket"]),
    "vscode": _norm(["vscode", "visual studio code", "vs code"]),
    "intellij": _norm(["intellij", "intellij idea"]),
    "webstorm": _norm(["webstorm"]),
    "postman": _norm(["postman", "api testing"]),
    
    # APIs & Services
    "rest": _norm(["rest", "rest api", "restful", "restful api"]),
    "graphql": _norm(["graphql", "graphql api"]),
    "grpc": _norm(["grpc", "g rpc"]),
    "groq": _norm(["groq", "groq ai"]),
    "openai": _norm(["openai", "openai api", "chatgpt api"]),
    "deepgram": _norm(["deepgram"]),
    
    # Concepts & Methodologies
    "oop": _norm(["oop", "object oriented programming", "object oriented", "object-oriented"]),
    "functional_programming": _norm(["functional programming", "fp"]),
    "mvc": _norm(["mvc", "model view controller"]),
    "microservices": _norm(["microservices", "microservice architecture"]),
    "serverless": _norm(["serverless", "serverless architecture"]),
    "agile": _norm(["agile", "agile methodology", "scrum", "kanban"]),
    "tdd": _norm(["tdd", "test driven development"]),
    "bdd": _norm(["bdd", "behavior driven development"]),
    
    # Web Development Concepts
    "responsive_design": _norm(["responsive design", "responsive web design", "mobile responsive"]),
    "web_accessibility": _norm(["accessibility", "a11y", "web accessibility", "wcag"]),
    "cross_browser": _norm(["cross browser", "cross browser compatibility"]),
    "seo": _norm(["seo", "search engine optimization"]),
    "web_performance": _norm(["web performance", "performance optimization", "page speed"]),
    "web_security": _norm(["web security", "security", "owasp", "xss", "csrf", "sql injection"]),
    
    # Testing
    "jest": _norm(["jest", "jest js"]),
    "mocha": _norm(["mocha", "mocha js"]),
    "cypress": _norm(["cypress", "cypress.io"]),
    "pytest": _norm(["pytest", "python test"]),
    "unit_testing": _norm(["unit testing", "unit tests"]),
    "integration_testing": _norm(["integration testing", "integration tests"]),
    "e2e_testing": _norm(["end to end testing", "e2e testing"]),
    
    # Data & Analytics
    "data_visualization": _norm(["data visualization", "charts", "d3.js", "chart.js"]),
    "machine_learning": _norm(["machine learning", "ml", "ai"]),
    "data_analysis": _norm(["data analysis", "data analytics"]),
    "pandas": _norm(["pandas", "python pandas"]),
    "numpy": _norm(["numpy", "python numpy"]),
    
    # Networking & Infrastructure
    "http": _norm(["http", "https", "http/2", "http2"]),
    "websocket": _norm(["websocket", "websockets", "real-time"]),
    "cdn": _norm(["cdn", "content delivery network"]),
    "dns": _norm(["dns", "domain name system"]),
    "ssl": _norm(["ssl", "tls", "https"]),
    "load_balancing": _norm(["load balancing", "load balancer"]),
    "nginx": _norm(["nginx", "nginx web server"]),
    "apache": _norm(["apache", "apache http server"]),
    
    # Design & UX
    "ui_design": _norm(["ui", "user interface", "ui design"]),
    "ux_design": _norm(["ux", "user experience", "ux design"]),
    "figma": _norm(["figma"]),
    "sketch": _norm(["sketch", "sketch app"]),
    "adobe_xd": _norm(["adobe xd", "xd"]),
    "photoshop": _norm(["photoshop", "adobe photoshop"]),
    "illustrator": _norm(["illustrator", "adobe illustrator"]),
}

# Skill category mapping for broader matching
SKILL_CATEGORIES: Dict[str, List[str]] = {
    "frontend": ["javascript", "typescript", "html", "css", "react", "angular", "vue", "svelte", 
                "jquery", "tailwind", "bootstrap", "material_ui", "vite", "webpack"],
    "backend": ["python", "java", "csharp", "php", "ruby", "go", "nodejs", "django", "flask", 
               "fastapi", "spring", "laravel", "rails", "aspnet"],
    "database": ["postgresql", "mysql", "mongodb", "sqlite", "redis", "sql", "nosql", 
                "supabase", "firebase"],
    "devops": ["aws", "azure", "gcp", "vercel", "railway", "digitalocean", "docker", 
              "kubernetes", "jenkins", "github_actions", "gitlab"],
    "web_concepts": ["responsive_design", "web_accessibility", "cross_browser", "seo", 
                    "web_performance", "web_security", "http", "websocket", "cdn", "ssl"],
    "methodologies": ["oop", "functional_programming", "mvc", "microservices", "serverless", 
                     "agile", "tdd", "bdd"],
    "testing": ["jest", "mocha", "cypress", "pytest", "unit_testing", "integration_testing", "e2e_testing"],
    "tools": ["git", "github", "gitlab_tool", "bitbucket", "vscode", "intellij", "webstorm", "postman"],
    "apis": ["rest", "graphql", "grpc", "groq", "openai", "deepgram"],
    "frontend": ["javascript", "typescript", "html", "css", "react", "angular", "vue", "svelte", 
                "jquery", "tailwind", "bootstrap", "material_ui", "vite", "webpack"],
    "backend": ["python", "java", "csharp", "php", "ruby", "go", "nodejs", "django", "flask", 
               "fastapi", "spring", "laravel", "rails", "aspnet"],
    "database": ["postgresql", "mysql", "mongodb", "sqlite", "redis", "sql", "nosql", 
                "supabase", "firebase"],
    "devops": ["aws", "azure", "gcp", "vercel", "railway", "digitalocean", "docker", 
              "kubernetes", "jenkins", "github_actions", "gitlab"],
    "web_concepts": ["responsive_design", "web_accessibility", "cross_browser", "seo", 
                    "web_performance", "web_security", "http", "websocket", "cdn", "ssl"],
    "methodologies": ["oop", "functional_programming", "mvc", "microservices", "serverless", 
                     "agile", "tdd", "bdd"],
    "testing": ["jest", "mocha", "cypress", "pytest", "unit_testing", "integration_testing", "e2e_testing"],
    "tools": ["git", "github", "gitlab_tool", "bitbucket", "vscode", "intellij", "webstorm", "postman"],
    "apis": ["rest", "graphql", "grpc", "groq", "openai", "deepgram"],

}


def get_all_skills() -> List[str]:
    """Return all unique skill tokens across all categories (lowercased)."""
    collected: List[str] = []
    for synonyms in SKILL_SYNONYMS.values():
        collected.extend(synonyms)
    # Include canonical keys as searchable tokens
    collected.extend(skill for skill in SKILL_SYNONYMS.keys())
    return _norm(collected)


def find_standard_skill(skill_text: str) -> Optional[str]:
    """
    Map any token to its canonical skill key if found.
    Exact, case-insensitive match against the synonym lists or canonical keys.
    """
    s = (skill_text or "").strip().lower()
    if not s:
        return None
    # Direct match by canonical key
    if s in SKILL_SYNONYMS:
        return s
    # Match in synonyms
    for canonical, synonyms in SKILL_SYNONYMS.items():
        if s in synonyms:
            return canonical
    return None


def get_skill_synonyms(canonical: str) -> List[str]:
    """Return all synonyms for a canonical key (empty list if not found)."""
    return SKILL_SYNONYMS.get((canonical or "").strip().lower(), [])


def get_skill_category(canonical: str) -> Optional[str]:
    """Return the category of a skill, or None if not found."""
    canonical = (canonical or "").strip().lower()
    for category, skills in SKILL_CATEGORIES.items():
        if canonical in skills:
            return category
    return None


def get_skills_in_category(category: str) -> List[str]:
    """Return all skills in a given category."""
    return SKILL_CATEGORIES.get((category or "").strip().lower(), [])