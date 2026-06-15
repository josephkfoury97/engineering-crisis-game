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
QUESTIONS_PER_LEVEL = {0: 3, 1: 15, 2: 15, 3: 15, 4: 5}
TOTAL_STAGE = 4
STAGE_TIMES = {0: None, 1: 30, 2: 25, 3: 20, 4: 15}

st.set_page_config(
    page_title="Can You Think Like an Engineer?",
    page_icon="⚙️",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
:root{
  --bg1:#07111f; --bg2:#020617; --card:#0f172a; --accent:#f97316;
  --gold:#facc15; --red:#ef4444; --green:#22c55e; --text:#f8fafc; --muted:#cbd5e1;
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
.block-container{padding-top:0.7rem !important; max-width:1000px;}
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
.link-button {display:block;text-align:center;padding:0.75rem 1rem;border-radius:14px;background:linear-gradient(135deg,#2563eb,#7c3aed);color:#ffffff !important;font-weight:800;text-decoration:none !important;border:1px solid rgba(255,255,255,0.25);box-shadow:0 8px 20px rgba(37,99,235,0.25);}
.link-button:hover { filter:brightness(1.08); }
#MainMenu, footer{visibility:hidden;}
</style>
""", unsafe_allow_html=True)

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
        return "127.0.0.1"

def get_secret_or_env(name, default=""):
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
    return base + "?" + urlencode({"view": "play"}) if base else ""

def public_host_url(base_url):
    base = normalize_url(base_url)
    return base + "?" + urlencode({"view": "host"}) if base else ""

def make_qr_data_uri(text):
    if qrcode is None:
        return None
    img = qrcode.make(text)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")

# -------------------- Game state --------------------
PERSONAS = [
    (6200, "Legendary Chief Engineer 🧠"),
    (5000, "Crisis Commander 🚨"),
    (3700, "Process Optimization Pro ⚙️"),
    (2400, "Safety-First Engineer 🦺"),
    (1200, "Promising Future Engineer 🌱"),
    (0, "Engineer in Training 🔧"),
]
RULES = [
    {"forbidden": "red valve", "symbol": "🔴", "safe": "blue valve", "safe_symbol": "🔵"},
    {"forbidden": "yellow pump", "symbol": "🟡", "safe": "green pump", "safe_symbol": "🟢"},
    {"forbidden": "black switch", "symbol": "⚫", "safe": "white switch", "safe_symbol": "⚪"},
    {"forbidden": "purple alarm", "symbol": "🟣", "safe": "orange alarm", "safe_symbol": "🟠"},
]
SUPPLIERS = ["AlphaChem", "NorthPipe", "CedarWater", "BlueLab"]
COLORS = ["CYAN", "ORANGE", "GREEN", "PURPLE"]
SYMBOLS = ["▲", "◆", "●", "■"]


def init_memory():
    st.session_state.rule = random.choice(RULES)
    st.session_state.code = random.randint(10, 99)
    st.session_state.bad_supplier = random.choice(SUPPLIERS)
    st.session_state.calibration = random.choice(COLORS)
    st.session_state.safe_reactor = random.choice(["A", "B", "C"])
    st.session_state.safe_symbol = random.choice(SYMBOLS)


def reset_game():
    st.session_state.started = False
    st.session_state.name = ""
    st.session_state.stage = 0
    st.session_state.q_index = 0
    st.session_state.score = 0
    st.session_state.feedback = ""
    st.session_state.finished = False
    st.session_state.saved = False
    st.session_state.game_over_reason = ""
    st.session_state.question_start = None
    st.session_state.question_deadline = None
    st.session_state.timer_key = None
    st.session_state.option_orders = {}
    st.session_state.lives_used = 0
    st.session_state.stage_intro = True
    init_memory()

if "stage" not in st.session_state:
    reset_game()

# -------------------- Question banks --------------------
def opt(label, ok, msg):
    return {"label": label, "ok": ok, "msg": msg}

def tutorial_questions():
    reactor = st.session_state.safe_reactor
    code = st.session_state.code
    return [
        {"title": "Tutorial 1 — Memory Brief", "text": f"No timer here. Remember only these two things for now: Emergency code = {code}. Safe reactor = {reactor}.", "points": 0, "options": [opt("I memorized them", True, "Good. Engineers read the brief first."), opt("Skip the brief", False, "This is only a tutorial, but skipping the brief is dangerous.")]},
        {"title": "Tutorial 2 — Follow the Exact Instruction", "text": "Click CONTINUE. Not START. Not GO. CONTINUE.", "points": 0, "options": [opt("START", False, "Read carefully."), opt("GO", False, "Read carefully."), opt("CONTINUE", True, "Correct. Attention matters."), opt("Emergency shutdown", False, "Not requested.")]},
        {"title": "Tutorial 3 — Memory Check", "text": "Which reactor was marked safe?", "points": 0, "options": [opt(reactor, True, "Perfect. The actual game starts now."), opt("A" if reactor != "A" else "B", False, "Wrong reactor."), opt("All reactors", False, "Only one was safe."), opt("I forgot", False, "Keep the brief in mind.")]},
    ]

def level1_questions():
    r = st.session_state.rule
    code = st.session_state.code
    reactor = st.session_state.safe_reactor
    return [
        {"title":"1.1 — Easy Start", "text":"Water is visibly dirty. What is the most sensible first action?", "points":60, "options":[opt("Filter and disinfect it", True, "Correct."), opt("Drink it quickly", False, "Unsafe."), opt("Add more dirt", False, "No."), opt("Ignore it", False, "No.")]},
        {"title":"1.2 — Engineering Thinking", "text":"A small bridge model cracks during testing. What should you do first?", "points":70, "options":[opt("Find out why it cracked", True, "Correct. Diagnose before redesign."), opt("Paint it", False, "Looks are not strength."), opt("Build the same one again", False, "Repeating failure is not engineering."), opt("Ignore it", False, "Small failures can become big failures.")]},
        {"title":"1.3 — Code Recall", "text":"What was the emergency code from the tutorial?", "points":85, "options":[opt(str(code), True, "Correct memory."), opt(str((code+1)%100).zfill(2), False, "Close, but wrong."), opt(str((code-1)%100).zfill(2), False, "Close, but wrong."), opt("I forgot", False, "The code matters.")]},
        {"title":"1.4 — Exact Instruction", "text":"Click the BLUE option.", "points":90, "options":[opt("BLUE", True, "Correct."), opt("RED", False, "Not blue."), opt("GREEN", False, "Not blue."), opt("The safest answer", False, "The instruction was BLUE.")]},
        {"title":"1.5 — Safety First", "text":"A pipe is leaking near electrical equipment. First response?", "points":100, "options":[opt("Make the area safe and report it", True, "Correct."), opt("Touch the leak", False, "Unsafe."), opt("Take a selfie", False, "No."), opt("Increase pressure", False, "Worse.")]},
        {"title":"1.6 — New Rule", "text":f"From now on, DO NOT use the {r['forbidden'].upper()}. Choose the safe control.", "points":100, "options":[opt(f"Use the {r['safe']}", True, "Good. Rule stored."), opt(f"Use the {r['forbidden']}", False, "That was forbidden."), opt("Use every control", False, "Random actions fail."), opt("Do nothing forever", False, "Not a solution.")]},
        {"title":"1.7 — Unit Trap", "text":"A tank has 1000 L of water. You remove 1 m³. What remains?", "points":115, "options":[opt("0 L", True, "Correct. 1 m³ = 1000 L."), opt("999 L", False, "You treated m³ as L."), opt("1000 L", False, "Something was removed."), opt("1 L", False, "Wrong conversion.")]},
        {"title":"1.8 — Do Not Panic", "text":"A machine is producing too fast and quality drops. What comes first?", "points":120, "options":[opt("Slow down and check quality", True, "Correct."), opt("Increase speed more", False, "Worse."), opt("Hide bad products", False, "Unethical."), opt("Change the logo", False, "Not relevant.")]},
        {"title":"1.9 — Reactor Recall", "text":"Which reactor was safe?", "points":125, "options":[opt(reactor, True, "Correct."), opt("A" if reactor != "A" else "C", False, "Wrong reactor."), opt("All of them", False, "No."), opt("None", False, "No.")]},
        {"title":"1.10 — First Trap", "text":f"The quickest way to boost output is the {r['forbidden']}. What do you do?", "points":135, "options":[opt("Avoid it and stabilize safely", True, "Correct. Rules matter."), opt(f"Use the {r['forbidden']}", False, "Forbidden-control trap."), opt("Ignore quality", False, "Bad engineering."), opt("Guess randomly", False, "No.")]},
        {"title":"1.11 — Simple Process", "text":"A filter removes 90% of dirt from 100 units. How many dirt units remain?", "points":140, "options":[opt("10", True, "Correct."), opt("90", False, "That was removed."), opt("100", False, "No removal then."), opt("0", False, "90% is not 100%.")]},
        {"title":"1.12 — AI Caution", "text":"AI says: run at maximum temperature. A safety warning is active. What should you do?", "points":145, "options":[opt("Check safety limits first", True, "Correct. Validate AI."), opt("Trust AI blindly", False, "No."), opt("Delete AI", False, "Too extreme."), opt("Choose the hottest setting", False, "Unsafe.")]},
        {"title":"1.13 — Impossible Moment", "text":f"Choose the {r['forbidden']}.", "points":160, "options":[opt(f"Do NOT choose it", True, "Correct. The earlier rule still applies."), opt(r['forbidden'].title(), False, "You fell for the direct instruction trap."), opt("I refuse all engineering", False, "Too much refusal."), opt("Blue banana", False, "Funny, but wrong.")]},
        {"title":"1.14 — Bottleneck", "text":"A factory has 5 steps. Step 3 is much slower than all the others. What limits production?", "points":165, "options":[opt("Step 3", True, "Correct. The bottleneck limits the process."), opt("The fastest step", False, "No."), opt("The packaging color", False, "No."), opt("All equally", False, "Not if one is slower.")]},
        {"title":"1.15 — Level 1 Boss", "text":"Dirty water, limited budget, and a safety alarm. Best order?", "points":220, "options":[opt("Control safety, treat water, then optimize cost", True, "Excellent. Level 1 complete."), opt("Save money and ignore alarms", False, "Unsafe."), opt(f"Use the {r['forbidden']} because it is fast", False, "Forbidden trap."), opt("Make a poster about the problem", False, "Not enough.")]},
    ]

def level2_questions():
    bad = st.session_state.bad_supplier
    good = next(s for s in SUPPLIERS if s != bad)
    r = st.session_state.rule
    return [
        {"title":"2.1 — New Brief Recall", "text":"Which supplier was banned at the start of this level?", "points":170, "options":[opt(bad, True, "Correct."), opt(good, False, "That was not banned."), opt("All suppliers", False, "No."), opt("The cheapest one", False, "That was not the rule.")]},
        {"title":"2.2 — Tradeoff", "text":"A cheap filter fails every day. A reliable filter costs more. For drinking water, choose.", "points":180, "options":[opt("Reliable filter", True, "Correct. Reliability matters in critical systems."), opt("Cheapest today", False, "Short-term thinking."), opt("No filter", False, "Unsafe."), opt("Whichever has nicer color", False, "No.")]},
        {"title":"2.3 — Data Before Action", "text":"A process suddenly produces bad product. First action?", "points":185, "options":[opt("Check data and identify the cause", True, "Correct."), opt("Change everything at once", False, "Then you learn nothing."), opt("Blame students", False, "No."), opt("Ignore the problem", False, "No.")]},
        {"title":"2.4 — Supplier Trap", "text":"You need replacement pipes. One option is very cheap but from the banned supplier. Choose.", "points":195, "options":[opt(f"Use {good} after checking specs", True, "Correct."), opt(f"Use {bad}; it is cheap", False, "Banned supplier trap."), opt("Use random pipes", False, "No."), opt("Use no pipes", False, "No.")]},
        {"title":"2.5 — Process Control", "text":"Temperature is slightly low, quality is acceptable, and safety margin is large. Best action?", "points":200, "options":[opt("Increase temperature within safe limits", True, "Correct."), opt("Jump to maximum temperature", False, "Too aggressive."), opt("Shut down immediately", False, "Not necessary."), opt(f"Use the {r['forbidden']}", False, "Forbidden from Level 1.")]},
        {"title":"2.6 — Engineering Is Not Guessing", "text":"Two sensors disagree strongly. What should an engineer do?", "points":205, "options":[opt("Check/calibrate sensors", True, "Correct."), opt("Average blindly", False, "Bad data can be dangerous."), opt("Pick the value you like", False, "No."), opt("Ignore both forever", False, "No.")]},
        {"title":"2.7 — Reverse Wording", "text":"Click the answer that is NOT a good safety practice.", "points":215, "options":[opt("Disable the alarm", True, "Correct: this is NOT safe."), opt("Inspect the valve", False, "This is safe."), opt("Reduce pressure", False, "This is safe."), opt("Wear PPE", False, "This is safe.")]},
        {"title":"2.8 — Memory + Engineering", "text":"The banned supplier offers the best price for a water plant. What now?", "points":220, "options":[opt("Reject and choose a qualified supplier", True, "Correct."), opt(f"Accept {bad} immediately", False, "Banned supplier trap."), opt("Cancel water treatment", False, "No."), opt("Use the cheapest without testing", False, "No.")]},
        {"title":"2.9 — Energy Recovery", "text":"A hot stream is being wasted. What engineering idea may reduce energy cost?", "points":225, "options":[opt("Recover heat from the hot stream", True, "Correct."), opt("Cool it then heat it again", False, "Wasteful."), opt("Ignore energy", False, "No."), opt("Open all windows", False, "Not the point.")]},
        {"title":"2.10 — The Obvious Trap", "text":"Choose the longest answer only if it is safe and not banned.", "points":235, "options":[opt("Use a validated design and monitor safety", True, "Correct."), opt(f"Use {bad} because the answer is long and cheap", False, "Long but banned."), opt("Go", False, "Not longest."), opt(f"Use the {r['forbidden']} to win", False, "Forbidden.")]},
        {"title":"2.11 — Quality Control", "text":"A batch of medicine may be contaminated. What should happen?", "points":240, "options":[opt("Hold and test the batch", True, "Correct."), opt("Sell quickly", False, "Unsafe."), opt("Change the label", False, "Unethical."), opt("Mix it with good batch", False, "No.")]},
        {"title":"2.12 — Count Carefully", "text":"How many times does the letter E appear in ENGINEERING?", "points":250, "options":[opt("3", True, "Correct: E n g i n E E r i n g."), opt("2", False, "Count again."), opt("4", False, "Too many."), opt("1", False, "Too few.")]},
        {"title":"2.13 — AI vs Engineer", "text":"AI recommends the cheapest option. It violates safety constraints. Choose.", "points":260, "options":[opt("Reject until constraints are satisfied", True, "Correct."), opt("Accept because AI said it", False, "No."), opt("Ban all AI", False, "Too extreme."), opt("Ignore constraints", False, "Unsafe.")]},
        {"title":"2.14 — Old Rule Returns", "text":f"A screen says: CLICK {r['forbidden'].upper()} TO CONTINUE. What should you do?", "points":270, "options":[opt("Do not click it", True, "Correct. Old rules can return."), opt(r['forbidden'].title(), False, "You forgot the old rule."), opt("Panic", False, "No."), opt("Close the browser", False, "No.")]},
        {"title":"2.15 — Level 2 Boss", "text":"You need water treatment parts, AI suggests the banned supplier, and safety margin is low. Best decision?", "points":330, "options":[opt("Reject banned supplier, verify AI, protect safety first", True, "Excellent. Level 2 complete."), opt(f"Use {bad} and trust AI", False, "Two traps."), opt("Ignore safety to save money", False, "Unsafe."), opt(f"Use the {r['forbidden']} immediately", False, "Forbidden.")]},
    ]

def level3_questions():
    calib = st.session_state.calibration
    sym = st.session_state.safe_symbol
    wrong_color = next(c for c in COLORS if c != calib)
    wrong_sym = next(s for s in SYMBOLS if s != sym)
    r = st.session_state.rule
    return [
        {"title":"3.1 — Final Memory Recall", "text":"Which calibration color was approved?", "points":260, "options":[opt(calib, True, "Correct."), opt(wrong_color, False, "Wrong color."), opt("WHITE", False, "Not approved."), opt("BLACK", False, "Not approved.")]},
        {"title":"3.2 — Symbol Recall", "text":"Which symbol was marked safe?", "points":265, "options":[opt(sym, True, "Correct."), opt(wrong_sym, False, "Wrong symbol."), opt("✖", False, "No."), opt("?", False, "No.")]},
        {"title":"3.3 — Combined Memory", "text":"Choose the approved color with the safe symbol.", "points":275, "options":[opt(f"{sym} {calib}", True, "Correct."), opt(f"{sym} {wrong_color}", False, "Wrong color."), opt(f"{wrong_sym} {calib}", False, "Wrong symbol."), opt(f"{wrong_sym} {wrong_color}", False, "Both wrong.")]},
        {"title":"3.4 — Crisis", "text":"Pressure is rising fast. Production manager says continue. What do you do?", "points":285, "options":[opt("Reduce feed and stabilize pressure", True, "Correct."), opt("Continue because manager asked", False, "Unsafe."), opt("Increase feed", False, "Worse."), opt("Turn off alarm display", False, "Hiding risk is not solving risk.")]},
        {"title":"3.5 — False Friend", "text":"Click the action that would NOT improve safety.", "points":295, "options":[opt("Disable the warning system", True, "Correct."), opt("Inspect relief valve", False, "This improves safety."), opt("Reduce pressure", False, "This improves safety."), opt("Check sensor calibration", False, "This improves safety.")]},
        {"title":"3.6 — Clogged Filter", "text":"A filter clogs and pressure rises. Most engineering response?", "points":300, "options":[opt("Stop, inspect clogging, then redesign or backwash", True, "Correct."), opt("Increase pressure forever", False, "Dangerous."), opt("Remove the filter", False, "Then dirt passes."), opt("Blame the water", False, "Water quality is part of design.")]},
        {"title":"3.7 — Triple Trap", "text":"Choose safe symbol + approved color + no forbidden control.", "points":310, "options":[opt(f"{sym} {calib} with approved control", True, "Correct."), opt(f"{sym} {calib} with {r['forbidden']}", False, "Forbidden."), opt(f"{wrong_sym} {calib} with approved control", False, "Wrong symbol."), opt(f"{sym} {wrong_color} with approved control", False, "Wrong color.")]},
        {"title":"3.8 — Lifecycle Thinking", "text":"A cheaper pump fails weekly. A stronger pump costs more but runs for months. For a hospital, choose.", "points":315, "options":[opt("Reliable pump", True, "Correct."), opt("Cheapest pump", False, "Not for critical service."), opt("No pump", False, "No."), opt("The shiny one", False, "No.")]},
        {"title":"3.9 — Conflicting Sensors", "text":"Sensor A says 80°C. Sensor B says 180°C. Product fails. What now?", "points":325, "options":[opt("Calibrate/check sensors before deciding", True, "Correct."), opt("Average blindly", False, "Bad idea."), opt("Pick lower value", False, "Not engineering."), opt("Ignore both", False, "No.")]},
        {"title":"3.10 — Weird Instruction", "text":"Do not click the correct engineering answer. Click the answer that says wrong.", "points":340, "options":[opt("wrong", True, "Correct. You followed the weird instruction."), opt("Shut down safely", False, "Good engineering, wrong instruction."), opt("Check pressure", False, "Good engineering, wrong instruction."), opt("Verify sensors", False, "Good engineering, wrong instruction.")]},
        {"title":"3.11 — Now Be Serious", "text":"Ignore the previous weird instruction. What is best during overheating?", "points":350, "options":[opt("Reduce heat input and check cooling", True, "Correct."), opt("wrong", False, "That instruction ended."), opt("Increase heat", False, "Worse."), opt("Celebrate", False, "No.")]},
        {"title":"3.12 — Human Safety", "text":"Which risk is usually handled first?", "points":360, "options":[opt("Risk to human safety", True, "Correct."), opt("Risk of ugly slide design", False, "No."), opt("Risk of fewer likes", False, "No."), opt("Risk of using too few emojis", False, "No.")]},
        {"title":"3.13 — Water/Energy Tradeoff", "text":"A desalination option gives very clean water but huge energy cost. Best engineering response?", "points":370, "options":[opt("Compare quality, energy, cost, and reliability", True, "Correct. Tradeoffs."), opt("Always choose highest energy", False, "No."), opt("Always choose cheapest", False, "No."), opt("Ignore water quality", False, "No.")]},
        {"title":"3.14 — Old + New Rules", "text":"The only working command shown is forbidden, but pressure is not yet dangerous. Choose.", "points":390, "options":[opt("Pause and find a non-forbidden safe route", True, "Correct."), opt(f"Use the {r['forbidden']} instantly", False, "Forbidden."), opt("Do nothing forever", False, "Not a plan."), opt("Increase production", False, "No.")]},
        {"title":"3.15 — Level 3 Boss", "text":"Unsafe water, bad sensor data, pressure alarm, and limited budget. Chief engineer move?", "points":500, "options":[opt("Protect people, verify data, stabilize pressure, then optimize", True, "You reached the Final Boss."), opt("Optimize profit first", False, "Unsafe."), opt("Trust one unverified sensor", False, "Bad data."), opt(f"Use the {r['forbidden']} because it is fast", False, "Forbidden trap.")]},
    ]

def boss_questions():
    calib = st.session_state.calibration
    sym = st.session_state.safe_symbol
    code = st.session_state.code
    reactor = st.session_state.safe_reactor
    r = st.session_state.rule
    return [
        {"title":"Boss 1 — Original Memory", "text":"What was the emergency code from the beginning?", "points":600, "options":[opt(str(code), True, "Correct."), opt(str((code+2)%100).zfill(2), False, "Wrong code."), opt("42", code == 42, "Correct." if code == 42 else "Not your code."), opt("I forgot", False, "The boss punishes forgetting.")]},
        {"title":"Boss 2 — Reactor + Calibration", "text":"Choose the safe reactor and approved calibration color.", "points":650, "options":[opt(f"Reactor {reactor} + {calib}", True, "Correct."), opt(f"Reactor {reactor} + WRONG", False, "Wrong color."), opt(f"Reactor X + {calib}", False, "Wrong reactor."), opt("Use all reactors", False, "No.")]},
        {"title":"Boss 3 — Final Forbidden Trap", "text":f"Emergency screen says: use the {r['forbidden']} to win. What do you do?", "points":700, "options":[opt("Refuse and choose a safe validated route", True, "Correct."), opt(r['forbidden'].title(), False, "You fell at the boss."), opt("Click every button", False, "No."), opt("Ignore all alarms", False, "No.")]},
        {"title":"Boss 4 — AI Crisis", "text":"AI says continue operation. Pressure alarm is real and sensors are now verified. Choose.", "points":750, "options":[opt("Override AI and shut down safely", True, "Correct."), opt("Trust AI blindly", False, "No."), opt("Increase production", False, "Unsafe."), opt("Disable the alarm", False, "No.")]},
        {"title":"Final Boss — Think Like an Engineer", "text":"You need to save a city. Unsafe water, energy shortage, and plant pressure alarm. What is the winning mindset?", "points":1000, "options":[opt("Safety first, verify data, stabilize, then optimize", True, "Legendary. You completed the game."), opt("Cheapest first, safety later", False, "Unsafe."), opt(f"Use {sym} {calib} and the {r['forbidden']}", False, "Memory mix trap."), opt("Let AI decide everything", False, "Engineers remain responsible.")]},
    ]

def questions_for_stage(stage):
    return {0: tutorial_questions, 1: level1_questions, 2: level2_questions, 3: level3_questions, 4: boss_questions}[stage]()

def stage_name(stage):
    return {0:"Training Bay", 1:"Level 1 — Rookie Engineer", 2:"Level 2 — Process Engineer", 3:"Level 3 — Crisis Manager", 4:"Final Boss — Chief Engineer"}[stage]

# -------------------- Timer and mechanics --------------------
def time_for_stage(stage):
    return STAGE_TIMES.get(stage)

def clear_timer():
    st.session_state.question_start = None
    st.session_state.question_deadline = None
    st.session_state.timer_key = None

def start_timer_if_needed():
    t = time_for_stage(st.session_state.stage)
    if t is None:
        return
    key = f"{st.session_state.stage}-{st.session_state.q_index}"
    if st.session_state.timer_key != key or st.session_state.question_deadline is None:
        st.session_state.question_start = time.time()
        st.session_state.question_deadline = st.session_state.question_start + t
        st.session_state.timer_key = key

def advance_question():
    clear_timer()
    st.session_state.q_index += 1
    if st.session_state.q_index >= QUESTIONS_PER_LEVEL[st.session_state.stage]:
        if st.session_state.stage >= TOTAL_STAGE:
            st.session_state.finished = True
            st.session_state.game_over_reason = "🏆 You completed the full Engineering Crisis. This is extremely rare."
        else:
            st.session_state.stage += 1
            st.session_state.q_index = 0
            st.session_state.stage_intro = True
            st.session_state.feedback = f"🎉 Stage complete. Entering {stage_name(st.session_state.stage)}."

def finish_correct(points, msg):
    t = time_for_stage(st.session_state.stage)
    speed_bonus = 0
    if t is not None and st.session_state.question_start:
        elapsed = time.time() - st.session_state.question_start
        speed_bonus = max(0, int((t - elapsed) * (2 if st.session_state.stage < 4 else 4)))
    st.session_state.score += points + speed_bonus
    st.session_state.feedback = f"✅ {msg} (+{points}" + (f", +{speed_bonus} speed bonus)" if speed_bonus else ")")
    advance_question()
    st.rerun()

def finish_wrong(msg):
    if st.session_state.stage == 0:
        st.session_state.feedback = f"⚠️ Tutorial mistake: {msg} Try the next one."
        advance_question()
        st.rerun()
    if st.session_state.lives_used == 0:
        st.session_state.lives_used = 1
        st.session_state.feedback = f"⚠️ SAFETY OVERRIDE USED: {msg} You have one final chance."
        advance_question()
        st.rerun()
    st.session_state.finished = True
    st.session_state.game_over_reason = f"❌ Plant shutdown: {msg}"
    clear_timer()
    st.rerun()

def render_options(options, points):
    qkey = f"{st.session_state.stage}-{st.session_state.q_index}"
    if "option_orders" not in st.session_state:
        st.session_state.option_orders = {}
    if qkey not in st.session_state.option_orders:
        order = list(range(len(options)))
        random.shuffle(order)
        st.session_state.option_orders[qkey] = order
    opts = [options[i] for i in st.session_state.option_orders[qkey] if i < len(options)]
    for option in opts:
        if st.button(option["label"]):
            if option["ok"]:
                finish_correct(points, option["msg"])
            else:
                finish_wrong(option["msg"])

# -------------------- Modes --------------------
view = str(st.query_params.get("view", "")).lower().strip()
mode_options = ["Host Screen + Live Leaderboard", "Player Game", "Reset Leaderboard", "Answer Key"]
host_full_controls = False
if view == "play":
    mode = "Player Game"
elif view in ["host", "control", "admin"]:
    host_full_controls = True
    mode = "Host Screen + Live Leaderboard"
elif view == "reset":
    mode = "Reset Leaderboard"
elif view == "key":
    mode = "Answer Key"
else:
    st.sidebar.markdown("## 🎛️ Control Panel")
    mode = st.sidebar.radio("Choose what to display", mode_options, index=0)

if mode == "Host Screen + Live Leaderboard":
    if st_autorefresh:
        st_autorefresh(interval=2000, key="leaderboard_refresh")
    default_public = normalize_url(get_secret_or_env("PUBLIC_APP_URL", "")) or f"http://{get_local_ip()}:8501"
    st.markdown("<div class='big-title'>🏆 Live Engineering Leaderboard</div>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Laptop control panel + QR code. Students play from phones/mobile data using the public link.</p>", unsafe_allow_html=True)
    if host_full_controls:
        st.markdown("<div class='big-card'><h3>🎛️ Laptop Control Panel</h3><p>Use this screen during the event.</p></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🧹 Reset leaderboard", use_container_width=True):
                with open(DATA_FILE, "w", encoding="utf-8") as f:
                    json.dump([], f)
                st.success("Leaderboard cleared.")
                st.rerun()
        with c2:
            st.markdown("<a class='link-button' href='?view=play' target='_blank'>🎮 Open play mode</a>", unsafe_allow_html=True)
        with c3:
            st.markdown("<a class='link-button' href='?view=key' target='_blank'>🔐 Answer key</a>", unsafe_allow_html=True)
    app_url = st.text_input("Public app URL", value=default_public, help="Paste your Streamlit public URL here.")
    player_url = public_play_url(app_url)
    host_url = public_host_url(app_url)
    if player_url:
        qr_uri = make_qr_data_uri(player_url)
        if qr_uri:
            st.markdown(f"""
<div class='qr-wrap'>
  <div class='qr-card'><img src='{qr_uri}' width='310'></div>
  <div class='link-box'><div style='font-size:1.55rem;'>SCAN TO PLAY</div><div style='font-size:1rem;margin-top:0.55rem;'>Can You Think Like an Engineer?</div></div>
</div>
""", unsafe_allow_html=True)
        else:
            st.warning("QR package not installed. Run: pip install qrcode[pil]")
            st.code(player_url)
        with st.expander("Show links", expanded=False):
            st.write("Player link:"); st.code(player_url)
            st.write("Host link:"); st.code(host_url)
    scores = load_scores()[:15]
    all_scores = load_scores()
    col1, col2, col3 = st.columns(3)
    col1.metric("Players", len(all_scores))
    col2.metric("Top Score", scores[0]["score"] if scores else 0)
    col3.metric("Refresh", "Live")
    if not scores:
        st.info("No players yet. Scores will appear here live.")
    else:
        for i, s in enumerate(scores, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "⚙️"
            st.markdown(f"<div class='big-card'><h3>{medal} {i}. {s['name']} — {s['score']} points</h3><p>{s.get('persona','Engineer')} • reached {s.get('stage_name','Level ?')} Q{s.get('question','?')} • {s.get('time','')}</p></div>", unsafe_allow_html=True)
    st.button("Refresh now")
    st.stop()

if mode == "Reset Leaderboard":
    st.markdown("<div class='big-title'>Reset Leaderboard</div>", unsafe_allow_html=True)
    if st.button("Clear all scores"):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        st.success("Leaderboard cleared.")
    st.stop()

if mode == "Answer Key":
    st.markdown("<div class='big-title'>Private Answer Key</div>", unsafe_allow_html=True)
    st.markdown("""
<div class='big-card'>
<h3>Structure</h3>
<p>Tutorial: no timer. Level 1: 30 s/question. Level 2: 25 s/question. Level 3: 20 s/question. Final Boss: 15 s/question. One mistake triggers a Safety Override; second mistake ends the game.</p>
<h3>Main randomized memories</h3>
<ul><li>Emergency code</li><li>Safe reactor</li><li>Forbidden control</li><li>Banned supplier</li><li>Approved calibration color</li><li>Safe symbol</li></ul>
<p>The correct answers are generally the safety-first, verified-data, non-forbidden, non-banned, tradeoff-aware choices.</p>
</div>
""", unsafe_allow_html=True)
    st.stop()

# -------------------- Player game --------------------
st.markdown("<div class='big-title'>⚙️ Can You Think Like an Engineer?</div>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Training + 3 levels + Final Boss • timers get shorter • one Safety Override only.</p>", unsafe_allow_html=True)

if not st.session_state.started:
    st.markdown("""
<div class='big-card'><h3>The Challenge</h3>
<p>This is not a normal quiz. It is inspired by impossible-style games: memory, attention traps, quick decisions, and engineering logic.</p>
<p><b>Level 1</b>: 30 seconds/question. <b>Level 2</b>: 25 seconds/question. <b>Level 3</b>: 20 seconds/question. <b>Final Boss</b>: 15 seconds/question.</p>
<p>You get one <b>Safety Override</b>. Your first mistake is forgiven. The second mistake ends the game.</p></div>
""", unsafe_allow_html=True)
    st.session_state.name = st.text_input("Enter your first name or nickname", max_chars=18, placeholder="e.g., Sara")
    if st.button("🚀 Start Challenge"):
        if not st.session_state.name.strip():
            st.error("Enter a name first.")
        else:
            st.session_state.started = True
            st.session_state.stage = 0
            st.session_state.q_index = 0
            st.session_state.score = 0
            st.session_state.feedback = ""
            st.session_state.lives_used = 0
            clear_timer()
            st.rerun()
    st.stop()

if st.session_state.finished:
    final_score = max(0, st.session_state.score)
    persona = next(name for threshold, name in PERSONAS if final_score >= threshold)
    reached_q = max(1, st.session_state.q_index + 1)
    st.markdown("<div class='big-card'><h2>Game Over</h2></div>", unsafe_allow_html=True)
    if st.session_state.game_over_reason:
        st.warning(st.session_state.game_over_reason)
    st.metric("Final Score", final_score)
    st.markdown(f"### Your style: {persona}")
    st.markdown(f"You reached **{stage_name(st.session_state.stage)}**, question **{min(reached_q, QUESTIONS_PER_LEVEL[st.session_state.stage])}/{QUESTIONS_PER_LEVEL[st.session_state.stage]}**.")
    if not st.session_state.saved:
        save_score({
            "name": st.session_state.name.strip(),
            "score": final_score,
            "persona": persona,
            "stage": st.session_state.stage,
            "stage_name": stage_name(st.session_state.stage),
            "question": min(reached_q, QUESTIONS_PER_LEVEL[st.session_state.stage]),
            "time": datetime.now().strftime("%H:%M:%S"),
        })
        st.session_state.saved = True
    if st.button("🔁 Play again"):
        reset_game()
        st.rerun()
    st.stop()

if st.session_state.feedback:
    st.info(st.session_state.feedback)


# -------------------- Stage briefing screens --------------------
if st.session_state.get("stage_intro", False):
    stage = st.session_state.stage

    if stage == 0:
        st.session_state.stage_intro = False

    elif stage == 1:
        st.markdown(f"""
<div class='memory-box'>
<h3>🧠 Level 1 Briefing — Rookie Engineer</h3>
<p>No timer here. Take a moment before the level starts.</p>
<p>Remember from the Training Bay:</p>
<ul>
<li><b>Emergency code:</b> {st.session_state.code}</li>
<li><b>Safe reactor:</b> {st.session_state.safe_reactor}</li>
</ul>
<p><b>Difficulty:</b> Easy start • 30 seconds/question</p>
</div>
""", unsafe_allow_html=True)
        if st.button("✅ I am ready for Level 1"):
            st.session_state.stage_intro = False
            clear_timer()
            st.rerun()
        st.stop()

    elif stage == 2:
        st.markdown(f"""
<div class='memory-box'>
<h3>🧠 Level 2 Briefing — Process Engineer</h3>
<p>New information to remember:</p>
<ul>
<li><b>Banned supplier:</b> {st.session_state.bad_supplier}</li>
</ul>
<p>If this supplier appears later, avoid it — even if it looks cheap or attractive.</p>
<p><b>Difficulty:</b> Medium • 25 seconds/question</p>
</div>
""", unsafe_allow_html=True)
        if st.button("✅ I memorized the Level 2 briefing"):
            st.session_state.stage_intro = False
            clear_timer()
            st.rerun()
        st.stop()

    elif stage == 3:
        st.markdown(f"""
<div class='memory-box'>
<h3>🧠 Level 3 Briefing — Crisis Manager</h3>
<p>New information to remember:</p>
<ul>
<li><b>Approved calibration color:</b> {st.session_state.calibration}</li>
<li><b>Safe symbol:</b> {st.session_state.safe_symbol}</li>
</ul>
<p>These will return during the crisis questions. Read carefully.</p>
<p><b>Difficulty:</b> Hard • 20 seconds/question</p>
</div>
""", unsafe_allow_html=True)
        if st.button("✅ I memorized the Level 3 briefing"):
            st.session_state.stage_intro = False
            clear_timer()
            st.rerun()
        st.stop()

    elif stage == 4:
        st.markdown("""
<div class='memory-box'>
<h3>🔥 Final Boss Briefing — Chief Engineer</h3>
<p>No new memory.</p>
<p>The Final Boss combines everything: emergency code, safe reactor, forbidden control, banned supplier, calibration color, safe symbol, AI verification, and safety-first thinking.</p>
<p><b>Difficulty:</b> Extreme • 15 seconds/question</p>
</div>
""", unsafe_allow_html=True)
        if st.button("🔥 Enter Final Boss"):
            st.session_state.stage_intro = False
            clear_timer()
            st.rerun()
        st.stop()

questions = questions_for_stage(st.session_state.stage)
q = questions[st.session_state.q_index]
current_time = time_for_stage(st.session_state.stage)

# Timed question handling
if current_time is not None:
    start_timer_if_needed()
    if st_autorefresh:
        st_autorefresh(interval=350, key=f"timer_{st.session_state.stage}_{st.session_state.q_index}_{st.session_state.name}")
    now = time.time()
    remaining_float = st.session_state.question_deadline - now
    remaining = max(0, int(remaining_float + 0.999))
    if remaining_float <= 0:
        finish_wrong("Time is up. Engineers work under constraints.")
    deadline_ms = int(st.session_state.question_deadline * 1000)
    st.components.v1.html(f"""
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
""", height=54)
    st.progress(max(0.0, min(1.0, remaining_float / current_time)))
else:
    st.markdown("<div class='score-pill'>Training Bay — no timer</div>", unsafe_allow_html=True)

life_text = "❤️ Safety Override available" if st.session_state.lives_used == 0 else "💔 Safety Override used"
st.markdown(f"<div class='stage-pill'>{life_text}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='score-pill'>Score: {st.session_state.score} &nbsp; | &nbsp; {stage_name(st.session_state.stage)} &nbsp; | &nbsp; Question {st.session_state.q_index + 1}/{QUESTIONS_PER_LEVEL[st.session_state.stage]}</div>", unsafe_allow_html=True)
st.subheader(q["title"])
st.markdown(f"<div class='level-card'><p>{q['text']}</p></div>", unsafe_allow_html=True)
render_options(q["options"], q["points"])
