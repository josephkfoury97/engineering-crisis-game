
import io
import json
import math
import os
import sqlite3
import time
import uuid
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlencode

import pandas as pd
import qrcode
import streamlit as st

try:
    from streamlit_sortables import sort_items
    SORTABLES_AVAILABLE = True
except Exception:
    SORTABLES_AVAILABLE = False

try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except Exception:
    SUPABASE_AVAILABLE = False


# ============================================================
# PAGE + DESIGN
# ============================================================
st.set_page_config(
    page_title="CHEN212 · Mission 01",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CSS = """
<style>
:root {
  --navy:#16324F;
  --blue:#2F6FA3;
  --pale:#EAF2F8;
  --ice:#F6F9FC;
  --line:#D7E2EC;
  --text:#17222D;
  --muted:#667788;
  --green:#1F7A5A;
  --amber:#B9770E;
  --red:#A93226;
}
html, body, [class*="css"] {font-family: Inter, "Segoe UI", Arial, sans-serif;}
.block-container {max-width: 1060px; padding-top: 1.0rem; padding-bottom: 2.0rem;}
[data-testid="stSidebar"] {background: var(--ice);}
h1,h2,h3 {color:var(--navy); letter-spacing:-0.02em;}
hr {border:none; border-top:1px solid var(--line); margin:1.2rem 0;}
.hero {
  background: linear-gradient(135deg, #16324F 0%, #2F6FA3 100%);
  color:white; padding:1.55rem 1.65rem; border-radius:20px;
  box-shadow:0 10px 26px rgba(22,50,79,.13); margin-bottom:1rem;
}
.hero h1 {color:white; margin:0 0 .25rem 0; font-size:2.05rem;}
.hero .sub {opacity:.88; font-size:1.03rem;}
.card {
  background:white; color:var(--text) !important;
  border:1px solid var(--line); border-radius:16px;
  padding:1rem 1.1rem; margin:.55rem 0;
}
.card *, .soft *, .mission * { color:inherit; }
.soft {
  background:var(--ice); color:var(--text) !important;
  border:1px solid var(--line); border-radius:14px;
  padding:.85rem 1rem; margin:.5rem 0;
}
.mission {
  background:#F7FAFD; color:var(--text) !important;
  border:1px solid #C9DCEB; border-left:5px solid var(--blue);
  border-radius:14px; padding:1rem 1.1rem; margin:.65rem 0;
}

/* Keep text readable inside light custom containers even when the device/browser
   uses dark mode. */
.card b, .card strong, .soft b, .soft strong, .mission b, .mission strong {
  color:var(--navy) !important;
}

/* Streamlit input fields: enforce a readable light field with dark text. */
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div,
div[data-baseweb="select"] > div {
  background-color:#FFFFFF !important;
  color:var(--text) !important;
}
input, textarea {
  color:var(--text) !important;
  -webkit-text-fill-color:var(--text) !important;
  caret-color:var(--text) !important;
}
input::placeholder, textarea::placeholder {
  color:#7A8997 !important;
  -webkit-text-fill-color:#7A8997 !important;
  opacity:1 !important;
}

/* Streamlit normally displays 'Press Ctrl+Enter to submit' under text areas.
   That instruction is not useful on phones, so hide it. */
[data-testid="InputInstructions"] {
  display:none !important;
}
.label {
  font-size:.78rem; letter-spacing:.08em; font-weight:800; text-transform:uppercase;
  color:var(--blue);
}
.big-number {font-size:2rem; font-weight:800; color:var(--navy);}
.pill {
  display:inline-block; border:1px solid #C9DCEB; background:#F7FAFD;
  padding:.28rem .62rem; border-radius:999px; font-size:.88rem; margin:.12rem .18rem .12rem 0;
}
.muted {color:var(--muted);}
.kicker {font-size:.82rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; color:#6D859B;}
.question-no {color:var(--blue); font-weight:800;}
.score-good {color:var(--green);font-weight:800;}
.score-mid {color:var(--amber);font-weight:800;}
.score-low {color:var(--red);font-weight:800;}
.small {font-size:.88rem;}
.center {text-align:center;}
div[data-testid="stButton"] > button {
  border-radius:11px; font-weight:700; min-height:2.75rem;
}
div[data-testid="stDownloadButton"] > button {border-radius:11px; font-weight:700;}
[data-testid="stMetricValue"] {color:var(--navy);}

/* Ensure widget labels and option text remain readable. */
[data-testid="stWidgetLabel"] p,
div[role="radiogroup"] label p,
div[data-baseweb="select"] *,
div[data-baseweb="popover"] * {
  color:var(--text) !important;
}

/* Keep Streamlit notification boxes readable. */
div[data-testid="stAlert"] {
  color:var(--text) !important;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

def hero(title, subtitle=""):
    st.markdown(
        f'<div class="hero"><div class="kicker" style="color:#D7E8F6">CHEN212 · CHEMICAL ENGINEERING I</div>'
        f'<h1>{title}</h1><div class="sub">{subtitle}</div></div>',
        unsafe_allow_html=True,
    )

def section_header(kicker, title, blurb=None):
    st.markdown(f'<div class="label">{kicker}</div>', unsafe_allow_html=True)
    st.header(title)
    if blurb:
        st.markdown(f'<div class="muted">{blurb}</div>', unsafe_allow_html=True)

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def qp(name, default=""):
    try:
        value = st.query_params.get(name, default)
        if isinstance(value, list):
            return value[0] if value else default
        return value
    except Exception:
        return default

VIEW = qp("view", "student")
RUN_FROM_URL = qp("run", "")


# ============================================================
# QUESTION BANK
# ============================================================
TAUGHT_SINGLE = [
    {
        "id":"T1","section":"Today's concepts","domain":"Scientist vs Engineer",
        "prompt":"Why does a new catalyst increase the reaction rate?",
        "options":["Primarily scientific","Primarily engineering","Could be either"],
        "correct":"Primarily scientific","points":1,
        "feedback":"The main goal is to understand why the phenomenon occurs."
    },
    {
        "id":"T2","section":"Today's concepts","domain":"Scientist vs Engineer",
        "prompt":"At what temperature should an industrial reactor operate to balance conversion, energy cost, and safety?",
        "options":["Primarily scientific","Primarily engineering","Could be either"],
        "correct":"Primarily engineering","points":1,
        "feedback":"This asks for a practical decision under several real-world constraints."
    },
    {
        "id":"T3","section":"Today's concepts","domain":"Scientist vs Engineer",
        "prompt":"Determine the molecular mechanism by which a pollutant binds to activated carbon.",
        "options":["Primarily scientific","Primarily engineering","Could be either"],
        "correct":"Primarily scientific","points":1,
        "feedback":"The emphasis is on explaining and understanding the phenomenon."
    },
    {
        "id":"T4","section":"Today's concepts","domain":"Scientist vs Engineer",
        "prompt":"Determine how much activated carbon is required to treat 5 million L/day of wastewater.",
        "options":["Primarily scientific","Primarily engineering","Could be either"],
        "correct":"Primarily engineering","points":1,
        "feedback":"This applies scientific knowledge to a process operating at useful scale."
    },
    {
        "id":"T5","section":"Today's concepts","domain":"Scientist vs Engineer",
        "prompt":"Develop a new catalyst and test whether it improves conversion.",
        "options":["Primarily scientific","Primarily engineering","Could be either"],
        "correct":"Could be either","points":1,
        "feedback":"Science and engineering overlap; the classification depends on the purpose and context."
    },
    {
        "id":"T6","section":"Today's concepts","domain":"Engineering judgment",
        "prompt":"A process works technically, but is extremely expensive and unsafe. Has the engineering problem been solved?",
        "options":["Yes","No"],
        "correct":"No","points":1,
        "feedback":"Technical feasibility alone is not enough: safety, economics, reliability and other constraints matter."
    },
]

MATCH_CARDS = {
    "Safety": "The reactor operates at extremely high pressure.",
    "Energy": "The process consumes a huge amount of electricity.",
    "Environment": "Large quantities of hazardous waste are produced.",
    "Cost": "The product can be manufactured, but costs $20/kg instead of $2/kg.",
}

SCALE_SINGLE = [
    {
        "id":"S1","section":"Scale-up","domain":"Scale-up",
        "prompt":"If every characteristic length of geometrically similar equipment increases by a factor of 10, approximately how much does its volume increase?",
        "options":["10×","100×","1000×","10,000×"],
        "correct":"1000×","points":1,
        "feedback":"Volume scales approximately with L³."
    },
    {
        "id":"S2","section":"Scale-up","domain":"Scale-up",
        "prompt":"What happens to the surface-area-to-volume ratio as geometrically similar equipment becomes larger?",
        "options":["It increases","It decreases","It stays constant","It becomes zero"],
        "correct":"It decreases","points":1,
        "feedback":"Surface area scales with L² while volume scales with L³."
    },
    {
        "id":"S3","section":"Scale-up","domain":"Scale-up",
        "prompt":"Why can this matter for a strongly exothermic reaction?",
        "options":[
            "The reaction automatically stops",
            "Heat may become harder to remove relative to the amount generated",
            "The reactor becomes weightless",
            "Pressure must become zero"
        ],
        "correct":"Heat may become harder to remove relative to the amount generated","points":1,
        "feedback":"A reaction that behaves safely in a small flask may become difficult to cool at large scale."
    },
]

DIAGNOSTIC = [
    # Math
    {"id":"M1","section":"Readiness diagnostic","domain":"Mathematics",
     "prompt":"Which is a correct scientific-notation form of 0.00045?",
     "options":["4.5 × 10⁻³","4.5 × 10⁻⁴","45 × 10⁻⁴","0.45 × 10⁻³"],
     "correct":"4.5 × 10⁻⁴"},
    {"id":"M2","section":"Readiness diagnostic","domain":"Mathematics",
     "prompt":"Given P = F/A, which expression correctly solves for A?",
     "options":["A = P/F","A = F/P","A = FP","A = 1/(FP)"],
     "correct":"A = F/P"},
    {"id":"M3","section":"Readiness diagnostic","domain":"Mathematics",
     "prompt":"A process uses 20 kg of raw material to produce 5 kg of product. If everything scales proportionally, how much raw material is needed for 50 kg of product?",
     "options":["50 kg","100 kg","200 kg","500 kg"],"correct":"200 kg"},
    {"id":"M4","section":"Readiness diagnostic","domain":"Mathematics",
     "prompt":"A mass flow-rate graph is plotted against time. What physical quantity does the area under the flow-rate-versus-time curve represent?",
     "options":["Mass transferred","Temperature","Pressure","Density"],"correct":"Mass transferred"},
    # Chemistry
    {"id":"C1","section":"Readiness diagnostic","domain":"Chemistry",
     "prompt":"For 2H₂ + O₂ → 2H₂O, if 4 mol H₂ react completely with enough O₂, how many mol H₂O can form?",
     "options":["1 mol","2 mol","4 mol","8 mol"],"correct":"4 mol"},
    {"id":"C2","section":"Readiness diagnostic","domain":"Chemistry",
     "prompt":"Which contains approximately the same number of molecules?",
     "options":["18 g H₂O and 44 g CO₂","18 g H₂O only","44 g CO₂ only","They cannot be compared"],
     "correct":"18 g H₂O and 44 g CO₂"},
    {"id":"C3","section":"Readiness diagnostic","domain":"Chemistry",
     "prompt":"A tank contains 20 kg ethanol and 80 kg water. What is the ethanol mass percentage?",
     "options":["10%","20%","25%","80%"],"correct":"20%"},
    {"id":"C4","section":"Readiness diagnostic","domain":"Chemistry",
     "prompt":"Salt water is separated into pure water and a concentrated salt solution. Is a chemical reaction necessarily required?",
     "options":["Yes","No","Only at high pressure","Not enough information"],"correct":"No"},
    # Physics
    {"id":"P1","section":"Readiness diagnostic","domain":"Physics",
     "prompt":"Two open tanks contain the same liquid. One tank is much deeper. At the bottom, which tank generally has the larger liquid pressure?",
     "options":["The deeper tank","The shallower tank","They are always equal","It depends only on total liquid volume"],
     "correct":"The deeper tank"},
    {"id":"P2","section":"Readiness diagnostic","domain":"Physics",
     "prompt":"Identical heaters deliver the same amount of energy. One heats 1 kg water and the other heats 10 kg water. Which generally experiences the larger temperature rise?",
     "options":["1 kg water","10 kg water","Exactly the same","Impossible to say in principle"],
     "correct":"1 kg water"},
    {"id":"P3","section":"Readiness diagnostic","domain":"Physics",
     "prompt":"Water flows steadily from a wider pipe section into a narrower pipe section. What generally happens to its average velocity?",
     "options":["It increases","It decreases","It stays exactly the same","It becomes zero"],"correct":"It increases"},
    # First balance
    {"id":"B1","section":"Readiness diagnostic","domain":"Process reasoning",
     "prompt":"100 kg/h enters a process. Two outlet streams leave. One is 70 kg/h. If nothing accumulates and there are no other streams, what should the second outlet be?",
     "options":["20 kg/h","30 kg/h","70 kg/h","170 kg/h"],"correct":"30 kg/h"},
]

PRIORITIES = [
    "How much raw material is available?",
    "What temperature and pressure are required?",
    "How much heat is released?",
    "What colour should the factory walls be?",
    "How will B be separated from unreacted material?",
    "Is the process economically viable?",
    "Who discovered the reaction?",
    "What hazards appear at large scale?",
]
PRIORITY_DEFENSIBLE = {
    "How much raw material is available?",
    "What temperature and pressure are required?",
    "How much heat is released?",
    "How will B be separated from unreacted material?",
    "Is the process economically viable?",
    "What hazards appear at large scale?",
}

PROCESS_TEXT = {
    "Process A": "98% conversion · very high pressure · high energy consumption · highest production rate · significant safety concern",
    "Process B": "92% conversion · moderate pressure · moderate energy use · safer · lower operating cost",
    "Process C": "85% conversion · low pressure · very low energy use · large amount of unreacted material",
}


# ============================================================
# DATA LAYER — SUPABASE IN PRODUCTION, SQLITE FALLBACK FOR DEMO
# ============================================================
def has_supabase():
    return (
        SUPABASE_AVAILABLE
        and "SUPABASE_URL" in st.secrets
        and "SUPABASE_KEY" in st.secrets
        and str(st.secrets["SUPABASE_URL"]).strip()
        and str(st.secrets["SUPABASE_KEY"]).strip()
    )

@st.cache_resource
def get_supabase():
    if not has_supabase():
        return None
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

SQLITE_PATH = "mission01_demo.sqlite3"

def sqlite_conn():
    conn = sqlite3.connect(SQLITE_PATH, check_same_thread=False, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS mission_runs(
        run_code TEXT PRIMARY KEY,
        title TEXT,
        is_open INTEGER,
        created_at TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS mission_sessions(
        session_id TEXT PRIMARY KEY,
        run_code TEXT,
        student_name TEXT,
        started_at TEXT,
        completed_at TEXT,
        current_stage TEXT,
        taught_score INTEGER DEFAULT 0,
        taught_max INTEGER DEFAULT 0,
        math_score INTEGER DEFAULT 0,
        math_max INTEGER DEFAULT 0,
        chemistry_score INTEGER DEFAULT 0,
        chemistry_max INTEGER DEFAULT 0,
        physics_score INTEGER DEFAULT 0,
        physics_max INTEGER DEFAULT 0,
        process_score INTEGER DEFAULT 0,
        process_max INTEGER DEFAULT 0,
        process_choice TEXT,
        process_reason TEXT,
        desired_info TEXT,
        confidence_math TEXT,
        confidence_chemistry TEXT,
        confidence_physics TEXT,
        confidence_problem_solving TEXT,
        confidence_units TEXT,
        review_topic TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS mission_responses(
        response_id TEXT PRIMARY KEY,
        session_id TEXT,
        run_code TEXT,
        student_name TEXT,
        question_id TEXT,
        section TEXT,
        domain TEXT,
        prompt TEXT,
        response_text TEXT,
        response_json TEXT,
        correct_answer TEXT,
        is_correct INTEGER,
        points REAL,
        max_points REAL,
        created_at TEXT,
        UNIQUE(session_id, question_id)
    )""")
    conn.commit()
    return conn

def db_mode():
    return "Supabase" if has_supabase() else "Local demo"

def ensure_run(run_code, title="Mission 01", is_open=True):
    if has_supabase():
        sb = get_supabase()
        sb.table("mission_runs").upsert({
            "run_code":run_code, "title":title, "is_open":is_open, "created_at":now_iso()
        }, on_conflict="run_code").execute()
    else:
        c = sqlite_conn()
        c.execute("""INSERT INTO mission_runs(run_code,title,is_open,created_at)
                     VALUES(?,?,?,?)
                     ON CONFLICT(run_code) DO UPDATE SET title=excluded.title,is_open=excluded.is_open""",
                  (run_code,title,1 if is_open else 0,now_iso()))
        c.commit()

def get_run(run_code):
    if has_supabase():
        data = get_supabase().table("mission_runs").select("*").eq("run_code",run_code).execute().data
        return data[0] if data else None
    c = sqlite_conn()
    row = c.execute("SELECT * FROM mission_runs WHERE run_code=?", (run_code,)).fetchone()
    return dict(row) if row else None

def start_session(run_code, student_name):
    sid = str(uuid.uuid4())
    row = {
        "session_id":sid, "run_code":run_code, "student_name":student_name.strip(),
        "started_at":now_iso(), "current_stage":"Started",
        "taught_score":0,"taught_max":0,
        "math_score":0,"math_max":0,"chemistry_score":0,"chemistry_max":0,
        "physics_score":0,"physics_max":0,"process_score":0,"process_max":0
    }
    if has_supabase():
        get_supabase().table("mission_sessions").insert(row).execute()
    else:
        c = sqlite_conn()
        cols = ",".join(row.keys()); placeholders=",".join(["?"]*len(row))
        c.execute(f"INSERT INTO mission_sessions({cols}) VALUES({placeholders})", tuple(row.values()))
        c.commit()
    return sid

def update_session(session_id, **fields):
    if not fields: return
    if has_supabase():
        get_supabase().table("mission_sessions").update(fields).eq("session_id",session_id).execute()
    else:
        c=sqlite_conn()
        sets=", ".join([f"{k}=?" for k in fields])
        c.execute(f"UPDATE mission_sessions SET {sets} WHERE session_id=?", tuple(fields.values())+(session_id,))
        c.commit()

def log_response(question_id, section, domain, prompt, response_text,
                 correct_answer=None, is_correct=None, points=0, max_points=0, response_json=None):
    sid = st.session_state.session_id
    if not sid:
        return
    row = {
        "response_id":str(uuid.uuid4()),
        "session_id":sid,
        "run_code":st.session_state.run_code,
        "student_name":st.session_state.student_name,
        "question_id":question_id,
        "section":section,
        "domain":domain,
        "prompt":prompt,
        "response_text":str(response_text),
        "response_json":json.dumps(response_json, ensure_ascii=False) if response_json is not None else None,
        "correct_answer":correct_answer,
        "is_correct":is_correct,
        "points":points,
        "max_points":max_points,
        "created_at":now_iso(),
    }
    if has_supabase():
        # Upsert by session_id + question_id (requires matching unique constraint)
        get_supabase().table("mission_responses").upsert(
            row, on_conflict="session_id,question_id"
        ).execute()
    else:
        c=sqlite_conn()
        c.execute("""INSERT INTO mission_responses(
            response_id,session_id,run_code,student_name,question_id,section,domain,prompt,
            response_text,response_json,correct_answer,is_correct,points,max_points,created_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(session_id,question_id) DO UPDATE SET
            response_text=excluded.response_text,response_json=excluded.response_json,
            correct_answer=excluded.correct_answer,is_correct=excluded.is_correct,
            points=excluded.points,max_points=excluded.max_points,created_at=excluded.created_at""",
            tuple(row.values()))
        c.commit()

def fetch_sessions(run_code):
    if has_supabase():
        data = get_supabase().table("mission_sessions").select("*").eq("run_code",run_code).order("started_at").execute().data
        return pd.DataFrame(data)
    c=sqlite_conn()
    rows=c.execute("SELECT * FROM mission_sessions WHERE run_code=? ORDER BY started_at", (run_code,)).fetchall()
    return pd.DataFrame([dict(r) for r in rows])

def fetch_responses(run_code, session_id=None):
    if has_supabase():
        q=get_supabase().table("mission_responses").select("*").eq("run_code",run_code)
        if session_id:
            q=q.eq("session_id",session_id)
        data=q.order("created_at").execute().data
        return pd.DataFrame(data)
    c=sqlite_conn()
    if session_id:
        rows=c.execute("SELECT * FROM mission_responses WHERE run_code=? AND session_id=? ORDER BY created_at",
                       (run_code,session_id)).fetchall()
    else:
        rows=c.execute("SELECT * FROM mission_responses WHERE run_code=? ORDER BY created_at",
                       (run_code,)).fetchall()
    return pd.DataFrame([dict(r) for r in rows])

def clear_run_data(run_code):
    if has_supabase():
        sb=get_supabase()
        sb.table("mission_responses").delete().eq("run_code",run_code).execute()
        sb.table("mission_sessions").delete().eq("run_code",run_code).execute()
    else:
        c=sqlite_conn()
        c.execute("DELETE FROM mission_responses WHERE run_code=?", (run_code,))
        c.execute("DELETE FROM mission_sessions WHERE run_code=?", (run_code,))
        c.commit()


# ============================================================
# SESSION HELPERS
# ============================================================
DEFAULT_STATE = {
    "page":0, "student_name":"", "session_id":None, "run_code":RUN_FROM_URL or "",
    "taught_score":0, "taught_max":0, "diag_answers":{}, "diagnostic_done":False,
}
for k,v in DEFAULT_STATE.items():
    if k not in st.session_state:
        st.session_state[k]=v

def advance(stage, page_delta=1):
    if st.session_state.session_id:
        update_session(st.session_state.session_id, current_stage=stage)
    st.session_state.page += page_delta
    st.rerun()

def nav_buttons(back=False, next_label="Continue →", next_disabled=False, stage=""):
    cols=st.columns([1,1])
    with cols[0]:
        if back and st.button("← Back", use_container_width=True):
            st.session_state.page=max(0,st.session_state.page-1); st.rerun()
    with cols[1]:
        if st.button(next_label, type="primary", use_container_width=True, disabled=next_disabled):
            advance(stage or next_label)

def submit_scored_single(q, key_prefix="ans"):
    key=f"{key_prefix}_{q['id']}"
    submitted=f"{key}_submitted"
    st.markdown(f"<span class='question-no'>{q['id']}</span> &nbsp; **{q['prompt']}**", unsafe_allow_html=True)
    choice=st.radio("Select one", q["options"], key=key, label_visibility="collapsed")
    if not st.session_state.get(submitted,False):
        if st.button("Check answer", key=f"btn_{key}", use_container_width=True):
            correct=choice==q["correct"]
            pts=q.get("points",1) if correct else 0
            st.session_state.taught_score += pts
            st.session_state.taught_max += q.get("points",1)
            st.session_state[submitted]=True
            log_response(q["id"],q["section"],q["domain"],q["prompt"],choice,q["correct"],correct,pts,q.get("points",1))
            update_session(st.session_state.session_id,
                           taught_score=st.session_state.taught_score,
                           taught_max=st.session_state.taught_max)
            st.rerun()
    else:
        if choice==q["correct"]:
            st.success("Correct · "+q["feedback"])
        else:
            st.error(f"Correct answer: **{q['correct']}** · {q['feedback']}")
    st.divider()

def qr_png_bytes(url):
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M,
                       box_size=10, border=4)
    qr.add_data(url); qr.make(fit=True)
    img=qr.make_image(fill_color="#16324F", back_color="white")
    buf=io.BytesIO(); img.save(buf,format="PNG"); return buf.getvalue()


# ============================================================
# INSTRUCTOR DASHBOARD
# ============================================================
def instructor_dashboard():
    hero("Instructor Control Room", "Mission 01 · live responses, readiness profile, exports and QR launch")
    pin_secret = str(st.secrets.get("INSTRUCTOR_PIN","2120"))
    if not st.session_state.get("instructor_ok",False):
        c1,c2=st.columns([2,1])
        with c1:
            pin=st.text_input("Instructor PIN", type="password", placeholder="Enter PIN")
        with c2:
            st.write(""); st.write("")
            if st.button("Unlock dashboard",type="primary",use_container_width=True):
                if pin==pin_secret:
                    st.session_state.instructor_ok=True; st.rerun()
                else:
                    st.error("Incorrect PIN.")
        st.caption("The PIN is stored in Streamlit Secrets, not in the student-facing URL.")
        return

    app_url_default=str(st.secrets.get("APP_URL","")).strip()
    if not app_url_default:
        app_url_default="https://YOUR-APP.streamlit.app/"
    if "dash_run" not in st.session_state:
        st.session_state.dash_run = str(st.secrets.get("DEFAULT_RUN","CHEN212-M01-F26"))
    if "dash_url" not in st.session_state:
        st.session_state.dash_url = app_url_default

    tabs=st.tabs(["Launch & QR","Live monitor","Student detail","Readiness snapshot","Export & manage"])
    with tabs[0]:
        section_header("Launch", "Create the student entry point")
        c1,c2=st.columns([1,1])
        with c1:
            st.session_state.dash_run=st.text_input("Run code",value=st.session_state.dash_run,
                                                   help="Use a new code each time you run the mission, e.g. CHEN212-M01-2026A.")
            st.session_state.dash_url=st.text_input("Deployed app URL",value=st.session_state.dash_url)
            open_state=st.toggle("Mission open to students", value=True)
            if st.button("Save / update this run",type="primary",use_container_width=True):
                ensure_run(st.session_state.dash_run,"Mission 01 · From Lab Bench to Chemical Plant",open_state)
                st.success("Run saved.")
        with c2:
            params=urlencode({"view":"student","run":st.session_state.dash_run})
            student_url=st.session_state.dash_url.rstrip("/")+"/?"+params
            st.markdown("**Student URL**")
            st.code(student_url,language=None)
            img=qr_png_bytes(student_url)
            st.image(img,width=280,caption="Students scan this code")
            st.download_button("Download QR as PNG",img,file_name=f"{st.session_state.dash_run}_QR.png",
                               mime="image/png",use_container_width=True)
            st.caption("The QR points directly to Student View and includes the run code.")

        paper_path=Path("assets/CHEN212_Engineering_Entry_Profile.pdf")
        if paper_path.exists():
            st.divider()
            st.markdown("**Printable paper component**")
            st.download_button("Download Engineering Entry Profile PDF",paper_path.read_bytes(),
                               file_name="CHEN212_Engineering_Entry_Profile.pdf",
                               mime="application/pdf")

    with tabs[1]:
        section_header("Live", "Monitor what each student is doing in real time")
        run=st.text_input("Monitor run",value=st.session_state.dash_run,key="monitor_run")
        @st.fragment(run_every="3s")
        def live_panel():
            sessions=fetch_sessions(run)
            responses=fetch_responses(run)
            a,b,c,d=st.columns(4)
            a.metric("Students",0 if sessions.empty else len(sessions))
            b.metric("Completed",0 if sessions.empty else int(sessions["completed_at"].notna().sum()))
            c.metric("Responses",0 if responses.empty else len(responses))
            if not sessions.empty and "started_at" in sessions:
                active=int((sessions["completed_at"].isna()).sum())
            else: active=0
            d.metric("In progress",active)
            if sessions.empty:
                st.info("No students have joined this run yet.")
                return
            show=sessions.copy()
            cols=["student_name","current_stage","taught_score","taught_max",
                  "math_score","math_max","chemistry_score","chemistry_max",
                  "physics_score","physics_max","process_score","process_max","completed_at"]
            show=show[[x for x in cols if x in show.columns]]
            show.columns=[x.replace("_"," ").title() for x in show.columns]
            st.dataframe(show,use_container_width=True,hide_index=True)
            if not responses.empty:
                st.markdown("**Most recent answers**")
                recent=responses.tail(12)[["student_name","section","question_id","response_text","is_correct","created_at"]].copy()
                recent.columns=["Student","Section","ID","Answer","Correct?","Time"]
                st.dataframe(recent.iloc[::-1],use_container_width=True,hide_index=True)
        live_panel()

    with tabs[2]:
        section_header("Student", "Inspect every response from one student")
        sessions=fetch_sessions(st.session_state.dash_run)
        if sessions.empty:
            st.info("No student sessions yet.")
        else:
            labels={f"{r.student_name} · {r.session_id[:8]}":r.session_id for _,r in sessions.iterrows()}
            sel=st.selectbox("Student",list(labels.keys()))
            sid=labels[sel]
            row=sessions[sessions["session_id"]==sid].iloc[0]
            c1,c2,c3,c4=st.columns(4)
            c1.metric("Taught",f"{int(row.get('taught_score',0) or 0)}/{int(row.get('taught_max',0) or 0)}")
            c2.metric("Math",f"{int(row.get('math_score',0) or 0)}/{int(row.get('math_max',0) or 0)}")
            c3.metric("Chemistry",f"{int(row.get('chemistry_score',0) or 0)}/{int(row.get('chemistry_max',0) or 0)}")
            c4.metric("Physics",f"{int(row.get('physics_score',0) or 0)}/{int(row.get('physics_max',0) or 0)}")
            res=fetch_responses(st.session_state.dash_run,sid)
            if not res.empty:
                detail=res[["section","domain","question_id","prompt","response_text","correct_answer","is_correct"]].copy()
                detail.columns=["Section","Domain","ID","Question","Student answer","Expected answer","Correct?"]
                st.dataframe(detail,use_container_width=True,hide_index=True,height=520)
            st.markdown("**Engineering decision**")
            st.write("Recommendation:",row.get("process_choice") or "—")
            st.write("Reasoning:",row.get("process_reason") or "—")
            st.write("Information requested:",row.get("desired_info") or "—")
            st.markdown("**Self-reported confidence / review request**")
            st.write({
                "Mathematics":row.get("confidence_math"),
                "Chemistry":row.get("confidence_chemistry"),
                "Physics":row.get("confidence_physics"),
                "Problem solving":row.get("confidence_problem_solving"),
                "Units & conversions":row.get("confidence_units"),
                "Topic they hope to review":row.get("review_topic"),
            })

    with tabs[3]:
        section_header("Diagnostic", "A class-level starting-point snapshot")
        sessions=fetch_sessions(st.session_state.dash_run)
        if sessions.empty:
            st.info("No diagnostic data yet.")
        else:
            for domain,score_col,max_col in [
                ("Mathematics","math_score","math_max"),
                ("Chemistry","chemistry_score","chemistry_max"),
                ("Physics","physics_score","physics_max"),
                ("Process reasoning","process_score","process_max"),
            ]:
                s=pd.to_numeric(sessions.get(score_col,0),errors="coerce").fillna(0)
                m=pd.to_numeric(sessions.get(max_col,0),errors="coerce").fillna(0)
                valid=m>0
                pct=float((s[valid].sum()/m[valid].sum())*100) if valid.any() else 0.0
                st.markdown(f"**{domain} · {pct:.0f}% class accuracy**")
                st.progress(min(max(pct/100,0),1))
            st.divider()
            st.markdown("**Question-level accuracy**")
            res=fetch_responses(st.session_state.dash_run)
            if not res.empty:
                diag=res[res["section"]=="Readiness diagnostic"].copy()
                if not diag.empty:
                    diag["correct_num"]=pd.to_numeric(diag["is_correct"],errors="coerce")
                    summary=(diag.groupby(["domain","question_id","prompt"],dropna=False)
                              .agg(Attempts=("response_id","count"),Accuracy=("correct_num","mean"))
                              .reset_index())
                    summary["Accuracy"]=summary["Accuracy"].map(lambda x:f"{100*x:.0f}%" if pd.notna(x) else "—")
                    st.dataframe(summary,use_container_width=True,hide_index=True)

    with tabs[4]:
        section_header("Data", "Export or reset a run")
        run=st.text_input("Run code",value=st.session_state.dash_run,key="manage_run")
        sessions=fetch_sessions(run); responses=fetch_responses(run)
        c1,c2=st.columns(2)
        with c1:
            st.download_button("Download session summary CSV",
                               sessions.to_csv(index=False).encode("utf-8"),
                               file_name=f"{run}_sessions.csv",mime="text/csv",
                               disabled=sessions.empty,use_container_width=True)
        with c2:
            st.download_button("Download all responses CSV",
                               responses.to_csv(index=False).encode("utf-8"),
                               file_name=f"{run}_responses.csv",mime="text/csv",
                               disabled=responses.empty,use_container_width=True)
        st.divider()
        st.warning("Reset permanently deletes student responses for this run.")
        confirm=st.text_input(f"Type RESET {run} to enable deletion")
        if st.button("Delete this run's student data",disabled=confirm!=f"RESET {run}"):
            clear_run_data(run); st.success("Student data deleted."); time.sleep(.4); st.rerun()
        st.caption(f"Backend currently in use: {db_mode()}.")


# ============================================================
# STUDENT EXPERIENCE
# ============================================================
def student_app():
    run = st.session_state.run_code or RUN_FROM_URL
    if not run:
        hero("Mission 01", "This link is missing a class run code.")
        st.error("Please scan the QR code shown by your instructor.")
        return

    existing_run=get_run(run)
    if existing_run is not None and not bool(existing_run.get("is_open",1)):
        hero("Mission 01", "This mission is currently closed.")
        st.info("Your instructor has not opened this run yet.")
        return

    p=st.session_state.page

    # PAGE 0 — Welcome
    if p==0:
        hero("MISSION 01 · From Lab Bench to Chemical Plant", "Your first CHEN212 engineering mission")
        st.markdown("""
<div class="mission">
<div class="label">Briefing</div>
A laboratory discovery looks promising. Management now wants to turn it into an industrial process.

Your job is not simply to find a number. Your job is to decide **what matters**, question assumptions,
and use evidence like an engineer.
</div>
""",unsafe_allow_html=True)
        c1,c2,c3=st.columns(3)
        c1.markdown("<div class='soft'><b>01 · Today's knowledge</b><br><span class='muted'>Scientist vs engineer, judgment, constraints</span></div>",unsafe_allow_html=True)
        c2.markdown("<div class='soft'><b>02 · Scale-up</b><br><span class='muted'>What changes between flask and plant?</span></div>",unsafe_allow_html=True)
        c3.markdown("<div class='soft'><b>03 · Readiness diagnostic</b><br><span class='muted'>Math, chemistry, physics, process reasoning</span></div>",unsafe_allow_html=True)
        st.info("The readiness diagnostic is **not graded**. Some questions cover material that has not yet been taught in CHEN212. Answer from what you remember.")
        name=st.text_input("Your first name",placeholder="Type your name",key="student_name_entry")
        consent=st.checkbox("I understand that my answers will be visible to my instructor for teaching and feedback.")
        if st.button("Begin mission →",type="primary",use_container_width=True,disabled=not(name.strip() and consent)):
            st.session_state.student_name=name.strip()
            st.session_state.run_code=run
            if existing_run is None:
                ensure_run(run,"Mission 01 · From Lab Bench to Chemical Plant",True)
            st.session_state.session_id=start_session(run,name.strip())
            st.session_state.page=1; st.rerun()

    # PAGE 1 — Taught knowledge
    elif p==1:
        hero("Part I · Today's Knowledge", "First: can you recognize the ideas we have just discussed?")
        st.progress(0.12)
        section_header("Quickfire", "Scientist or Engineer?")
        st.caption("These questions are formative. Submit each one to see immediate feedback.")
        for q in TAUGHT_SINGLE:
            submit_scored_single(q)
        nav_buttons(next_label="Go to matching challenge →",stage="Matching challenge")

    # PAGE 2 — Matching
    elif p==2:
        hero("Part I · Match the Engineering Concern", "Connect each observation to the constraint it most directly raises")
        st.progress(0.23)
        if SORTABLES_AVAILABLE:
            st.markdown("**Drag each observation into the most appropriate category.**")
            init=[
                {"header":"Unsorted","items":list(MATCH_CARDS.values())},
                {"header":"Safety","items":[]},
                {"header":"Energy","items":[]},
                {"header":"Environment","items":[]},
                {"header":"Cost","items":[]},
            ]
            result=sort_items(init,multi_containers=True,direction="vertical",key="constraint_drag")
            st.caption("On a phone, press and drag a card. If dragging is difficult, use the fallback below.")
            use_fallback=st.checkbox("Use dropdown matching instead")
        else:
            result=None; use_fallback=True
            st.info("Drag-and-drop component is unavailable, so dropdown matching is shown instead.")

        matches={}
        if not SORTABLES_AVAILABLE or use_fallback:
            for category, card in MATCH_CARDS.items():
                matches[category]=st.selectbox(card,["— choose —"]+list(MATCH_CARDS.keys()),
                                               key=f"match_{category}")
        else:
            # result is list of dicts, read category placements
            for bucket in result:
                header=bucket.get("header")
                for item in bucket.get("items",[]):
                    if header!="Unsorted":
                        matches[item]=header

        if st.button("Submit matching challenge",type="primary",use_container_width=True):
            correct_n=0
            if not SORTABLES_AVAILABLE or use_fallback:
                detail={}
                for category,card in MATCH_CARDS.items():
                    ans=matches.get(category)
                    ok=ans==category
                    correct_n+=int(ok)
                    detail[card]=ans
            else:
                detail={}
                reverse={v:k for k,v in MATCH_CARDS.items()}
                for card,placed in matches.items():
                    expected=reverse.get(card)
                    ok=placed==expected
                    correct_n+=int(ok)
                    detail[card]=placed
            maxp=4
            st.session_state.taught_score += correct_n
            st.session_state.taught_max += maxp
            log_response("MATCH1","Today's concepts","Engineering constraints",
                         "Match each process observation to Safety, Energy, Environment, or Cost.",
                         f"{correct_n}/4 correct", "4/4 correct", correct_n==4, correct_n,maxp,detail)
            update_session(st.session_state.session_id,taught_score=st.session_state.taught_score,taught_max=st.session_state.taught_max)
            st.session_state.match_result=(correct_n,detail)
            st.rerun()
        if "match_result" in st.session_state:
            n,_=st.session_state.match_result
            if n==4: st.success("Excellent — 4/4. You connected the observations to the engineering constraints.")
            else: st.warning(f"You matched {n}/4 correctly. High pressure → Safety; electricity → Energy; hazardous waste → Environment; product price → Cost.")
            nav_buttons(next_label="Enter the scale-up challenge →",stage="Scale-up challenge")

    # PAGE 3 — Scale up priorities + scored
    elif p==3:
        hero("Part II · Scale-Up Challenge", "A successful flask is not yet an industrial process")
        st.progress(0.36)
        st.markdown("""
<div class="mission">
<div class="label">Lab success</div>
A chemist has developed <b>A → B</b> in a <b>100 mL</b> reactor and obtains <b>95% conversion</b>.

The CEO says: <b>“Excellent. Build a plant that produces 500 tonnes of B per day.”</b>
</div>
""",unsafe_allow_html=True)
        section_header("Challenge A", "What would you investigate before approving scale-up?")
        picks=st.multiselect("Select exactly FIVE issues you would investigate first:",PRIORITIES,key="priority_pick")
        if st.button("Lock in my five",use_container_width=True,disabled=len(picks)!=5):
            pts=sum(1 for x in picks if x in PRIORITY_DEFENSIBLE)
            # cap at 5; the point is judgment, not one magic list
            pts=min(pts,5)
            st.session_state.taught_score+=pts; st.session_state.taught_max+=5
            log_response("S0","Scale-up","Engineering judgment",
                         "Select five issues to investigate before scale-up.",", ".join(picks),
                         "Several answers are defensible; focus on feed, conditions, heat, separation, economics and hazards.",
                         None,pts,5,picks)
            update_session(st.session_state.session_id,taught_score=st.session_state.taught_score,taught_max=st.session_state.taught_max)
            st.session_state.priority_done=True; st.rerun()
        if st.session_state.get("priority_done"):
            st.success("Good engineering questions include feed availability, operating conditions, heat removal, separations, economics and hazards. There is not one magical list.")
            for q in SCALE_SINGLE:
                submit_scored_single(q,key_prefix="scale")
            nav_buttons(next_label="Make an engineering recommendation →",stage="Engineering decision")

    # PAGE 4 — Engineering decision
    elif p==4:
        hero("Part III · Engineering Decision", "Three processes. No perfect option.")
        st.progress(0.51)
        c1,c2,c3=st.columns(3)
        for c,name in zip([c1,c2,c3],["Process A","Process B","Process C"]):
            with c:
                st.markdown(f"<div class='card'><div class='label'>{name}</div>{PROCESS_TEXT[name]}</div>",unsafe_allow_html=True)
        st.info("This part is judged on your reasoning, not on choosing a predetermined 'correct' process.")
        choice=st.radio("Which process would you recommend initially?",list(PROCESS_TEXT.keys()),horizontal=True)
        reason=st.text_area("Give your TWO strongest reasons.",placeholder="1. ...\n2. ...",height=110)
        info=st.text_input("What ONE additional piece of information would you request before final approval?",
                           placeholder="e.g., capital cost, required production rate, recycle feasibility...")
        if st.button("Submit recommendation →",type="primary",use_container_width=True,
                     disabled=len(reason.strip())<20 or len(info.strip())<4):
            log_response("D1","Engineering decision","Engineering judgment",
                         "Which process would you recommend and why?",choice,None,None,0,0,
                         {"choice":choice,"reason":reason,"desired_information":info})
            update_session(st.session_state.session_id,process_choice=choice,process_reason=reason,desired_info=info)
            st.session_state.page=5; update_session(st.session_state.session_id,current_stage="Readiness diagnostic"); st.rerun()

    # PAGE 5 — Diagnostic intro
    elif p==5:
        hero("Part IV · Engineering Readiness Diagnostic", "What tools are already in your engineering toolbox?")
        st.progress(0.60)
        st.markdown("""
<div class="mission">
<div class="label">Important</div>
The next questions are <b>not graded</b>. Some involve material that will appear later in CHEN212 or in later engineering courses.

Do not search the internet. Do not worry if you do not know something. Your instructor wants an honest picture of the class starting point.
</div>
""",unsafe_allow_html=True)
        st.markdown("""
<span class="pill">Mathematics</span>
<span class="pill">Chemistry</span>
<span class="pill">Physics</span>
<span class="pill">Process reasoning</span>
""",unsafe_allow_html=True)
        if st.button("Start diagnostic →",type="primary",use_container_width=True):
            st.session_state.page=6; st.rerun()

    # PAGE 6 — Diagnostic all questions, no immediate answers
    elif p==6:
        hero("Part IV · Readiness Diagnostic", "Answer from memory — results are for teaching, not grading")
        st.progress(0.72)
        answers={}
        domains=["Mathematics","Chemistry","Physics","Process reasoning"]
        for domain in domains:
            st.subheader(domain)
            for q in [x for x in DIAGNOSTIC if x["domain"]==domain]:
                st.markdown(f"<span class='question-no'>{q['id']}</span> &nbsp; **{q['prompt']}**",unsafe_allow_html=True)
                answers[q["id"]]=st.radio("Select one",q["options"],key=f"diag_{q['id']}",label_visibility="collapsed",index=None)
                st.divider()
        st.warning("Once submitted, the diagnostic answers are locked.")
        all_answered = all(v is not None for v in answers.values())
        if st.button("Submit diagnostic →",type="primary",use_container_width=True,disabled=not all_answered):
            scores={d:[0,0] for d in domains}
            for q in DIAGNOSTIC:
                ans=answers[q["id"]]
                ok=ans==q["correct"]
                scores[q["domain"]][0]+=int(ok); scores[q["domain"]][1]+=1
                log_response(q["id"],q["section"],q["domain"],q["prompt"],ans,q["correct"],ok,int(ok),1)
            update_session(
                st.session_state.session_id,
                math_score=scores["Mathematics"][0],math_max=scores["Mathematics"][1],
                chemistry_score=scores["Chemistry"][0],chemistry_max=scores["Chemistry"][1],
                physics_score=scores["Physics"][0],physics_max=scores["Physics"][1],
                process_score=scores["Process reasoning"][0],process_max=scores["Process reasoning"][1],
                current_stage="Self-reflection"
            )
            st.session_state.diag_scores=scores
            st.session_state.page=7; st.rerun()

    # PAGE 7 — Reflection + private profile
    elif p==7:
        hero("Part V · Your Starting Profile", "A private snapshot — not a grade")
        st.progress(0.86)
        scores=st.session_state.get("diag_scores",{})
        if scores:
            cols=st.columns(4)
            for col,domain in zip(cols,["Mathematics","Chemistry","Physics","Process reasoning"]):
                sc,mx=scores[domain]
                col.metric(domain,f"{sc}/{mx}")
        st.caption("These numbers simply show today's starting point. They help your instructor decide where the class needs review.")
        st.divider()
        section_header("Reflection", "How confident do you currently feel?")
        conf_options=["Very confident","Fairly confident","Unsure","Not confident yet"]
        conf={}
        for area in ["Mathematics","Chemistry","Physics","Problem solving","Units & conversions"]:
            conf[area]=st.select_slider(area,options=conf_options,value="Unsure",key=f"conf_{area}")
        review=st.text_input("One topic from school/university that you hope we review:",
                             placeholder="e.g., moles, rearranging equations, scientific notation...")
        st.markdown("**One question before we move on:**")
        unfamiliar=st.text_area(
            "You see an unfamiliar chemical plant for the first time. Write THREE questions you would ask before trying to understand how it works.",
            placeholder="1. ...\n2. ...\n3. ...",height=115
        )
        if st.button("Save my profile →",type="primary",use_container_width=True,
                     disabled=len(unfamiliar.strip())<15):
            log_response("R1","Reflection","Engineering thinking",
                         "Three questions you would ask before trying to understand an unfamiliar chemical plant.",
                         unfamiliar,None,None,0,0)
            update_session(
                st.session_state.session_id,
                confidence_math=conf["Mathematics"],confidence_chemistry=conf["Chemistry"],
                confidence_physics=conf["Physics"],confidence_problem_solving=conf["Problem solving"],
                confidence_units=conf["Units & conversions"],review_topic=review,
                current_stage="Paper engineering memo"
            )
            st.session_state.page=8; st.rerun()

    # PAGE 8 — paper component
    elif p==8:
        hero("Final Step · Engineering Entry Profile", "Now move from the phone to paper")
        st.progress(0.94)
        st.markdown("""
<div class="mission">
<div class="label">Professional paper component</div>
Your instructor will give you an <b>Engineering Entry Profile</b> sheet.

Complete it individually and hand it in before you leave.
</div>
""",unsafe_allow_html=True)
        st.markdown("""
The paper asks you to:
1. record and justify your process recommendation;
2. detect what is impossible in a simple factory mass-flow claim;
3. write three questions you would ask about an unfamiliar plant;
4. identify an area you would like reviewed.
""")
        st.info("Do not copy your phone answers word-for-word. The paper is your concise engineering memo.")
        st.markdown("### One last black-box thought")
        st.markdown("""
**100 kg/h feed → PROCESS → 70 kg/h product + ?**

If nothing accumulates and there are no other streams, the missing stream is **30 kg/h**.

**You have just used the logic of your first material balance.**
""")
        st.markdown("""
<div class="soft"><b>Keep this question in mind:</b><br>
How can an engineer know what is happening inside a process if we cannot see inside every pipe, tank and reactor?
</div>
""",unsafe_allow_html=True)
        if st.button("Finish Mission 01 ✓",type="primary",use_container_width=True):
            update_session(st.session_state.session_id,completed_at=now_iso(),current_stage="Completed")
            st.session_state.page=9; st.rerun()

    elif p==9:
        hero("Mission 01 Complete ✓", "From scientific discovery to engineering thinking")
        st.progress(1.0)
        st.success("Thank you. Your instructor now has your digital responses, and your paper Engineering Entry Profile completes the activity.")
        st.markdown("""
Today you have already used several habits that will return throughout CHEN212:

- distinguish understanding from application;
- question whether a process is practical;
- recognize scale-up consequences;
- use scientific and mathematical foundations;
- reason about flows into and out of a process.
""")
        st.markdown("**Next:** The Engineering Team.")
        st.caption("You may close this page.")

if VIEW=="instructor":
    instructor_dashboard()
else:
    student_app()
