import json
import os
import random
import time
import socket
import base64
from io import BytesIO
from datetime import datetime
from urllib.parse import urlencode

import streamlit as st

try:
    import qrcode
except Exception:
    qrcode = None

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    st_autorefresh = None

DATA_FILE = "leaderboard.json"
QUESTION_TIME = 15
QUESTIONS_PER_LEVEL = 15
TOTAL_LEVELS = 3

st.set_page_config(
    page_title="Can You Think Like an Engineer?",
    page_icon="⚙️",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
:root{
  --bg1:#07111f; --bg2:#020617; --card:#0f172a; --card2:#111827;
  --accent:#f97316; --gold:#facc15; --red:#ef4444; --green:#22c55e;
  --blue:#2563eb; --purple:#7c3aed; --cyan:#06b6d4; --text:#f8fafc; --muted:#cbd5e1;
}
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"],
[data-testid="stToolbar"], [data-testid="stDecoration"]{
  background: radial-gradient(circle at 50% -10%, #1e3a8a 0%, #07111f 45%, #020617 100%) !important;
  color: var(--text) !important;
}
[data-testid="stHeader"]{background: transparent !important; height:0rem !important; visibility:hidden !important;}
[data-testid="stToolbar"]{background: transparent !important;}
[data-testid="stSidebar"]{background:#050b16 !important; border-right:1px solid rgba(255,255,255,0.15);}
[data-testid="stSidebar"] *{color:#fff !important;}
.block-container{padding-top:0.7rem !important; max-width:980px;}
h1,h2,h3,h4,h5,h6,p,label,span,div{color:var(--text) !important;}
.big-title{text-align:center;font-size:2.55rem;font-weight:950;letter-spacing:-0.045em;margin-bottom:0.25rem;}
.subtitle{text-align:center;color:var(--muted) !important;font-size:1.03rem;margin-bottom:1rem;}
.big-card,.level-card,.memory-box{
  background:linear-gradient(145deg, rgba(255,255,255,0.115), rgba(255,255,255,0.045));
  padding:1.15rem 1.25rem;border-radius:22px;border:1px solid rgba(255,255,255,0.18);
  box-shadow:0 16px 40px rgba(0,0,0,0.34);margin:0.5rem 0 1rem 0;
}
.level-card{background:#0f172a;border-left:5px solid var(--accent);}
.memory-box{background:#172554;border:1px solid rgba(250,204,21,0.55);}
.score-pill{text-align:center;font-size:1.03rem;font-weight:850;background:rgba(255,255,255,0.10);border:1px solid rgba(255,255,255,0.15);padding:0.55rem 0.9rem;border-radius:999px;margin-bottom:0.75rem;}
.stage-pill{text-align:center;font-size:1.00rem;font-weight:850;background:rgba(249,115,22,0.16);border:1px solid rgba(249,115,22,0.30);padding:0.45rem 0.8rem;border-radius:999px;margin-bottom:0.55rem;}
.small-note{color:var(--muted) !important;font-size:0.94rem;}
.good{color:#bbf7d0 !important;font-weight:900;}.danger{color:#fecaca !important;font-weight:900;}.gold{color:#fde68a !important;font-weight:900;}
/* Dark non-white buttons */
div.stButton > button, button[kind="secondary"], button[kind="primary"]{
  width:100%;min-height:3.15rem;font-size:1.01rem;border-radius:15px;
  border:1px solid rgba(255,255,255,0.26) !important;
  background:linear-gradient(135deg, #1d4ed8 0%, #6d28d9 100%) !important;
  color:#ffffff !important;font-weight:850 !important;box-shadow:0 9px 22px rgba(0,0,0,0.35);
}
div.stButton > button:hover{filter:brightness(1.16);border-color:#fff !important;transform:translateY(-1px);}
div.stButton > button:active{transform:scale(0.985);}
div.stButton > button p, div.stButton > button span{color:#ffffff !important;font-weight:850 !important;}
.stTextInput input{background:#0b1220 !important;color:#ffffff !important;border:1px solid rgba(255,255,255,0.3) !important;border-radius:13px !important;font-weight:800;}
[data-testid="stAlert"]{background:rgba(255,255,255,0.10) !important;color:#fff !important;border:1px solid rgba(255,255,255,0.16) !important;}
[data-testid="stAlert"] *{color:#fff !important;}
[data-testid="stMetricValue"],[data-testid="stMetricLabel"],[data-testid="stMetricDelta"]{color:#fff !important;}
.qr-wrap{display:flex;gap:1rem;align-items:center;justify-content:center;flex-wrap:wrap;margin:0.75rem 0 1.1rem 0;}
.qr-card{background:#fff;padding:12px;border-radius:18px;box-shadow:0 10px 25px rgba(0,0,0,0.30);}
.link-box{background:rgba(255,255,255,0.10);border:1px solid rgba(255,255,255,0.18);border-radius:16px;padding:0.9rem 1rem;word-break:break-all;font-weight:900;text-align:center;}
#MainMenu, footer{visibility:hidden;}

.link-button {
    display:block;
    text-align:center;
    padding:0.75rem 1rem;
    border-radius:14px;
    background:linear-gradient(135deg,#2563eb,#7c3aed);
    color:#ffffff !important;
    font-weight:800;
    text-decoration:none !important;
    border:1px solid rgba(255,255,255,0.25);
    box-shadow:0 8px 20px rgba(37,99,235,0.25);
}
.link-button:hover { filter:brightness(1.08); }
</style>
""",
    unsafe_allow_html=True,
)

# -------------------- Leaderboard --------------------
def load_scores():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _name_key(name):
    return " ".join(str(name or "").strip().split()).casefold()


def save_score(entry):
    """Save/update a score while keeping one leaderboard row per player name.

    If the same name plays again, their previous row is replaced by the newest
    score. This keeps the live leaderboard clean during the event.
    """
    entry["name"] = " ".join(str(entry.get("name", "Player")).strip().split()) or "Player"
    new_key = _name_key(entry["name"])
    scores = [s for s in load_scores() if _name_key(s.get("name")) != new_key]
    scores.append(entry)
    scores = sorted(scores, key=lambda x: x.get("score", 0), reverse=True)[:150]
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2, ensure_ascii=False)
    os.replace(tmp, DATA_FILE)


def get_local_ip():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


def get_secret_or_env(name, default=""):
    """Read from Streamlit secrets first, then environment variables."""
    try:
        value = st.secrets.get(name, "")
        if value:
            return str(value).strip()
    except Exception:
        pass
    return str(os.environ.get(name, default)).strip()


def normalize_url(url):
    url = str(url or "").strip()
    if not url:
        return ""
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url
    return url.rstrip("/")


def public_play_url(base_url):
    base = normalize_url(base_url)
    if not base:
        return ""
    # Query parameter forces the player screen on phones even if the app later opens with defaults.
    return base + "?" + urlencode({"view": "play"})


def public_host_url(base_url):
    base = normalize_url(base_url)
    if not base:
        return ""
    return base + "?" + urlencode({"view": "host"})


def make_qr_data_uri(text):
    if qrcode is None:
        return None
    img = qrcode.make(text)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


PERSONAS = [
    (5200, "Legendary Chief Engineer 🧠"),
    (4300, "Crisis Commander 🚨"),
    (3300, "Process Optimization Pro ⚙️"),
    (2300, "Safety-First Engineer 🦺"),
    (1300, "Promising Future Engineer 🌱"),
    (0, "Engineer in Training 🔧"),
]

RULES = [
    {"forbidden": "red valve", "symbol": "🔴", "safe": "blue valve", "safe_symbol": "🔵"},
    {"forbidden": "yellow pump", "symbol": "🟡", "safe": "green pump", "safe_symbol": "🟢"},
    {"forbidden": "black switch", "symbol": "⚫", "safe": "white switch", "safe_symbol": "⚪"},
    {"forbidden": "purple alarm", "symbol": "🟣", "safe": "orange alarm", "safe_symbol": "🟠"},
]

SUPPLIERS = ["AlphaChem", "NorthPipe", "CedarWater", "BlueLab"]
PRIORITIES = ["SAFETY", "WATER", "ENERGY"]
SYMBOLS = ["▲", "◆", "●", "■"]
COLORS = ["CYAN", "ORANGE", "GREEN", "PURPLE"]


def init_memory():
    st.session_state.rule = random.choice(RULES)
    st.session_state.code = random.randint(10, 99)
    st.session_state.bad_supplier = random.choice(SUPPLIERS)
    st.session_state.priority = random.choice(PRIORITIES)
    st.session_state.safe_symbol = random.choice(SYMBOLS)
    st.session_state.calibration = random.choice(COLORS)


def reset_game():
    st.session_state.started = False
    st.session_state.name = ""
    st.session_state.stage = 1
    st.session_state.q_index = -1  # -1 = no-timer briefing screen for this stage
    st.session_state.score = 0
    st.session_state.feedback = ""
    st.session_state.finished = False
    st.session_state.saved = False
    st.session_state.game_over_reason = ""
    st.session_state.question_start = None
    st.session_state.question_deadline = None
    st.session_state.timer_key = None
    st.session_state.option_orders = {}
    init_memory()


if "stage" not in st.session_state:
    reset_game()

# -------------------- Question banks --------------------
def make_option(label, ok, msg):
    return {"label": label, "ok": ok, "msg": msg}


def level1_questions():
    r = st.session_state.rule
    code = st.session_state.code
    return [
        {"title": "1.1 — Warm-up", "text": "Click START. Nothing tricky yet.", "points": 60, "options": [
            make_option("START", True, "Good. You followed the exact instruction."),
            make_option("Emergency shutdown", False, "Safe-sounding, but not requested."),
            make_option("The longest answer on the screen", False, "Not the instruction."),
            make_option("Skip", False, "Engineers do not skip the brief."),
        ]},
        {"title": "1.2 — First Engineering Decision", "text": "A bridge model cracks during testing. What should an engineer do first?", "points": 70, "options": [
            make_option("Find out why it cracked", True, "Correct. Diagnose before redesigning."),
            make_option("Build the exact same model again", False, "Repeating failure is not engineering."),
            make_option("Paint it to look stronger", False, "Aesthetic improvement is not structural improvement."),
            make_option("Ignore the crack", False, "Small failures can become big failures."),
        ]},
        {"title": "1.3 — Clean Water", "text": "A village needs safer water today. Choose the most realistic emergency action.", "points": 80, "options": [
            make_option("Filter and disinfect the water", True, "Correct. Fast, realistic, and safer."),
            make_option("Build a desalination plant in one hour", False, "Too slow for an emergency stand problem."),
            make_option("Use the water without checking", False, "Unsafe."),
            make_option("Stop drinking water", False, "Not a solution."),
        ]},
        {"title": "1.4 — Attention Trap", "text": "Do NOT click the answer with the word ENGINEER. Choose the safe action.", "points": 90, "options": [
            make_option("Test the water before use", True, "Correct. You avoided the forbidden word."),
            make_option("Ask the ENGINEER to guess", False, "You clicked the forbidden word."),
            make_option("Drink now, test later", False, "Unsafe."),
            make_option("Ignore all warnings", False, "Never."),
        ]},
        {"title": "1.5 — Code Recall", "text": "What was the two-digit emergency code from the briefing?", "points": 100, "options": [
            make_option(str(code), True, "Correct memory."),
            make_option(str((code + 1) % 100).zfill(2), False, "Close, but wrong."),
            make_option(str((code - 1) % 100).zfill(2), False, "Close, but wrong."),
            make_option("I forgot", False, "The first memory check got you."),
        ]},
        {"title": "1.6 — Unit Trap", "text": "A tank contains 1000 L. You remove 1 m³. What remains?", "points": 110, "options": [
            make_option("0 L", True, "Correct. 1 m³ = 1000 L."),
            make_option("999 L", False, "You treated 1 m³ as 1 L."),
            make_option("1000 L", False, "Something was removed."),
            make_option("1 L", False, "Wrong conversion."),
        ]},
        {"title": "1.7 — Forbidden Control", "text": "The process is unstable. Stabilize it WITHOUT touching the forbidden control from the briefing.", "points": 115, "options": [
            make_option(f"{r['safe_symbol']} Use the {r['safe']}", True, "Correct. You remembered the forbidden control."),
            make_option(f"{r['symbol']} Use the {r['forbidden']}", False, "You touched the forbidden control."),
            make_option("Hit every control quickly", False, "Random action is not engineering."),
            make_option("Increase production rate", False, "Stabilize first, optimize later."),
        ]},
        {"title": "1.8 — Which Comes First?", "text": "A machine is making products too fast and quality is dropping. What comes first?", "points": 120, "options": [
            make_option("Reduce speed and check quality", True, "Correct. Output without quality is waste."),
            make_option("Increase speed more", False, "That worsens the issue."),
            make_option("Hide the bad products", False, "Not engineering, and not ethical."),
            make_option("Change the logo", False, "Branding is not process control."),
        ]},
        {"title": "1.9 — Literal Reading", "text": "Choose the option below this sentence that says it is not below this sentence.", "points": 125, "options": [
            make_option("I am below this sentence", False, "It admits it is below."),
            make_option("I am not below this sentence", True, "Correct. Literal but tricky."),
            make_option("The safe valve", False, "This is not a valve question."),
            make_option("All of the above", False, "No."),
        ]},
        {"title": "1.10 — Pressure Alarm", "text": "A plant is producing more product, but a pressure alarm starts. Choose the engineering response.", "points": 130, "options": [
            make_option("Reduce risk and investigate the alarm", True, "Correct. Safety before production."),
            make_option("Ignore it if profit is high", False, "Dangerous."),
            make_option("Turn off the sound only", False, "Silencing an alarm is not solving it."),
            make_option("Increase pressure", False, "Unsafe."),
        ]},
        {"title": "1.11 — Quick Math", "text": "A filter removes 90% of dirt. Water enters with 100 dirt units. How many remain?", "points": 135, "options": [
            make_option("10", True, "Correct. 10% remains."),
            make_option("90", False, "That is the amount removed."),
            make_option("100", False, "No removal then."),
            make_option("0", False, "90% is not 100%."),
        ]},
        {"title": "1.12 — AI Caution", "text": "AI says: 'Run at maximum temperature.' A safety warning is active. What do you do?", "points": 140, "options": [
            make_option("Check safety limits before accepting", True, "Correct. Engineers validate AI."),
            make_option("Trust AI blindly", False, "AI is a tool, not a replacement for judgement."),
            make_option("Delete AI forever", False, "Too extreme."),
            make_option("Choose the hottest setting", False, "Unsafe."),
        ]},
        {"title": "1.13 — Shortest Valid Answer", "text": "Click the shortest answer, unless it is the forbidden control.", "points": 145, "options": [
            make_option("Go", True, "Correct. Shortest valid answer."),
            make_option(r['forbidden'].title(), False, "It was tempting, but forbidden."),
            make_option("Check the full safety report", False, "Safe-sounding, but not the shortest valid answer."),
            make_option("Run away", False, "Not engineering."),
        ]},
        {"title": "1.14 — Bottleneck", "text": "A factory line has 5 steps. Step 3 is much slower than all others. What limits production?", "points": 150, "options": [
            make_option("Step 3", True, "Correct. The bottleneck controls the rate."),
            make_option("The fastest step", False, "Fast steps wait for the slow one."),
            make_option("The final package color", False, "Not the bottleneck."),
            make_option("All steps equally", False, "Not if one is much slower."),
        ]},
        {"title": "1.15 — Level 1 Final", "text": "You have dirty water, limited money, and a safety warning. What is the best order?", "points": 170, "options": [
            make_option("Control safety risk, then treat water, then optimize cost", True, "Excellent. You survived Level 1."),
            make_option("Spend everything on appearance", False, "Not useful."),
            make_option(f"Use the {r['forbidden']} because it is fastest", False, "Forbidden control trap."),
            make_option("Ignore safety and save money", False, "Unsafe."),
        ]},
    ]


def level2_questions():
    bad = st.session_state.bad_supplier
    priority = st.session_state.priority
    other_supplier = next(s for s in SUPPLIERS if s != bad)
    return [
        {"title": "2.1 — New Rule Check", "text": "Which supplier should you avoid?", "points": 150, "options": [
            make_option(bad, True, "Correct. You remembered the warning."),
            make_option(other_supplier, False, "That supplier was not banned."),
            make_option("No supplier matters", False, "Supply choices affect safety and quality."),
            make_option("Choose the cheapest only", False, "Cheap can be risky."),
        ]},
        {"title": "2.2 — Priority Decision", "text": "Budget can fix only one issue first. Use the crisis priority from the briefing.", "points": 155, "options": [
            make_option("SAFETY", priority == "SAFETY", "Correct priority." if priority == "SAFETY" else "Wrong priority."),
            make_option("WATER", priority == "WATER", "Correct priority." if priority == "WATER" else "Wrong priority."),
            make_option("ENERGY", priority == "ENERGY", "Correct priority." if priority == "ENERGY" else "Wrong priority."),
            make_option("SOCIAL MEDIA", False, "Not an engineering crisis priority."),
        ]},
        {"title": "2.3 — Process Tradeoff", "text": "A reaction is slow. Heating it helps, but too much heat creates danger. What is best?", "points": 160, "options": [
            make_option("Increase temperature within safe limits", True, "Correct. Optimize inside constraints."),
            make_option("Use maximum heat", False, "Unsafe."),
            make_option("Use no heat ever", False, "May be too slow."),
            make_option("Ignore temperature", False, "Temperature matters."),
        ]},
        {"title": "2.4 — Supplier Trap", "text": "Choose a supplier for pipes. One option is banned from the briefing.", "points": 165, "options": [
            make_option(f"Use {other_supplier}", True, "Correct. You avoided the banned supplier."),
            make_option(f"Use {bad}", False, "That was the banned supplier."),
            make_option("Buy random pipes with no testing", False, "Unsafe and unprofessional."),
            make_option("Use no pipes", False, "Not a realistic system."),
        ]},
        {"title": "2.5 — The Blue Button Trap", "text": "Choose the best answer. Do not be distracted by color words.", "points": 170, "options": [
            make_option("Check data before changing the process", True, "Correct. Evidence first."),
            make_option("Blue button", False, "Color was a distraction."),
            make_option("Emergency code from Level 1", False, "Not asked now."),
            make_option("Choose the longest answer because it looks serious", False, "Appearance is not logic."),
        ]},
        {"title": "2.6 — Separation", "text": "You have sand mixed with water. What is the simplest separation method?", "points": 175, "options": [
            make_option("Filtration", True, "Correct."),
            make_option("Wi-Fi", False, "Creative, but no."),
            make_option("Increase pressure until it disappears", False, "Unsafe nonsense."),
            make_option("Painting the sand", False, "No separation."),
        ]},
        {"title": "2.7 — Reverse Psychology", "text": "Do NOT choose the most engineering-sounding answer. Choose the simple correct answer.", "points": 180, "options": [
            make_option("Measure the leak", True, "Correct. Simple and useful."),
            make_option("Integrated thermo-hydraulic optimization framework", False, "Engineering-sounding trap."),
            make_option("Ignore the leak", False, "Unsafe."),
            make_option("Guess the leak using vibes", False, "No."),
        ]},
        {"title": "2.8 — Contamination", "text": "A water sample may be contaminated. What is the worst action?", "points": 185, "options": [
            make_option("Serve it immediately without testing", True, "Correct: this is the worst action."),
            make_option("Test it", False, "That is good, not worst."),
            make_option("Disinfect it", False, "That can help."),
            make_option("Warn people", False, "That is responsible."),
        ]},
        {"title": "2.9 — Read Carefully", "text": "Click the answer that is wrong.", "points": 190, "options": [
            make_option("Safety checks are optional", True, "Correct: this statement is wrong."),
            make_option("Engineers solve problems", False, "This is true, not wrong."),
            make_option("Testing reduces uncertainty", False, "This is true."),
            make_option("Water treatment can save lives", False, "This is true."),
        ]},
        {"title": "2.10 — Energy Choice", "text": "A process uses too much energy. What is a strong engineering action?", "points": 195, "options": [
            make_option("Recover heat from the hot outlet stream", True, "Correct. Heat recovery is practical engineering."),
            make_option("Pretend energy is free", False, "Costs and sustainability matter."),
            make_option("Make the plant colder randomly", False, "Random changes are not design."),
            make_option("Ban electricity", False, "Not a solution."),
        ]},
        {"title": "2.11 — Double Constraint", "text": "Choose the safest action, but do NOT choose anything involving the banned supplier.", "points": 200, "options": [
            make_option("Test the pipe from the approved supplier", True, "Correct. Safe and not banned."),
            make_option(f"Test the pipe from {bad}", False, "Banned supplier trap."),
            make_option("Skip all tests", False, "Unsafe."),
            make_option("Increase pressure until it breaks", False, "Destructive without need."),
        ]},
        {"title": "2.12 — Efficiency Trap", "text": "A design is fastest but has a high chance of failure. Another is slower but safe. Which is better for a public water system?", "points": 205, "options": [
            make_option("Slower but safe", True, "Correct. Reliability matters."),
            make_option("Fastest always wins", False, "Not if it fails."),
            make_option("Do nothing", False, "Not acceptable."),
            make_option("Choose randomly", False, "Engineering uses reasoning."),
        ]},
        {"title": "2.13 — Hidden Math", "text": "A pump can fill 3 tanks per hour. How many tanks in 20 minutes?", "points": 210, "options": [
            make_option("1", True, "Correct. 20 minutes is one third of an hour."),
            make_option("3", False, "That is for one hour."),
            make_option("20", False, "Minutes are not tanks."),
            make_option("60", False, "No."),
        ]},
        {"title": "2.14 — AI vs Human", "text": "AI predicts a pipe is safe, but sensors disagree. What do you do?", "points": 215, "options": [
            make_option("Investigate before operation", True, "Correct. Conflicting evidence needs checking."),
            make_option("Always obey AI", False, "No."),
            make_option("Always ignore sensors", False, "Sensors carry real data."),
            make_option("Choose the banned supplier", False, "Why bring them back?"),
        ]},
        {"title": "2.15 — Level 2 Final", "text": "A safe but expensive solution competes with a cheap risky solution from the banned supplier. Choose.", "points": 260, "options": [
            make_option("Choose safe approved solution and optimize cost later", True, "Excellent. You survived Level 2."),
            make_option(f"Choose {bad} because it is cheaper", False, "Banned supplier and risky."),
            make_option("Choose nothing and hope", False, "Hope is not a strategy."),
            make_option("Choose the option with the longest text", False, "Length is not logic."),
        ]},
    ]


def level3_questions():
    sym = st.session_state.safe_symbol
    calib = st.session_state.calibration
    r = st.session_state.rule
    # Pick a wrong symbol different from safe symbol
    wrong_sym = next(x for x in SYMBOLS if x != sym)
    wrong_color = next(c for c in COLORS if c != calib)
    return [
        {"title": "3.1 — Symbol Recall", "text": "Only one symbol was marked SAFE in the briefing. Choose it.", "points": 230, "options": [
            make_option(sym, True, "Correct symbol."),
            make_option(wrong_sym, False, "Wrong symbol."),
            make_option("✖", False, "Not the safe symbol."),
            make_option("?", False, "Not the safe symbol."),
        ]},
        {"title": "3.2 — Calibration Recall", "text": "Which calibration color was approved?", "points": 235, "options": [
            make_option(calib, True, "Correct calibration color."),
            make_option(wrong_color, False, "Wrong calibration color."),
            make_option("WHITE", False, "Not approved."),
            make_option("BLACK", False, "Not approved."),
        ]},
        {"title": "3.3 — Advanced Trap", "text": "Choose the approved color, unless it appears next to the wrong symbol.", "points": 240, "options": [
            make_option(f"{sym} {calib}", True, "Correct. Approved color with safe symbol."),
            make_option(f"{wrong_sym} {calib}", False, "Approved color, but wrong symbol."),
            make_option(f"{sym} {wrong_color}", False, "Safe symbol, but wrong color."),
            make_option(f"{wrong_sym} {wrong_color}", False, "Both wrong."),
        ]},
        {"title": "3.4 — Plant Crisis", "text": "Pressure is rising and the alarm is real. The production manager says continue. What do you do?", "points": 245, "options": [
            make_option("Reduce feed and stabilize pressure", True, "Correct. Control the hazard."),
            make_option("Continue because manager asked", False, "Engineering responsibility matters."),
            make_option("Increase feed", False, "Worse."),
            make_option("Turn off the alarm display", False, "Hiding risk is not safety."),
        ]},
        {"title": "3.5 — False Friend", "text": "Click the option that would NOT improve safety.", "points": 250, "options": [
            make_option("Disable the warning system", True, "Correct: this would not improve safety."),
            make_option("Inspect the relief valve", False, "This improves safety."),
            make_option("Reduce pressure", False, "This improves safety."),
            make_option("Check sensor calibration", False, "This improves safety."),
        ]},
        {"title": "3.6 — Multi-Step", "text": "Dirty water enters a filter. The filter clogs and pressure rises. What is the most engineering answer?", "points": 255, "options": [
            make_option("Stop, inspect clogging, then redesign or backwash", True, "Correct. Diagnose and fix root cause."),
            make_option("Increase pressure forever", False, "Dangerous and unsustainable."),
            make_option("Remove the filter", False, "Then dirt passes through."),
            make_option("Blame the water", False, "Water quality is part of design."),
        ]},
        {"title": "3.7 — The Forbidden Returns", "text": "Choose the safe symbol and do not touch the forbidden control from Level 1.", "points": 260, "options": [
            make_option(f"{sym} and use approved control", True, "Correct. You combined memories."),
            make_option(f"{sym} and use the {r['forbidden']}", False, "Safe symbol, but forbidden control."),
            make_option(f"{wrong_sym} and use approved control", False, "Wrong symbol."),
            make_option(f"{wrong_sym} and use the {r['forbidden']}", False, "Two traps at once."),
        ]},
        {"title": "3.8 — Economic Trap", "text": "A solution is cheaper but fails every 3 days. A second costs more but runs for months. For a hospital, choose.", "points": 265, "options": [
            make_option("Reliable solution", True, "Correct. Lifecycle reliability beats cheap failure."),
            make_option("Cheapest today", False, "Not for critical systems."),
            make_option("No solution", False, "Unacceptable."),
            make_option("The one with nicer color", False, "No."),
        ]},
        {"title": "3.9 — Sensor Conflict", "text": "Temperature sensor A says 80°C. Sensor B says 180°C. Product is failing. What now?", "points": 270, "options": [
            make_option("Calibrate/check sensors before deciding", True, "Correct. Bad data leads to bad decisions."),
            make_option("Average them blindly", False, "Averages can hide sensor failure."),
            make_option("Ignore both", False, "Data matters."),
            make_option("Pick the lower value because it feels safer", False, "Feelings are not calibration."),
        ]},
        {"title": "3.10 — Impossible-Style Wording", "text": "Do not click the correct engineering answer. Click the answer that says 'wrong'.", "points": 275, "options": [
            make_option("wrong", True, "Correct. You followed the weird instruction."),
            make_option("Shut down safely", False, "Correct engineering, but not the instruction."),
            make_option("Check pressure", False, "Good engineering, wrong instruction."),
            make_option("Verify sensors", False, "Good engineering, wrong instruction."),
        ]},
        {"title": "3.11 — But Now Be Serious", "text": "Now ignore the previous weird instruction. Which action is actually best during overheating?", "points": 280, "options": [
            make_option("Reduce heat input and check cooling", True, "Correct. Back to real engineering."),
            make_option("wrong", False, "That instruction ended."),
            make_option("Increase heat", False, "Worse."),
            make_option("Celebrate", False, "Not helpful."),
        ]},
        {"title": "3.12 — Approved Calibration", "text": "You must calibrate a sensor. Pick the approved color and the safe symbol.", "points": 285, "options": [
            make_option(f"{sym} {calib}", True, "Correct."),
            make_option(f"{sym} {wrong_color}", False, "Wrong color."),
            make_option(f"{wrong_sym} {calib}", False, "Wrong symbol."),
            make_option("Use no calibration", False, "No."),
        ]},
        {"title": "3.13 — Risk Ranking", "text": "Which risk must usually be handled first?", "points": 290, "options": [
            make_option("Risk to human safety", True, "Correct. Safety risk first."),
            make_option("Risk of ugly slide design", False, "Not comparable."),
            make_option("Risk of lower social media likes", False, "No."),
            make_option("Risk of using too few emojis", False, "No."),
        ]},
        {"title": "3.14 — Final Memory Mix", "text": "Choose the only option that satisfies all memories: safe symbol, approved calibration, and no forbidden control.", "points": 310, "options": [
            make_option(f"{sym} {calib} with approved control", True, "Excellent memory integration."),
            make_option(f"{sym} {calib} with {r['forbidden']}", False, "Forbidden control."),
            make_option(f"{wrong_sym} {calib} with approved control", False, "Wrong symbol."),
            make_option(f"{sym} {wrong_color} with approved control", False, "Wrong color."),
        ]},
        {"title": "3.15 — Grand Final", "text": "A city has unsafe water, high energy cost, bad sensor data, and pressure alarm. Choose the chief engineer move.", "points": 420, "options": [
            make_option("Protect people, verify data, stabilize pressure, then optimize water and energy", True, "You completed the full challenge."),
            make_option("Optimize profit while ignoring alarms", False, "Unsafe."),
            make_option("Trust one unverified sensor and rush", False, "Bad data can be dangerous."),
            make_option(f"Use the {r['forbidden']} immediately", False, "Final forbidden-control trap."),
        ]},
    ]


def questions_for_stage(stage):
    if stage == 1:
        return level1_questions()
    if stage == 2:
        return level2_questions()
    return level3_questions()


def stage_name(stage):
    return {
        1: "Level 1 — Rookie Engineer",
        2: "Level 2 — Process Engineer",
        3: "Level 3 — Chief Engineer",
    }[stage]

# -------------------- Timer and game mechanics --------------------
def clear_timer():
    st.session_state.question_start = None
    st.session_state.question_deadline = None
    st.session_state.timer_key = None


def start_timer_if_needed():
    key = f"{st.session_state.stage}-{st.session_state.q_index}"
    if st.session_state.timer_key != key or st.session_state.question_deadline is None:
        st.session_state.question_start = time.time()
        st.session_state.question_deadline = st.session_state.question_start + QUESTION_TIME
        st.session_state.timer_key = key


def finish_correct(points, msg):
    elapsed = time.time() - (st.session_state.question_start or time.time())
    speed_bonus = max(0, int((QUESTION_TIME - elapsed) * 3))
    st.session_state.score += points + speed_bonus
    st.session_state.feedback = f"✅ {msg} (+{points}" + (f", +{speed_bonus} speed bonus)" if speed_bonus else ")")
    clear_timer()
    st.session_state.q_index += 1
    if st.session_state.q_index >= QUESTIONS_PER_LEVEL:
        if st.session_state.stage >= TOTAL_LEVELS:
            st.session_state.finished = True
            st.session_state.game_over_reason = "🏆 You completed all 45 questions. This is extremely rare."
        else:
            st.session_state.stage += 1
            st.session_state.q_index = -1
            st.session_state.feedback = f"🎉 Level {st.session_state.stage - 1} completed. Prepare for {stage_name(st.session_state.stage)}."
    st.rerun()


def finish_wrong(msg):
    st.session_state.finished = True
    st.session_state.game_over_reason = f"❌ Eliminated: {msg}"
    clear_timer()
    st.rerun()


def render_options(options, points):
    # Keep the option order fixed for the current question.
    # Streamlit reruns the script repeatedly because of the live timer; without
    # storing the order, the buttons would reshuffle every second.
    qkey = f"{st.session_state.stage}-{st.session_state.q_index}"
    if "option_orders" not in st.session_state:
        st.session_state.option_orders = {}
    if qkey not in st.session_state.option_orders:
        order = list(range(len(options)))
        random.shuffle(order)
        st.session_state.option_orders[qkey] = order
    opts = [options[i] for i in st.session_state.option_orders[qkey] if i < len(options)]
    for opt in opts:
        if st.button(opt["label"]):
            if opt["ok"]:
                finish_correct(points, opt["msg"])
            else:
                finish_wrong(opt["msg"])

# -------------------- Routing / modes --------------------
# Public deployment URLs:
#   ?view=play     -> simple student game page for phones
#   ?view=host     -> full laptop control panel with leaderboard, QR, reset, answer key, and play mode
#   ?view=control  -> same as host
#
# This keeps the phone experience clean while giving you full control on the laptop.
view = str(st.query_params.get("view", "")).lower().strip()
mode_options = ["Host Screen + Live Leaderboard", "Player Game", "Reset Leaderboard", "Answer Key"]

host_full_controls = False
if view == "play":
    mode = "Player Game"
elif view in ["host", "control", "admin"]:
    # Host mode should not depend on the Streamlit sidebar, because the
    # sidebar can be hidden/collapsed on some browsers and screen sizes.
    # Everything needed for the event is shown directly on the main page.
    host_full_controls = True
    mode = "Host Screen + Live Leaderboard"
elif view == "reset":
    mode = "Reset Leaderboard"
elif view == "key":
    mode = "Answer Key"
else:
    # Full app by default for local testing or when opening the root deployed URL.
    st.sidebar.markdown("## 🎛️ Control Panel")
    mode = st.sidebar.radio("Choose what to display", mode_options, index=0)

if mode == "Host Screen + Live Leaderboard":
    if st_autorefresh:
        st_autorefresh(interval=2000, key="leaderboard_refresh")

    default_public = normalize_url(get_secret_or_env("PUBLIC_APP_URL", ""))
    if not default_public:
        # Useful for local testing only. For the real event, deploy online and paste the public URL.
        default_public = f"http://{get_local_ip()}:8501"

    st.markdown("<div class='big-title'>🏆 Live Engineering Leaderboard</div>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Keep this screen open on your laptop. Students scan the QR code and play from any network/mobile data.</p>", unsafe_allow_html=True)

    if host_full_controls:
        st.markdown("""
<div class='big-card'>
<h3>🎛️ Laptop Control Panel</h3>
<p>This host page includes the live leaderboard, QR code, reset button, answer key, and a link to play the game yourself.</p>
</div>
""", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🧹 Reset leaderboard", use_container_width=True):
                with open(DATA_FILE, "w", encoding="utf-8") as f:
                    json.dump([], f)
                st.success("Leaderboard cleared.")
                st.rerun()
        with c2:
            st.markdown("<a class='link-button' href='?view=play' target='_blank'>🎮 Open play mode</a>", unsafe_allow_html=True)
        with st.expander("🔐 Private answer key", expanded=False):
            st.markdown("""
**General rule:** Each level starts with a no-timer briefing. The player remembers 2 items. Then 15 timed questions follow.

**Level 1:** START; Find out why it cracked; Filter and disinfect the water; Test the water before use; memorized code; 0 L; safe paired control; Reduce speed and check quality; I am not below this sentence; Reduce risk and investigate the alarm; 10; Check safety limits before accepting; Go; Step 3; Control safety risk, then treat water, then optimize cost.

**Level 2:** banned supplier; memorized priority; Increase temperature within safe limits; non-banned supplier; Check data before changing the process; Filtration; Measure the leak; Serve it immediately without testing; Safety checks are optional; Recover heat from hot outlet stream; approved supplier pipe; Slower but safe; 1; Investigate before operation; Safe approved solution and optimize cost later.

**Level 3:** safe symbol; approved calibration color; safe symbol + approved color; Reduce feed and stabilize pressure; Disable warning system; Stop, inspect clogging, then redesign/backwash; safe symbol + approved control; reliable solution; Calibrate/check sensors; wrong; Reduce heat input and check cooling; safe symbol + approved calibration color; human safety risk; safe symbol + approved calibration + approved control; Protect people, verify data, stabilize pressure, then optimize water and energy.
""")

    st.markdown("""
<div class='big-card'>
<h3>Public phone access</h3>
<p>Students do <b>not</b> need to be on the same Wi‑Fi. They should scan the QR code generated from the public deployed link.</p>
</div>
""", unsafe_allow_html=True)

    app_url = st.text_input(
        "Public app URL",
        value=default_public,
        help="Example: https://your-engineering-crisis-game.streamlit.app. This must be a public deployed URL for mobile-data access.",
    )
    player_url = public_play_url(app_url)
    host_url = public_host_url(app_url)

    if player_url:
        st.markdown(f"""
<div class='big-card'>
<h3>Event URLs</h3>
<p><b>Students:</b> scan the QR code below.</p>
<p><b>Your laptop:</b> open the host URL below to see the live leaderboard.</p>
</div>
""", unsafe_allow_html=True)

        qr_uri = make_qr_data_uri(player_url)
        if qr_uri:
            st.markdown(f"""
<div class='qr-wrap'>
  <div class='qr-card'><img src='{qr_uri}' width='290'></div>
  <div class='link-box'>
    <div style='font-size:1.55rem;'>SCAN TO PLAY</div>
    <div style='font-size:1.00rem;margin-top:0.55rem;'>Can You Think Like an Engineer?</div>
  </div>
</div>
""", unsafe_allow_html=True)
        else:
            st.warning("QR package not installed. Run: pip install qrcode[pil]")
            st.markdown(f"<div class='link-box'>{player_url}</div>", unsafe_allow_html=True)

        with st.expander("Show links", expanded=False):
            st.write("Player link:")
            st.code(player_url)
            st.write("Laptop control-panel link:")
            st.code(host_url)
            st.caption("Open this on your laptop to access the leaderboard, reset button, answer key, and player mode.")

    scores = load_scores()[:15]
    total_players = len(load_scores())
    highest = scores[0]["score"] if scores else 0
    col1, col2, col3 = st.columns(3)
    col1.metric("Players", total_players)
    col2.metric("Top Score", highest)
    col3.metric("Refresh", "Live")

    if not scores:
        st.info("No players yet. Scores will appear here live.")
    else:
        for i, s in enumerate(scores, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "⚙️"
            st.markdown(
                f"<div class='big-card'><h3>{medal} {i}. {s['name']} — {s['score']} points</h3>"
                f"<p>{s.get('persona','Engineer')} • reached Level {s.get('stage','?')}, Q{s.get('question','?')} • {s.get('time','')}</p></div>",
                unsafe_allow_html=True,
            )
    st.button("Refresh now")
    st.stop()

if mode == "Reset Leaderboard":
    st.markdown("<div class='big-title'>Reset Leaderboard</div>", unsafe_allow_html=True)
    st.warning("Use this before the event or between testing sessions.")
    if st.button("Clear all scores"):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        st.success("Leaderboard cleared.")
    st.stop()

if mode == "Answer Key":
    st.markdown("<div class='big-title'>Private Answer Key</div>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Use only for testing. Randomized memory items change for every player.</p>", unsafe_allow_html=True)
    st.markdown("""
<div class='big-card'>
<h3>General rule</h3>
<p>Every stage starts with a no-timer briefing. The player must remember 2 items. Then 15 timed questions follow.</p>
<h3>Level 1 answers</h3>
<ol><li>START</li><li>Find out why it cracked</li><li>Filter and disinfect the water</li><li>Test the water before use</li><li>The Level 1 code</li><li>0 L</li><li>The safe paired control, not the forbidden one</li><li>Reduce speed and check quality</li><li>I am not below this sentence</li><li>Reduce risk and investigate the alarm</li><li>10</li><li>Check safety limits before accepting</li><li>Go</li><li>Step 3</li><li>Control safety risk, then treat water, then optimize cost</li></ol>
<h3>Level 2 answers</h3>
<ol><li>The banned supplier</li><li>The memorized priority</li><li>Increase temperature within safe limits</li><li>Use the non-banned supplier</li><li>Check data before changing the process</li><li>Filtration</li><li>Measure the leak</li><li>Serve it immediately without testing</li><li>Safety checks are optional</li><li>Recover heat from the hot outlet stream</li><li>Test the pipe from the approved supplier</li><li>Slower but safe</li><li>1</li><li>Investigate before operation</li><li>Choose safe approved solution and optimize cost later</li></ol>
<h3>Level 3 answers</h3>
<ol><li>The safe symbol</li><li>The approved calibration color</li><li>Safe symbol + approved color</li><li>Reduce feed and stabilize pressure</li><li>Disable the warning system</li><li>Stop, inspect clogging, then redesign or backwash</li><li>Safe symbol + approved control, no forbidden control</li><li>Reliable solution</li><li>Calibrate/check sensors before deciding</li><li>wrong</li><li>Reduce heat input and check cooling</li><li>Safe symbol + approved calibration color</li><li>Risk to human safety</li><li>Safe symbol + approved calibration + approved control</li><li>Protect people, verify data, stabilize pressure, then optimize water and energy</li></ol>
</div>
""", unsafe_allow_html=True)
    st.stop()

# -------------------- Player game --------------------
st.markdown("<div class='big-title'>⚙️ Can You Think Like an Engineer?</div>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>3 levels • 45 questions • 15 seconds each • one wrong answer and you are out.</p>", unsafe_allow_html=True)

if not st.session_state.started:
    st.markdown(
        "<div class='big-card'><h3>The Challenge</h3>"
        "<p>This is not a normal quiz. It is inspired by impossible-style games: memory, attention traps, quick decisions, and engineering logic.</p>"
        "<p><b>Level 1</b> is friendly. <b>Level 2</b> gets strategic. <b>Level 3</b> is brutal.</p></div>",
        unsafe_allow_html=True,
    )
    st.session_state.name = st.text_input("Enter your first name or nickname", max_chars=18, placeholder="e.g., Sara")
    if st.button("🚀 Start Tournament"):
        if not st.session_state.name.strip():
            st.error("Enter a name first.")
        else:
            st.session_state.started = True
            st.session_state.stage = 1
            st.session_state.q_index = -1
            st.session_state.score = 0
            st.session_state.feedback = ""
            clear_timer()
            st.rerun()
    st.stop()

if st.session_state.finished:
    final_score = max(0, st.session_state.score)
    persona = next(name for threshold, name in PERSONAS if final_score >= threshold)
    reached_q = max(0, st.session_state.q_index + 1)
    st.markdown("<div class='big-card'><h2>Game Over</h2></div>", unsafe_allow_html=True)
    if st.session_state.game_over_reason:
        st.warning(st.session_state.game_over_reason)
    st.metric("Final Score", final_score)
    st.markdown(f"### Your style: {persona}")
    st.markdown(f"You reached **Level {st.session_state.stage}**, question **{min(reached_q, QUESTIONS_PER_LEVEL)}/{QUESTIONS_PER_LEVEL}**.")
    if not st.session_state.saved:
        save_score({
            "name": st.session_state.name.strip(),
            "score": final_score,
            "persona": persona,
            "stage": st.session_state.stage,
            "question": min(reached_q, QUESTIONS_PER_LEVEL),
            "time": datetime.now().strftime("%H:%M:%S"),
        })
        st.session_state.saved = True
    if st.button("🔁 Play again"):
        reset_game()
        st.rerun()
    st.stop()

if st.session_state.feedback:
    st.info(st.session_state.feedback)

# Briefing screen for each level: no timer.
if st.session_state.q_index == -1:
    st.markdown(f"<div class='stage-pill'>{stage_name(st.session_state.stage)}</div>", unsafe_allow_html=True)
    if st.session_state.stage == 1:
        st.markdown(f"""
<div class='memory-box'>
<h3>Level 1 Briefing — Remember only TWO things</h3>
<h2>{st.session_state.rule['symbol']} Forbidden control: {st.session_state.rule['forbidden'].upper()}</h2>
<h2>🔢 Emergency code: {st.session_state.code}</h2>
<p class='small-note'>No timer here. The level becomes timed after you continue.</p>
</div>
""", unsafe_allow_html=True)
    elif st.session_state.stage == 2:
        st.markdown(f"""
<div class='memory-box'>
<h3>Level 2 Briefing — New rules</h3>
<h2>🚫 Banned supplier: {st.session_state.bad_supplier}</h2>
<h2>🎯 Crisis priority: {st.session_state.priority}</h2>
<p class='small-note'>Keep these in mind. This level mixes engineering and traps.</p>
</div>
""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
<div class='memory-box'>
<h3>Level 3 Briefing — Final rules</h3>
<h2>✅ Safe symbol: {st.session_state.safe_symbol}</h2>
<h2>🎨 Approved calibration color: {st.session_state.calibration}</h2>
<p class='small-note'>This level combines all the memories. It is meant to be hard.</p>
</div>
""", unsafe_allow_html=True)
    if st.button("I memorized this. Start the level."):
        st.session_state.q_index = 0
        st.session_state.feedback = ""
        clear_timer()
        st.rerun()
    st.stop()

# Timed question screen.
questions = questions_for_stage(st.session_state.stage)
q = questions[st.session_state.q_index]

start_timer_if_needed()
if st_autorefresh:
    st_autorefresh(interval=350, key=f"timer_{st.session_state.stage}_{st.session_state.q_index}_{st.session_state.name}")
else:
    st.warning("Install streamlit-autorefresh for automatic timeout: pip install streamlit-autorefresh")

now = time.time()
remaining_float = st.session_state.question_deadline - now
remaining = max(0, int(remaining_float + 0.999))
if remaining_float <= 0:
    st.session_state.finished = True
    st.session_state.game_over_reason = "⏱️ Time is up. Engineers must act under constraints."
    clear_timer()
    st.rerun()

deadline_ms = int(st.session_state.question_deadline * 1000)
st.components.v1.html(
    f"""
<div style="font-family:Arial,sans-serif;text-align:center;margin:0 0 8px 0;">
  <div id="timerBox" style="font-size:34px;font-weight:950;color:#facc15;">⏱️ <span id="timer">{remaining}</span> s</div>
</div>
<script>
const deadline = {deadline_ms};
const el = document.getElementById('timer');
const box = document.getElementById('timerBox');
function tick() {{
  const rem = Math.max(0, Math.ceil((deadline - Date.now()) / 1000));
  el.textContent = rem;
  if (rem <= 5) box.style.color = '#ef4444';
  else box.style.color = '#facc15';
}}
tick();
setInterval(tick, 100);
</script>
""",
    height=54,
)
st.progress(max(0.0, min(1.0, remaining_float / QUESTION_TIME)))

st.markdown(
    f"<div class='score-pill'>Score: {st.session_state.score} &nbsp; | &nbsp; {stage_name(st.session_state.stage)} &nbsp; | &nbsp; Question {st.session_state.q_index + 1}/{QUESTIONS_PER_LEVEL}</div>",
    unsafe_allow_html=True,
)
st.subheader(q["title"])
st.markdown(f"<div class='level-card'><p>{q['text']}</p></div>", unsafe_allow_html=True)
render_options(q["options"], q["points"])
