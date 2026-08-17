
import streamlit as st
import random
from datetime import datetime

st.set_page_config(
    page_title="CHEN212 Mission 01",
    page_icon="⚗️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------- Styling ----------
st.markdown("""
<style>
.block-container {max-width: 860px; padding-top: 1.2rem; padding-bottom: 2rem;}
.hero {
    padding: 1.2rem 1.4rem;
    border-radius: 18px;
    border: 1px solid rgba(127,127,127,.22);
    margin-bottom: 1rem;
}
.mission {
    padding: .85rem 1rem;
    border-radius: 14px;
    border: 1px solid rgba(127,127,127,.20);
    margin: .7rem 0;
}
.badge {
    display:inline-block; padding:.25rem .65rem; border-radius:999px;
    border:1px solid rgba(127,127,127,.28); font-size:.9rem; margin-right:.35rem;
}
.bigscore {font-size:2.2rem; font-weight:750;}
.smallmuted {opacity:.72; font-size:.92rem;}
hr {margin-top:1.1rem; margin-bottom:1.1rem;}
</style>
""", unsafe_allow_html=True)

# ---------- State ----------
if "page" not in st.session_state:
    st.session_state.page = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "answered" not in st.session_state:
    st.session_state.answered = {}
if "student_name" not in st.session_state:
    st.session_state.student_name = ""
if "secret_card" not in st.session_state:
    st.session_state.secret_card = random.choice([
        ("ENERGY", "Energy prices are expected to double next year."),
        ("PRODUCTION", "Management requires at least 480 tonnes/day."),
        ("SAFETY", "The company has had two serious high-pressure incidents in the past five years."),
        ("RECYCLE", "Unreacted A can be recycled very cheaply.")
    ])
if "decision_reason" not in st.session_state:
    st.session_state.decision_reason = ""
if "decision_info" not in st.session_state:
    st.session_state.decision_info = ""
if "final_choice" not in st.session_state:
    st.session_state.final_choice = ""

TOTAL_AUTO = 18

def header(title, subtitle=None):
    st.markdown(f'<div class="hero"><h1 style="margin:0">{title}</h1>' +
                (f'<div class="smallmuted">{subtitle}</div>' if subtitle else '') +
                '</div>', unsafe_allow_html=True)

def next_button(label="Continue →"):
    if st.button(label, use_container_width=True, type="primary"):
        st.session_state.page += 1
        st.rerun()

def check_single(key, prompt, options, correct, explanation, points=1):
    st.markdown(f"**{prompt}**")
    choice = st.radio("Choose one:", options, key=key, label_visibility="collapsed")
    submitted_key = f"{key}_submitted"
    if not st.session_state.get(submitted_key, False):
        if st.button("Submit answer", key=f"{key}_btn", use_container_width=True):
            st.session_state[submitted_key] = True
            ok = choice == correct
            if ok:
                st.session_state.score += points
                st.success(f"Correct. {explanation}")
            else:
                st.error(f"Not quite. Correct answer: **{correct}**. {explanation}")
            st.rerun()
    else:
        ok = choice == correct
        (st.success if ok else st.error)(
            ("Correct. " if ok else f"Correct answer: **{correct}**. ") + explanation
        )
    st.divider()

# ---------- Pages ----------
p = st.session_state.page

if p == 0:
    header("⚗️ CHEN212 — Mission 01", "FROM LAB BENCH TO CHEMICAL PLANT")
    st.markdown("""
You have joined a process-development team.

A laboratory discovery looks promising. Management now wants to scale it to industrial production.

Your mission is to decide whether the process is truly ready.

<span class="badge">Part 1 · Knowledge Check</span>
<span class="badge">Part 2 · Scale-Up</span>
<span class="badge">Part 3 · Engineering Decision</span>
<span class="badge">Part 4 · Team Briefing</span>
""", unsafe_allow_html=True)
    st.info("This is not a speed test. Think like an engineer: identify what matters, challenge assumptions, and justify decisions.")
    st.session_state.student_name = st.text_input("Your first name", value=st.session_state.student_name, placeholder="e.g., Maya")
    if st.button("Start mission 🚀", use_container_width=True, type="primary", disabled=not st.session_state.student_name.strip()):
        st.session_state.page = 1
        st.rerun()

elif p == 1:
    header("Part 1 — Scientist or Engineer?", "Quickfire knowledge check")
    st.progress(0.15)
    check_single("q1", "1. Why does a new catalyst increase the reaction rate?",
                 ["Primarily scientific", "Primarily engineering", "Could be either"],
                 "Primarily scientific",
                 "The emphasis is on understanding the phenomenon.")
    check_single("q2", "2. At what temperature should an industrial reactor operate to balance conversion, energy cost, and safety?",
                 ["Primarily scientific", "Primarily engineering", "Could be either"],
                 "Primarily engineering",
                 "The question asks for a practical decision under multiple constraints.")
    check_single("q3", "3. Determine the molecular mechanism by which a pollutant binds to activated carbon.",
                 ["Primarily scientific", "Primarily engineering", "Could be either"],
                 "Primarily scientific",
                 "The primary goal is to explain why the phenomenon occurs.")
    check_single("q4", "4. Determine how much activated carbon is needed to treat 5 million L/day of wastewater.",
                 ["Primarily scientific", "Primarily engineering", "Could be either"],
                 "Primarily engineering",
                 "This applies knowledge to a real process at useful scale.")
    check_single("q5", "5. Develop a new catalyst and test whether it improves conversion.",
                 ["Primarily scientific", "Primarily engineering", "Could be either"],
                 "Could be either",
                 "The boundary is not absolute; the answer depends on the goal and context.")
    check_single("q6", "6. A process works technically, but it is extremely expensive and unsafe. Has the engineering problem been solved?",
                 ["Yes", "No"],
                 "No",
                 "Engineering must also consider constraints such as safety, cost, reliability, and practicality.")

    st.subheader("Match the concern")
    st.caption("For each situation, choose the engineering concern it most directly raises.")
    match_items = [
        ("The reactor operates at extremely high pressure.", "Safety"),
        ("The process uses a huge amount of electricity.", "Energy"),
        ("Large quantities of hazardous waste are produced.", "Environment"),
        ("The product can be made, but at $20/kg instead of $2/kg.", "Cost"),
    ]
    match_options = ["Safety", "Energy", "Environment", "Cost"]
    all_correct = True
    for i, (situation, answer) in enumerate(match_items, start=1):
        sel = st.selectbox(situation, ["— choose —"] + match_options, key=f"match_{i}")
        if sel != answer:
            all_correct = False
    if not st.session_state.get("match_done", False):
        if st.button("Check my matches", use_container_width=True):
            st.session_state.match_done = True
            correct_n = sum(st.session_state.get(f"match_{i}") == ans for i, (_, ans) in enumerate(match_items, start=1))
            st.session_state.score += correct_n
            st.rerun()
    else:
        if all_correct:
            st.success("Perfect match. You identified four of the major constraints that shape an engineering decision.")
        else:
            st.warning("Review the matches: high pressure → Safety; electricity use → Energy; hazardous waste → Environment; product price → Cost.")
    next_button("Enter the scale-up challenge →")

elif p == 2:
    header("Part 2 — Scale-Up Challenge", "The lab result is only the beginning")
    st.progress(0.42)
    st.markdown("""
<div class="mission">
<h3>🧪 LAB SUCCESS</h3>
A chemist has developed a new reaction:

**A → B**

In a **100 mL** laboratory reactor, the process gives **95% conversion**.

The CEO says: **“Excellent. Build a plant that produces 500 tonnes of B per day.”**
</div>
""", unsafe_allow_html=True)

    st.subheader("Challenge A — What matters before scale-up?")
    choices = st.multiselect(
        "Select the FIVE most important questions to investigate first:",
        [
            "How much raw material is available?",
            "What temperature and pressure are required?",
            "How much heat is released?",
            "What colour should the factory walls be?",
            "How will B be separated from unreacted material?",
            "Is the process economically viable?",
            "Who discovered the reaction?",
            "What hazards appear at large scale?"
        ],
        key="five_select"
    )
    if not st.session_state.get("five_done", False):
        if st.button("Lock in my five", use_container_width=True, disabled=len(choices)!=5):
            ideal = {
                "What temperature and pressure are required?",
                "How much heat is released?",
                "How will B be separated from unreacted material?",
                "Is the process economically viable?",
                "What hazards appear at large scale?"
            }
            # Raw-material availability is also defensible, so award by overlap.
            defensible = ideal | {"How much raw material is available?"}
            points = len(set(choices) & defensible)
            st.session_state.score += min(points, 5)
            st.session_state.five_done = True
            st.rerun()
    else:
        st.success("Good. In real engineering, several answers can be defensible. The important point is to identify scale, operating conditions, heat removal, separations, hazards, economics, and feed availability.")
    st.divider()

    check_single("q7", "If every characteristic length of geometrically similar equipment increases by a factor of 10, approximately how much does its volume increase?",
                 ["10×", "100×", "1000×", "10,000×"],
                 "1000×",
                 "Volume scales approximately with L³.")
    check_single("q8", "What happens to the surface-area-to-volume ratio as equipment gets larger?",
                 ["It increases", "It decreases", "It stays constant", "It becomes zero"],
                 "It decreases",
                 "Surface area scales with L² while volume scales with L³.")
    check_single("q9", "Why can this matter for an exothermic reaction?",
                 ["The reaction automatically stops",
                  "Heat may become harder to remove relative to the amount generated",
                  "The reactor becomes weightless",
                  "Pressure must become zero"],
                 "Heat may become harder to remove relative to the amount generated",
                 "A process that is safe in a flask may overheat when scaled up.")
    next_button("Proceed to the engineering decision →")

elif p == 3:
    header("Part 3 — Engineering Decision", "There may not be one perfect answer")
    st.progress(0.68)
    st.markdown("""
### Management gives you three options

**Process A**
- 98% conversion
- very high pressure
- high energy consumption
- highest production rate
- significant safety concern

**Process B**
- 92% conversion
- moderate pressure
- moderate energy use
- safer
- lower operating cost

**Process C**
- 85% conversion
- very low energy consumption
- low pressure
- large amount of unreacted material leaves the process
""")
    st.markdown("---")
    st.subheader("🔐 Confidential information")
    label, secret = st.session_state.secret_card
    st.warning(f"**{label}:** {secret}")
    st.caption("Do not show this to your classmates yet.")

    choice = st.radio("Which process would you recommend initially?", ["Process A", "Process B", "Process C"], key="proc_choice")
    reason = st.text_area("Give your TWO strongest reasons.", value=st.session_state.decision_reason,
                          placeholder="1. ...\n2. ...", height=110)
    info = st.text_input("What ONE additional piece of information would you most want before final approval?",
                         value=st.session_state.decision_info,
                         placeholder="e.g., capital cost, required production rate, recycle feasibility...")
    if st.button("Submit my recommendation", use_container_width=True, type="primary", disabled=(len(reason.strip())<15 or len(info.strip())<3)):
        st.session_state.decision_reason = reason
        st.session_state.decision_info = info
        st.session_state.final_choice = choice
        st.session_state.page = 4
        st.rerun()

elif p == 4:
    header("Part 4 — Team Briefing", "Now reveal what you knew")
    st.progress(0.88)
    st.success(f"Initial recommendation: **{st.session_state.final_choice}**")
    st.markdown(f"**Your reasons:**\n\n{st.session_state.decision_reason}")
    st.markdown(f"**Information you still wanted:** {st.session_state.decision_info}")
    st.divider()
    st.subheader("👥 Classroom instruction")
    st.markdown("""
1. **Reveal your confidential information** to the group.
2. Listen to what the others knew.
3. As a team, agree on **one final recommendation**.
4. Be ready to defend it in **30 seconds**.
""")
    final_team = st.radio("After discussion, what does your team recommend?", ["Process A", "Process B", "Process C", "We need more information"], key="team_final")
    team_reason = st.text_area("Write the team's final justification in 2–4 sentences.", key="team_reason", height=120)
    if st.button("Complete mission ✅", use_container_width=True, type="primary", disabled=len(team_reason.strip())<20):
        st.session_state.page = 5
        st.rerun()

elif p == 5:
    header("Mission Complete ✅", "You have made your first engineering recommendation")
    st.progress(1.0)
    st.markdown(f'<div class="bigscore">{st.session_state.score}/{TOTAL_AUTO}+</div>', unsafe_allow_html=True)
    st.caption("Automatic score covers the knowledge and scale-up items. Your engineering decision is judged on reasoning, not speed.")
    st.markdown("""
### What this mission was testing
- Scientist vs engineer
- Engineering as application of scientific knowledge
- Real-world constraints and judgment
- Why scale-up is not simple multiplication
- Why engineers need information from one another

### Final paper memo
Before returning to the lecture, write on the memo card your instructor gives you:

1. **The first issue I would investigate is…**
2. **This matters because…**
3. **Before approving the plant, I would also need to know…**
""")
    st.info("Next topic: **The Engineering Team** — because no single person had all the information needed to make the decision.")
    if st.button("Restart mission", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
