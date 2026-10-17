import json, math, os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

SCHOOLS = json.load(open("schools.json"))
BY_ID = {s["id"]: s for s in SCHOOLS}

LLM_KEY = os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
MODEL = os.getenv("MODEL", "llama-3.3-70b-versatile")
llm = OpenAI(api_key=LLM_KEY, base_url=LLM_BASE_URL, timeout=20, max_retries=1) if LLM_KEY else None

app = FastAPI(title="Compass305")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def km(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = (math.sin((lat2 - lat1) * p / 2) ** 2
         + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2)
    return 12742 * math.asin(math.sqrt(a))

@app.get("/schools")
def schools(lat: float, lon: float, grade: str | None = None, radius_km: float = 5, type: str | None = None):
    g = (grade or "").strip().upper()
    if g in ("", "ANY", "ALL"):
        grade = None
    elif g in ("PK", "PREK", "VPK"):
        grade = -1
    elif g in ("K", "KG"):
        grade = 0
    else:
        try:
            grade = int(g)
        except ValueError:
            raise HTTPException(422, "grade must be PK, K, or 1-12")
    out = []
    for s in SCHOOLS:
        if s["lat"] is None or s["lon"] is None:
            continue
        if type and s["type"] != type:
            continue
        if grade is not None and s["grade_min"] is not None:
            if not (s["grade_min"] <= grade <= s["grade_max"]):
                continue
        d = km(lat, lon, s["lat"], s["lon"])
        if d <= radius_km:
            out.append({**s, "distance_km": round(d, 2)})
    return sorted(out, key=lambda s: s["distance_km"])[:50]

@app.get("/schools/{sid}")
def school(sid: str):
    if sid not in BY_ID:
        raise HTTPException(404, "not found")
    return BY_ID[sid]

class Ask(BaseModel):
    question: str
    school_ids: list[str] = []
    mode: str = "grounded"

@app.post("/ask")
def ask(body: Ask):
    if not llm:
        return {"answer": "AI is off (no LLM_API_KEY set).", "cited_ids": [], "found": False, "mode": body.mode}
    recs = [BY_ID[i] for i in body.school_ids if i in BY_ID][:5]
    if body.mode == "general":
        names = ", ".join(r["name"] for r in recs)
        prompt = ("You help families in Miami-Dade County, Florida understand schools. "
                  "Give a short, general, helpful answer (max 4 sentences) based on common knowledge "
                  "about Miami-Dade public and private schools. Do not invent specific facts about a named school; "
                  "if policies vary, say so and suggest contacting the school or dadeschools.net. "
                  "Reply in the language of the question."
                  + (f" Schools the family is looking at: {names}." if names else "")
                  + f"\n\nQUESTION: {body.question}")
    else:
        if not recs:
            raise HTTPException(400, "pick at least one school")
        prompt = ("Answer the family's question using ONLY these school records. "
                  "If the answer isn't in them, reply exactly 'Not in our data.' and nothing else. "
                  "Cite school ids in [brackets]. Reply in the language of the question.\n\n"
                  f"RECORDS:\n{json.dumps(recs)}\n\nQUESTION: {body.question}")
    try:
        r = llm.chat.completions.create(model=MODEL, temperature=0.2 if body.mode == "general" else 0,
                                        messages=[{"role": "user", "content": prompt}])
    except Exception as e:
        raise HTTPException(502, f"AI error: {e}")
    ans = (r.choices[0].message.content or "").strip()
    if body.mode == "general":
        return {"answer": ans, "cited_ids": [], "found": True, "mode": "general"}
    if ans.lower().startswith("not in our data"):
        return {"answer": "Not in our data.", "cited_ids": [], "found": False, "mode": "grounded"}
    cited = [s["id"] for s in recs if s["id"] in ans]
    return {"answer": ans, "cited_ids": cited, "found": bool(cited), "mode": "grounded"}
