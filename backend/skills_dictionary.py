"""
Skill synonym dictionary and helpers for hybrid resume-job matching.

This module exposes:
- SKILL_SYNONYMS: Dict[str, List[str]]
- get_all_skills() -> List[str]
- find_standard_skill(text: str) -> Optional[str]
- get_skill_synonyms(canonical: str) -> List[str]

It is a curated merge:
- Keeps short, stable canonical keys expected by the matching code (e.g., "python", "javascript", "project_management").
- Integrates broad, cross-industry synonyms inspired by the provided current skills dictionary while normalizing to lowercase tokens.
- Avoids side effects (no prints/writes).
"""

from typing import Dict, List, Optional


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


# Canonical skill map (broad, cross-industry), normalized to lowercase.
# Many synonyms below were adapted from the provided current dictionary (e.g., "*_programming",
# "*_framework", healthcare/finance/marketing/HR/manufacturing domains), and merged into
# compact canonical buckets used by the matching engine.
SKILL_SYNONYMS: Dict[str, List[str]] = {
    # Programming languages and core stacks
    "javascript": _norm([
        "javascript", "js", "ecmascript", "es6", "es2015", "es2020",
        "node.js", "nodejs",
        # From attached "javascript_programming"
        "javascript developer", "javscript"
    ]),
    "typescript": _norm([
        "typescript", "ts", "typescript developer", "ts programming"
    ]),
    "python": _norm([
        "python", "py", "python3", "python programming", "python developer", "python scripting",
        "django", "flask", "fastapi",
    ]),
    "java": _norm([
        "java", "java programming", "java developer", "spring", "spring boot", "hibernate"
    ]),
    "csharp": _norm([
        "c#", "c sharp", "csharp", ".net", "dotnet", "asp.net", "asp.net core"
    ]),
    "cpp": _norm([
        "c++", "cplusplus", "c plus plus"
    ]),
    "go": _norm([
        "go", "golang", "go programming", "golang developer"
    ]),
    "rust": _norm([
        "rust", "rust programming", "rust developer"
    ]),
    "php": _norm([
        "php", "php programming", "php developer", "laravel", "symfony", "wordpress"
    ]),
    "ruby": _norm([
        "ruby", "ruby programming", "ruby developer", "rails", "ruby on rails", "ror"
    ]),
    "swift": _norm([
        "swift", "swift programming", "ios swift", "swift developer", "objective-c", "objective c", "objc"
    ]),
    "kotlin": _norm([
        "kotlin", "kotlin programming", "kotlin developer", "android kotlin"
    ]),
    "r": _norm([
        "r", "r programming", "r developer", "r statistical"
    ]),
    "matlab": _norm([
        "matlab", "matlab programming", "matlab scripting"
    ]),
    "perl": _norm([
        "perl", "perl scripting"
    ]),

    # Frontend frameworks & tooling
    "react": _norm([
        "react", "reactjs", "react.js", "react developer", "react native", "next.js", "nextjs"
    ]),
    "redux": _norm([
        "redux", "reduxjs", "state management", "react redux"
    ]),
    "angular": _norm([
        "angular", "angularjs", "angular.js"
    ]),
    "vue": _norm([
        "vue", "vuejs", "vue.js", "nuxt.js", "nuxt"
    ]),
    "svelte": _norm([
        "svelte", "sveltejs"
    ]),
    "webpack": _norm([
        "webpack", "module bundler", "webpack config"
    ]),
    "babel": _norm([
        "babel", "babel transpiler", "babeljs"
    ]),
    "esbuild": _norm([
        "esbuild", "esbuild bundler"
    ]),
    "html": _norm([
        "html", "html5"
    ]),
    "css": _norm([
        "css", "css3", "sass", "scss", "less", "tailwind", "tailwind css", "bootstrap"
    ]),

    # Backend frameworks & platforms
    "nodejs": _norm([
        "node", "nodejs", "node.js", "express", "expressjs", "express.js"
    ]),
    "django": _norm([
        "django", "django python", "django framework"
    ]),
    "flask": _norm([
        "flask", "flask python", "flask microframework"
    ]),
    "spring": _norm([
        "spring", "spring boot", "springboot", "spring framework"
    ]),
    "dotnet": _norm([
        ".net", "dotnet", "asp.net", "aspnet", "asp.net core"
    ]),
    "laravel": _norm([
        "laravel", "laravel php", "laravel framework"
    ]),
    "rails": _norm([
        "rails", "ruby on rails", "ror", "rails developer"
    ]),

    # Databases & storage
    "mysql": _norm([
        "mysql", "my sql", "mysql database"
    ]),
    "postgresql": _norm([
        "postgresql", "postgres", "postgres sql", "pg"
    ]),
    "sqlserver": _norm([
        "microsoft sql server", "mssql", "sql server", "tsql", "t-sql"
    ]),
    "oracle_db": _norm([
        "oracle", "oracle database", "oracle db"
    ]),
    "mongodb": _norm([
        "mongodb", "mongo db", "mongo database", "nosql"
    ]),
    "cassandra": _norm([
        "cassandra", "apache cassandra"
    ]),
    "redis": _norm([
        "redis", "redis cache", "in-memory datastore", "key-value store"
    ]),
    "elasticsearch": _norm([
        "elasticsearch", "elastic search", "elastic", "elk", "opensearch"
    ]),
    "neo4j": _norm([
        "neo4j", "graph database", "graph db"
    ]),
    "dynamodb": _norm([
        "dynamodb", "amazon dynamodb", "aws dynamodb"
    ]),
    "sql": _norm([
        "sql", "structured query language", "sql querying"
    ]),

    # Data engineering & analytics
    "bigquery": _norm(["bigquery", "google bigquery", "gcp bigquery"]),
    "hive": _norm(["hive", "apache hive"]),
    "airflow": _norm(["airflow", "apache airflow", "airflow dag", "workflow orchestration"]),
    "kafka": _norm(["kafka", "apache kafka", "kafka streaming"]),
    "spark": _norm(["spark", "apache spark", "pyspark", "spark sql", "spark streaming", "structured streaming"]),
    "tableau": _norm(["tableau", "tableau desktop", "tableau server", "data visualization", "dashboard creation"]),
    "power_bi": _norm(["power bi", "microsoft power bi", "pbix"]),
    "excel": _norm([
        "microsoft excel", "excel", "ms excel", "spreadsheets", "xls", "xlsx",
        "pivot tables", "vlookup", "xlookup", "macros", "vba"
    ]),

    # ML & AI
    "machine_learning": _norm(["machine learning", "ml", "ml engineer", "ml models", "artificial intelligence", "ai"]),
    "deep_learning": _norm(["deep learning", "neural networks", "dl"]),
    "tensorflow": _norm(["tensorflow", "tf", "keras", "tensorflow keras"]),
    "pytorch": _norm(["pytorch", "torch", "pytorch lightning"]),
    "scikit_learn": _norm(["scikit-learn", "sklearn", "scikit learn"]),
    "nlp": _norm(["nlp", "natural language processing", "text mining", "nlp engineer"]),
    "computer_vision": _norm(["computer vision", "cv", "image processing"]),
    "data_science": _norm(["data science", "data scientist", "data analysis"]),
    "feature_engineering": _norm(["feature engineering", "feature selection"]),

    # Cloud & DevOps
    "aws": _norm(["aws", "amazon web services", "ec2", "s3", "lambda", "rds", "cloudformation", "cloudfront"]),
    "azure": _norm(["azure", "microsoft azure", "azure functions"]),
    "gcp": _norm(["gcp", "google cloud", "google cloud platform", "gcp cloud functions"]),
    "docker": _norm(["docker", "docker containers", "containerization", "docker compose", "dockerized"]),
    "kubernetes": _norm(["kubernetes", "k8s", "helm", "helm charts", "cluster"]),
    "terraform": _norm(["terraform", "infrastructure as code", "iac"]),
    "ansible": _norm(["ansible", "ansible automation"]),
    "jenkins": _norm(["jenkins", "jenkins pipeline", "ci/cd", "continuous integration", "continuous deployment"]),
    "github_actions": _norm(["github actions", "actions", "gha"]),
    "gitlab_ci": _norm(["gitlab ci", "gitlab pipelines"]),
    "circleci": _norm(["circleci", "circle ci"]),
    "prometheus": _norm(["prometheus", "monitoring prometheus"]),
    "grafana": _norm(["grafana", "grafana dashboards"]),
    "datadog": _norm(["datadog", "datadog monitoring"]),
    "splunk": _norm(["splunk", "splunk logging", "splunk es"]),
    "new_relic": _norm(["new relic", "newrelic", "application monitoring"]),

    # APIs & architecture
    "rest_api": _norm(["rest", "rest api", "restful", "restful api"]),
    "graphql": _norm(["graphql", "graphql api"]),
    "grpc": _norm(["grpc", "g rpc", "remote procedure calls"]),
    "microservices": _norm(["microservices", "microservices architecture", "service oriented architecture", "soa"]),
    "serverless": _norm(["serverless", "serverless architecture", "aws lambda", "azure functions", "gcp cloud functions"]),
    "event_driven_architecture": _norm(["event-driven", "event driven architecture", "eda"]),

    # Security & testing
    "application_security": _norm(["application security", "appsec", "secure coding", "owasp"]),
    "penetration_testing": _norm(["penetration testing", "pen testing", "ethical hacking"]),
    "siem": _norm(["siem", "security information and event management"]),
    "unit_testing": _norm(["unit testing", "unit tests", "test driven development", "tdd"]),
    "integration_testing": _norm(["integration testing", "integration tests"]),
    "selenium": _norm(["selenium", "selenium webdriver"]),
    "cypress": _norm(["cypress", "cypress.io", "end-to-end testing"]),
    "pytest": _norm(["pytest", "python testing", "py.test"]),
    "junit": _norm(["junit", "java unit testing"]),

    # Mobile & desktop
    "android": _norm(["android", "android sdk", "android developer", "android studio", "kotlin", "java"]),
    "ios": _norm(["ios", "ios developer", "xcode", "swift", "objective-c"]),
    "react_native": _norm(["react native", "react-native", "mobile react"]),
    "flutter": _norm(["flutter", "dart", "flutter mobile"]),
    "electron": _norm(["electron", "desktop apps", "electron js"]),

    # Business & soft skills
    "project_management": _norm(["project management", "pmp", "project planning", "project coordination", "agile", "scrum", "kanban", "waterfall"]),
    "leadership": _norm(["leadership", "team leadership", "team lead", "people management", "mentoring", "coaching"]),
    "communication": _norm(["communication", "communication skills", "verbal communication", "written communication", "presentation skills", "public speaking"]),
    "problem_solving": _norm(["problem solving", "critical thinking", "analytical thinking", "troubleshooting"]),
    "time_management": _norm(["time management", "prioritization", "task management"]),
    "negotiation": _norm(["negotiation", "deal closing", "negotiation skills"]),
    "stakeholder_management": _norm(["stakeholder management", "stakeholder engagement"]),
    "business_analysis": _norm(["business analysis", "ba", "business analyst", "requirements gathering"]),

    # Sales & marketing
    "seo": _norm(["seo", "search engine optimization", "organic search"]),
    "sem": _norm(["sem", "search engine marketing", "paid search", "ppc"]),
    "google_ads": _norm(["google ads", "adwords", "adwords campaigns"]),
    "facebook_ads": _norm(["facebook ads", "meta ads", "social ads"]),
    "content_marketing": _norm(["content marketing", "content strategy", "content creation"]),
    "copywriting": _norm(["copywriting", "copy writer", "ad copy", "content copy"]),
    "email_marketing": _norm(["email marketing", "email campaigns", "mailchimp", "sendgrid"]),
    "social_media": _norm(["social media", "social media management", "smm", "community management"]),
    "marketing_automation": _norm(["inbound marketing", "lead nurturing", "marketing automation"]),
    "marketing_analytics": _norm(["marketing analytics", "campaign analytics", "ga4", "google analytics"]),
    "crm": _norm(["crm", "customer relationship management", "hubspot", "salesforce"]),
    "lead_generation": _norm(["lead generation", "lead gen", "prospecting"]),
    "account_management": _norm(["account management", "client management", "customer success"]),
    "business_development": _norm(["business development", "bd", "bizdev"]),
    "retention": _norm(["customer retention", "churn reduction", "loyalty programs"]),
    "affiliate_marketing": _norm(["affiliate marketing", "partner marketing"]),
    "ecommerce_marketing": _norm(["ecommerce marketing", "shopify marketing", "marketplace marketing"]),

    # Finance & accounting
    "accounting": _norm(["accounting", "bookkeeping", "financial accounting", "general ledger", "gl accounting"]),
    "financial_reporting": _norm(["financial reporting", "ifrs reporting", "gaap reporting"]),
    "audit": _norm(["audit", "external audit", "internal audit", "auditor"]),
    "budgeting_forecasting": _norm(["budgeting", "forecasting", "financial planning", "fp&a"]),
    "financial_modeling": _norm(["financial modeling", "financial modelling", "excel financial models"]),
    "treasury": _norm(["treasury", "cash management", "liquidity management"]),
    "investment_analysis": _norm(["investment analysis", "portfolio management", "asset management"]),
    "risk_management": _norm(["risk management", "enterprise risk", "credit risk", "market risk"]),
    "quickbooks": _norm(["quickbooks", "intuit quickbooks", "qb"]),
    "sap_financials": _norm(["sap fi", "sap financials", "sap erp financial module"]),
    "oracle_financials": _norm(["oracle financials", "oracle ebs financials", "oracle erp"]),
    "accounts_payable": _norm(["accounts payable", "ap", "invoice processing"]),
    "accounts_receivable": _norm(["accounts receivable", "ar", "billing collections"]),
    "credit_analysis": _norm(["credit analysis", "credit underwriting"]),
    "finance_compliance": _norm(["financial compliance", "regulatory compliance", "finra", "sec compliance"]),

    # Healthcare
    "nursing": _norm(["rn", "registered nurse", "licensed nurse", "nursing"]),
    "lpn": _norm(["lpn", "licensed practical nurse", "licensed vocational nurse", "lpn lvn"]),
    "cna": _norm(["cna", "certified nursing assistant", "nursing aide"]),
    "emt": _norm(["emt", "emt-basic", "emergency medical technician"]),
    "paramedic": _norm(["paramedic", "advanced life support", "als"]),
    "cpr_bls": _norm(["cpr", "bls", "basic life support"]),
    "acls": _norm(["acls", "advanced cardiac life support"]),
    "pals": _norm(["pals", "pediatric advanced life support"]),
    "phlebotomy": _norm(["phlebotomy", "blood draw", "phlebotomist"]),
    "iv_therapy": _norm(["iv therapy", "intravenous therapy", "iv insertion"]),
    "wound_care": _norm(["wound care", "wound management", "dressing changes"]),
    "infection_control": _norm(["infection control", "aseptic technique", "infection prevention"]),
    "medication_admin": _norm(["medication administration", "med admin", "drug administration"]),
    "ekg_ecg": _norm(["ekg", "ecg", "electrocardiogram"]),
    "radiography": _norm(["xray", "radiography", "radiologic technician"]),
    "mri": _norm(["mri", "magnetic resonance imaging", "mri tech"]),
    "ct_scan": _norm(["ct scan", "computed tomography", "ct tech"]),
    "ultrasound": _norm(["ultrasound", "sonography", "ultrasound tech", "sono"]),
    "ehr": _norm(["ehr", "emr", "electronic health records", "health information management", "epic", "cerner", "eclinicalworks"]),
    "medical_coding": _norm(["medical coding", "cpt", "icd-10", "coding specialist"]),
    "medical_billing": _norm(["medical billing", "billing and coding", "medical claims"]),
    "clinical_research": _norm(["clinical research", "clinical trials", "gcp", "good clinical practice"]),
    "healthcare_quality": _norm(["quality in healthcare", "patient safety", "clinical governance"]),
    "telemedicine": _norm(["telemedicine", "telehealth", "telecare"]),

    # Manufacturing, construction, operations
    "lean_manufacturing": _norm(["lean manufacturing", "lean", "kaizen", "continuous improvement"]),
    "six_sigma": _norm(["six sigma", "6σ", "sixsigma", "lean six sigma", "black belt", "green belt"]),
    "quality_assurance": _norm(["quality assurance", "qa", "quality control", "qc"]),
    "root_cause_analysis": _norm(["root cause analysis", "rca", "fishbone", "5 why", "five why"]),
    "sop": _norm(["sop", "standard operating procedures", "process documentation"]),
    "cnc": _norm(["cnc", "cnc machining", "cnc operator"]),
    "cad_cam": _norm(["cad", "cam", "computer aided design", "autocad", "solidworks"]),
    "plc_programming": _norm(["plc programming", "programmable logic controller", "siemens s7", "allen bradley"]),
    "welding": _norm(["welding", "mig welding", "tig welding", "weld operator"]),
    "osha": _norm(["osha", "occupational safety and health", "safety compliance", "workplace safety"]),
    "construction_management": _norm(["construction management", "site management", "project superintendent"]),
    "equipment_operation": _norm(["heavy equipment operation", "excavator", "bulldozer", "forklift operator"]),
    "estimating": _norm(["construction estimating", "cost estimating", "quantity surveying"]),
    "blueprint_reading": _norm(["blueprint reading", "reading plans", "construction drawings"]),

    # Retail & hospitality
    "customer_service": _norm(["customer service", "customer support", "client relations", "customer care", "help desk"]),
    "pos": _norm(["pos", "point of sale", "pos systems", "register"]),
    "inventory_management": _norm(["inventory management", "stock control", "merchandise control", "warehouse management"]),
    "visual_merchandising": _norm(["visual merchandising", "merchandising", "store displays"]),
    "loss_prevention": _norm(["loss prevention", "shrinkage control", "asset protection"]),
    "hotel_operations": _norm(["hotel operations", "hotel management", "front desk", "concierge"]),
    "food_safety": _norm(["food safety", "hazard analysis", "haccp", "servsafe"]),
    "event_planning": _norm(["event planning", "event management", "banquet operations"]),
    "reservations": _norm(["reservations", "booking systems", "opera pms", "rezdy"]),
    "guest_relations": _norm(["guest relations", "guest services", "customer hospitality"]),

    # HR & legal
    "recruiting": _norm(["recruiting", "talent acquisition", "sourcing", "headhunting"]),
    "onboarding": _norm(["onboarding", "new hire orientation", "employee onboarding"]),
    "payroll": _norm(["payroll", "payroll processing", "adp", "payroll software"]),
    "benefits_admin": _norm(["benefits administration", "employee benefits", "health insurance admin"]),
    "employee_relations": _norm(["employee relations", "er", "workplace relations"]),
    "hr_compliance": _norm(["hr compliance", "labor law compliance", "employment law"]),
    "performance_management": _norm(["performance management", "performance reviews", "pdps"]),
    "employment_law": _norm(["employment law", "labor law", "workplace law"]),
    "litigation_support": _norm(["litigation support", "legal support", "paralegal"]),
    "legal_research": _norm(["legal research", "lexisnexis", "westlaw"]),

    # Tools, productivity, certifications
    "jira": _norm(["jira", "jira software", "atlassian jira", "issue tracking"]),
    "confluence": _norm(["confluence", "atlassian confluence", "wiki"]),
    "asana": _norm(["asana", "asana project management"]),
    "trello": _norm(["trello", "kanban board", "trello boards"]),
    "slack": _norm(["slack", "slack messaging"]),
    "microsoft_teams": _norm(["microsoft teams", "teams", "ms teams"]),
    "zoom": _norm(["zoom", "zoom meetings", "video conferencing"]),
    "google_workspace": _norm(["google workspace", "g suite", "gsuite", "gmail", "google drive"]),
    "microsoft_office": _norm(["microsoft office", "office 365", "ms office", "word", "powerpoint", "excel"]),
    "pmp": _norm(["pmp", "project management professional", "project management certification"]),
    "scrum_master": _norm(["scrum master", "csm", "scrum master certification"]),
    "prince2": _norm(["prince2", "prince 2", "prince2 practitioner"]),
    "safe_agile": _norm(["safe", "scaled agile", "safe agile", "scaling agile"]),
    "itil": _norm(["itil", "it service management", "itil framework"]),
    "security_plus": _norm(["security+", "comptia security+", "comptia security plus"]),
    "aws_solutions_architect": _norm(["aws certified solutions architect", "aws architect", "aws sa"]),
    "azure_administrator": _norm(["microsoft azure administrator", "azure admin", "azure administrator"]),
    "gcp_architect": _norm(["google cloud professional cloud architect", "gcp architect", "google cloud architect"]),
    "cisco_networking": _norm(["cisco", "cisco networking", "ccna", "network engineer"]),
    "tcp_ip": _norm(["tcp/ip", "networking", "routing", "switching"]),
    "voip": _norm(["voip", "voice over ip", "sip", "pbx"]),
    "ux_design": _norm(["ux", "user experience", "ux design", "user research"]),
    "ui_design": _norm(["ui", "user interface", "ui design", "visual design"]),
    "graphic_design": _norm(["graphic design", "adobe photoshop", "adobe illustrator", "indesign"]),
    "photoshop": _norm(["photoshop", "adobe photoshop", "ps"]),
    "illustrator": _norm(["illustrator", "adobe illustrator"]),
    "indesign": _norm(["indesign", "adobe indesign"]),
    "figma": _norm(["figma", "figma design", "ui prototyping"]),
    "sketch": _norm(["sketch", "sketch app"]),
    "invision": _norm(["invision", "invision prototyping"]),
}


def get_all_skills() -> List[str]:
    """Return all unique skill tokens across all categories (lowercased)."""
    collected: List[str] = []
    for synonyms in SKILL_SYNONYMS.values():
        collected.extend(synonyms)
    # Include canonical keys as searchable tokens
    collected.extend(SKill for SKill in SKILL_SYNONYMS.keys())
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