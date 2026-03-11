import streamlit as st
import time
import httpx

from backend.core import build_graph  # direct pipeline call

# ── Config ─────────────────────────────────────────────────────────────────────
API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="AI Financial Research Assistant",
    page_icon="💼",
    layout="wide",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Lora:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Mono', monospace;
    background-color: #080808;
    color: #e8e8e8;
}
.stApp { background-color: #080808; }
[data-testid="stSidebar"] { background-color: #0a0a0a; border-right: 1px solid #1a1a1a; }
[data-testid="stSidebar"] * { font-family: 'DM Mono', monospace !important; }
header[data-testid="stHeader"] { background: transparent; }

.stTextInput > div > div > input {
    background-color: #111 !important;
    border: 1px solid #2a2a2a !important;
    color: #fff !important;
    font-family: 'DM Mono', monospace !important;
    border-radius: 8px !important;
}
.stButton > button {
    background: linear-gradient(135deg, #00D4FF, #00FF9F) !important;
    color: #000 !important;
    font-family: 'DM Mono', monospace !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    letter-spacing: 0.05em !important;
    width: 100%;
}
.stButton > button:hover { opacity: 0.85 !important; transform: translateY(-1px); }
.stProgress > div > div > div { background: linear-gradient(90deg, #00D4FF, #00FF9F) !important; border-radius: 4px !important; }
.stProgress > div > div { background-color: #1a1a1a !important; border-radius: 4px !important; }
.streamlit-expanderHeader { background-color: #0d0d0d !important; border: 1px solid #222 !important; border-radius: 8px !important; color: #aaa !important; font-size: 12px !important; }
[data-testid="metric-container"] { background-color: #111 !important; border: 1px solid #222 !important; border-radius: 10px !important; padding: 14px !important; }
[data-testid="stMetricLabel"] { color: #555 !important; font-size: 11px !important; }
[data-testid="stMetricValue"] { color: #fff !important; font-size: 18px !important; }
hr { border-color: #1a1a1a !important; }
.stSelectbox > div > div { background-color: #111 !important; border: 1px solid #2a2a2a !important; color: #fff !important; }
p, li, span { color: #ccc; }
h1, h2, h3 { color: #fff !important; font-family: 'Lora', serif !important; }
.agent-box { background: #0d0d0d; border: 1px solid #222; border-radius: 10px; padding: 12px 16px; margin-bottom: 8px; }
.agent-active { border-color: #00D4FF; box-shadow: 0 0 12px #00D4FF20; }
.agent-done   { border-color: #00FF9F; box-shadow: 0 0 8px #00FF9F15; }
.stTabs [data-baseweb="tab-list"] { background-color: #0d0d0d !important; border-radius: 8px; }
.stTabs [data-baseweb="tab"] { color: #555 !important; font-family: 'DM Mono', monospace !important; }
.stTabs [aria-selected="true"] { color: #00D4FF !important; }
</style>
""", unsafe_allow_html=True)


# ── API helpers — ONLY your 3 endpoints ───────────────────────────────────────
def api_register(email: str, password: str, full_name: str):
    r = httpx.post(f"{API_BASE}/auth/register", json={
        "email": email, "password": password, "full_name": full_name
    }, timeout=10)
    return r.json(), r.status_code


def api_login(email: str, password: str):
    # OAuth2PasswordRequestForm needs form data (not JSON)
    # "username" field = email in your case
    r = httpx.post(f"{API_BASE}/auth/login", data={
        "username":   email,
        "password":   password,
        "grant_type": "password",
    }, timeout=10)
    return r.json(), r.status_code


def api_me(token: str):
    r = httpx.get(f"{API_BASE}/auth/me",
                  headers={"Authorization": f"Bearer {token}"}, timeout=10)
    return r.json(), r.status_code


# ── Pipeline (direct — same as your original app) ──────────────────────────────
@st.cache_resource(show_spinner=False)
def get_app():
    return build_graph()


# ── Session defaults ───────────────────────────────────────────────────────────
for key, default in [
    ("token",       None),
    ("user",        None),
    ("final_state", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ══════════════════════════════════════════════════════════════════════════════
# AUTH SCREEN  — shown when not logged in
# ══════════════════════════════════════════════════════════════════════════════
def show_auth():
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='text-align:center;margin-bottom:32px'>
            <div style='font-size:48px'>💼</div>
            <div style='font-family:Lora,serif;font-size:26px;color:#fff;margin-top:8px'>Financial Research AI</div>
            <div style='font-size:11px;color:#555;letter-spacing:0.15em;margin-top:4px'>LANGGRAPH · GEMINI · FAISS</div>
        </div>
        """, unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["🔑 Login", "✨ Register"])

        # ── LOGIN ──────────────────────────────────────────────────────────────
        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            email    = st.text_input("Email",    key="login_email",    placeholder="you@example.com")
            password = st.text_input("Password", key="login_password", type="password", placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("LOGIN →", key="login_btn", use_container_width=True):
                if not email or not password:
                    st.error("Please fill in all fields.")
                else:
                    with st.spinner("Authenticating…"):
                        data, code = api_login(email, password)
                    if code == 200:
                        st.session_state.token = data["access_token"]
                        me_data, _ = api_me(st.session_state.token)
                        st.session_state.user = me_data
                        st.success("Welcome back! 🎉")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(data.get("detail", "Login failed."))

        # ── REGISTER ───────────────────────────────────────────────────────────
        with tab_register:
            st.markdown("<br>", unsafe_allow_html=True)
            full_name  = st.text_input("Full Name", key="reg_name",     placeholder="John Doe")
            email_r    = st.text_input("Email",     key="reg_email",    placeholder="you@example.com")
            password_r = st.text_input("Password",  key="reg_password", type="password", placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("CREATE ACCOUNT →", key="register_btn", use_container_width=True):
                if not email_r or not password_r:
                    st.error("Email and password are required.")
                else:
                    with st.spinner("Creating account…"):
                        data, code = api_register(email_r, password_r, full_name)
                    if code == 201:
                        st.success("Account created! Switch to Login tab.")
                    else:
                        st.error(data.get("detail", "Registration failed."))


# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP SCREEN — shown after login
# ══════════════════════════════════════════════════════════════════════════════
def show_app():
    user = st.session_state.user or {}

    # ── Sidebar ────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"""
        <div style='background:#111;border:1px solid #222;border-radius:10px;padding:12px 16px;margin-bottom:16px'>
            <div style='font-size:10px;color:#555;letter-spacing:0.1em'>LOGGED IN AS</div>
            <div style='font-size:13px;color:#00FF9F;margin-top:4px'>{user.get('email', '')}</div>
            <div style='font-size:11px;color:#444'>{user.get('full_name', '')}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 💼 AI Financial Research")
        st.markdown("<p style='font-size:10px;color:#555;letter-spacing:0.1em'>LANGGRAPH · GEMINI · FAISS</p>", unsafe_allow_html=True)
        st.divider()

        company = st.text_input("Target Company", value="Apple", placeholder="e.g. Tesla, Microsoft…")
        preset  = st.selectbox("Quick Picks", ["── select ──", "Apple", "Tesla", "Microsoft", "Amazon", "Nvidia", "Google"])
        if preset != "── select ──":
            company = preset

        st.divider()

        st.markdown("<p style='font-size:10px;color:#555;letter-spacing:0.1em'>PIPELINE NODES</p>", unsafe_allow_html=True)
        for node, icon, color in [
            ("supervisor", "🧠", "#aaa"),
            ("research",   "🔍", "#00D4FF"),
            ("rag",        "📄", "#00FF9F"),
            ("risk",       "⚠️",  "#FFB800"),
            ("writer",     "📝", "#FF6B6B"),
        ]:
            st.markdown(f"<div style='font-size:11px;color:{color};padding:4px 0'>{icon} &nbsp;{node}</div>", unsafe_allow_html=True)

        st.divider()
        analyze_btn = st.button("ANALYZE →", use_container_width=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # Logout — clears session → back to auth screen
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.token       = None
            st.session_state.user        = None
            st.session_state.final_state = None
            st.rerun()

    # ── Header ─────────────────────────────────────────────────────────────────
    col_title, col_badge = st.columns([5, 1])
    with col_title:
        st.markdown("## Investment Research Assistant")
        st.markdown("<p style='color:#555;font-size:12px;margin-top:-12px'>Multi-agent pipeline · Real-time web search · RAG document analysis</p>", unsafe_allow_html=True)
    with col_badge:
        if st.session_state.final_state:
            st.markdown("<div style='background:#00FF9F15;border:1px solid #00FF9F40;border-radius:8px;padding:8px 14px;text-align:center;margin-top:12px'><div style='font-size:10px;color:#00FF9F'>STATUS</div><div style='font-size:14px;color:#00FF9F;font-weight:700'>READY</div></div>", unsafe_allow_html=True)

    st.divider()

    # ── Pipeline ───────────────────────────────────────────────────────────────
    if analyze_btn and company.strip():
        st.session_state.final_state = None

        col_agents, col_log = st.columns([1, 2])

        with col_agents:
            st.markdown("<p style='font-size:10px;color:#555;letter-spacing:0.1em'>AGENT STATUS</p>", unsafe_allow_html=True)
            placeholders = {}
            for agent, icon in [("supervisor","🧠"), ("research","🔍"), ("rag","📄"), ("risk","⚠️"), ("writer","📝")]:
                placeholders[agent] = st.empty()
                placeholders[agent].markdown(
                    f"<div class='agent-box'>{icon} <span style='font-size:12px;color:#444'>{agent} — waiting</span></div>",
                    unsafe_allow_html=True,
                )

        with col_log:
            st.markdown("<p style='font-size:10px;color:#555;letter-spacing:0.1em'>SUPERVISOR LOG</p>", unsafe_allow_html=True)
            log_placeholder = st.empty()
            logs = []

        progress_bar = st.progress(0)
        status_text  = st.empty()

        def update_agent(name, icon, state, color, msg):
            css = "agent-active" if state == "running" else "agent-done" if state == "done" else "agent-box"
            dot = f"<span style='color:{color}'>⬤</span> " if state == "running" else ("✅ " if state == "done" else "")
            placeholders[name].markdown(
                f"<div class='agent-box {css}'>{icon} <span style='font-size:12px;color:{color}'>{dot}{name}</span>"
                f"<br><span style='font-size:10px;color:#555;margin-left:4px'>{msg}</span></div>",
                unsafe_allow_html=True,
            )

        def add_log(msg, color="#00D4FF"):
            logs.append(f"<span style='color:{color}'>{msg}</span>")
            log_placeholder.markdown(
                "<div style='background:#0d0d0d;border:1px solid #1a1a1a;border-radius:10px;padding:14px;font-size:11px;line-height:1.8'>"
                + "<br>".join(logs) + "</div>",
                unsafe_allow_html=True,
            )

        try:
            app = get_app()

            initial_state = {
                "query":           f"Analyze {company} for investment",
                "company":         company,
                "research_result": "",
                "rag_result":      "",
                "risk_result":     "",
                "final_result":    "",
                "next":            "",
            }

            add_log(f"Starting analysis for {company}…", "#aaa")
            update_agent("supervisor", "🧠", "running", "#aaa", "routing…")
            progress_bar.progress(5)

            for step_num, step in enumerate(app.stream(initial_state)):
                node_name = list(step.keys())[0]
                node_out  = step[node_name]

                if node_name == "supervisor":
                    nxt = node_out.get("next", "")
                    add_log(f"→ routing to: {nxt}", "#00D4FF")
                    update_agent("supervisor", "🧠", "running", "#aaa", f"→ {nxt}")
                    progress_bar.progress(min(10 + step_num * 5, 25))

                elif node_name == "research":
                    status_text.markdown("<p style='color:#00D4FF;font-size:12px'>🔍 Searching the web…</p>", unsafe_allow_html=True)
                    update_agent("research", "🔍", "running", "#00D4FF", "searching web…")
                    add_log("🔍 Research agent running…", "#00D4FF")
                    progress_bar.progress(40)
                    time.sleep(0.3)
                    update_agent("research", "🔍", "done", "#00D4FF", "complete ✅")
                    add_log("✅ Research complete.", "#00FF9F")

                elif node_name == "rag":
                    status_text.markdown("<p style='color:#00FF9F;font-size:12px'>📄 Analysing documents…</p>", unsafe_allow_html=True)
                    update_agent("rag", "📄", "running", "#00FF9F", "loading FAISS index…")
                    add_log("📄 RAG agent running…", "#00FF9F")
                    progress_bar.progress(60)
                    time.sleep(0.3)
                    update_agent("rag", "📄", "done", "#00FF9F", "complete ✅")
                    add_log("✅ RAG retrieval complete.", "#00FF9F")

                elif node_name == "risk":
                    status_text.markdown("<p style='color:#FFB800;font-size:12px'>⚠️ Evaluating risks…</p>", unsafe_allow_html=True)
                    update_agent("risk", "⚠️", "running", "#FFB800", "evaluating risks…")
                    add_log("⚠️  Risk agent running…", "#FFB800")
                    progress_bar.progress(80)
                    time.sleep(0.3)
                    update_agent("risk", "⚠️", "done", "#FFB800", "complete ✅")
                    add_log("✅ Risk assessment complete.", "#00FF9F")

                elif node_name == "writer":
                    status_text.markdown("<p style='color:#FF6B6B;font-size:12px'>📝 Writing report…</p>", unsafe_allow_html=True)
                    update_agent("writer", "📝", "running", "#FF6B6B", "generating report…")
                    add_log("📝 Writer agent running…", "#FF6B6B")
                    progress_bar.progress(95)
                    time.sleep(0.3)
                    update_agent("writer", "📝", "done", "#FF6B6B", "complete ✅")
                    add_log("✅ Report complete.", "#00FF9F")
                    st.session_state.final_state = node_out

            update_agent("supervisor", "🧠", "done", "#aaa", "pipeline finished")
            progress_bar.progress(100)
            status_text.markdown("<p style='color:#00FF9F;font-size:12px'>✅ Analysis complete!</p>", unsafe_allow_html=True)
            add_log("━━━ Pipeline complete ━━━", "#555")

        except Exception as e:
            st.error(f"Pipeline error: {e}")

    # ── Report display ─────────────────────────────────────────────────────────
    if st.session_state.final_state:
        state = st.session_state.final_state
        st.divider()

        hdr1, hdr2, hdr3 = st.columns([4, 1, 1])
        with hdr1:
            st.markdown(f"### 📊 Investment Brief: {state.get('company', company)}")
        with hdr2:
            st.markdown("<div style='background:#00FF9F15;border:1px solid #00FF9F40;border-radius:8px;padding:8px;text-align:center'><div style='font-size:9px;color:#00FF9F'>VERDICT</div><div style='font-size:16px;color:#00FF9F;font-weight:700'>BUY</div></div>", unsafe_allow_html=True)
        with hdr3:
            st.markdown("<div style='background:#FFB80015;border:1px solid #FFB80040;border-radius:8px;padding:8px;text-align:center'><div style='font-size:9px;color:#FFB800'>CONFIDENCE</div><div style='font-size:16px;color:#FFB800;font-weight:700'>HIGH</div></div>", unsafe_allow_html=True)

        st.divider()

        tab1, tab2, tab3, tab4 = st.tabs(["📋 Full Report", "🔍 Web Research", "📄 Doc Analysis", "⚠️ Risk Assessment"])

        with tab1:
            report = state.get("final_result", "No report generated.")
            st.markdown(
                f"<div style='font-family:Lora,serif;line-height:1.9;color:#ddd;background:#0d0d0d;border:1px solid #1a1a1a;border-radius:12px;padding:28px'>{report}</div>",
                unsafe_allow_html=True,
            )
            st.download_button(
                label="⬇️ Download Report",
                data=report,
                file_name=f"{state.get('company','report')}_investment_brief.md",
                mime="text/markdown",
            )
        with tab2:
            st.markdown(f"<div style='font-size:13px;line-height:1.8;color:#ccc;background:#0d0d0d;border:1px solid #1a1a1a;border-radius:10px;padding:20px'>{state.get('research_result','No research data.')}</div>", unsafe_allow_html=True)
        with tab3:
            st.markdown(f"<div style='font-size:13px;line-height:1.8;color:#ccc;background:#0d0d0d;border:1px solid #1a1a1a;border-radius:10px;padding:20px'>{state.get('rag_result','No document analysis.')}</div>", unsafe_allow_html=True)
        with tab4:
            st.markdown(f"<div style='font-size:13px;line-height:1.8;color:#ccc;background:#0d0d0d;border:1px solid #1a1a1a;border-radius:10px;padding:20px'>{state.get('risk_result','No risk assessment.')}</div>", unsafe_allow_html=True)

    elif not analyze_btn:
        st.markdown("""
        <div style='text-align:center;padding:80px 20px;opacity:0.3'>
            <div style='font-size:56px;margin-bottom:16px'>📊</div>
            <div style='font-size:14px;color:#555;font-family:DM Mono,monospace'>
                Enter a company in the sidebar and click <strong style='color:#aaa'>ANALYZE →</strong><br>
                to run the full multi-agent pipeline
            </div>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.token:
    show_app()
else:
    show_auth()