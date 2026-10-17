import json, math, os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

SCHOOLS = json.load(open("schools.json"))
BY_ID = {s["id"]: s for s in SCHOOLS}

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("MODEL", "gemini-2.0-flash")
llm = OpenAI(api_key=GEMINI_KEY,
             base_url="https://generativelanguage.googleapis.com/v1beta/openai/") if GEMINI_KEY else None

app = FastAPI(title="Compass305")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def km(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = (math.sin((lat2 - lat1) * p / 2) ** 2
         + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2)
    return 12742 * math.asin(math.sqrt(a))

@app.get("/schools")
def schools(lat: float, lon: float, grade: int | None = None, radius_km: float = 5, type: str | None = None):
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
    school_ids: list[str]

@app.post("/ask")
def ask(body: Ask):
    recs = [BY_ID[i] for i in body.school_ids if i in BY_ID][:5]
    if not recs:
        raise HTTPException(400, "pick at least one school")
    if not llm:
        return {"answer": "AI is off (no GEMINI_API_KEY set).", "cited_ids": []}
    prompt = ("Answer the family's question using ONLY these school records. "
              "If the answer isn't in them, say 'Not in our data.' "
              "Cite school ids in [brackets]. Reply in the language of the question.\n\n"
              f"RECORDS:\n{json.dumps(recs)}\n\nQUESTION: {body.question}")
    try:
        r = llm.chat.completions.create(model=MODEL, temperature=0,
                                        messages=[{"role": "user", "content": prompt}])
    except Exception as e:
        raise HTTPException(502, f"AI error: {e}")
    ans = r.choices[0].message.content
    return {"answer": ans, "cited_ids": [s["id"] for s in recs if s["id"] in ans]}
