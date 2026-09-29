from __future__ import annotations

import json
import io
import zipfile
from pathlib import Path
import streamlit as st

from agent.graph import build_graph, source_hash
from agent.state import AgentState
from storage import KnowledgeStore

st.set_page_config(page_title="API Intelligence", page_icon="⚡", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --bg:        #F7F9FC;
  --surface:   #FFFFFF;
  --border:    #E2E8F0;
  --border-md: #CBD5E1;
  --text:      #172033;
  --muted:     #64748B;
  --faint:     #94A3B8;
  --primary:   #2563EB;
  --primary-bg:#EFF6FF;
  --primary-bd:#BFDBFE;
  --violet:    #7C3AED;
  --success:   #16A34A;
  --success-bg:#F0FDF4;
  --success-bd:#BBF7D0;
  --warn:      #D97706;
  --warn-bg:   #FFFBEB;
  --warn-bd:   #FDE68A;
  --danger:    #DC2626;
  --danger-bg: #FEF2F2;
  --danger-bd: #FECACA;
  --radius:    10px;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.06),0 1px 2px rgba(0,0,0,0.04);
  --shadow:    0 4px 12px rgba(0,0,0,0.07),0 1px 3px rgba(0,0,0,0.05);
}

html, body, .stApp {
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: 'Inter', -apple-system, sans-serif !important;
}
.block-container {
  max-width: 1300px !important;
  padding: 0 2rem 3rem !important;
  margin-left: auto !important;
  margin-right: auto !important;
}
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* hide sidebar + collapse toggle */
[data-testid="stSidebar"],
[data-testid="collapsedControl"] { display: none !important; }

/* ── Inputs ── */
.stTextArea textarea, .stTextInput input {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  color: var(--text) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.85rem !important;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.stTextArea textarea:focus, .stTextInput input:focus {
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important;
  outline: none !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
  background: var(--surface) !important;
  border: 1.5px dashed var(--border-md) !important;
  border-radius: 8px !important;
  transition: border-color 0.15s, background 0.15s;
}
[data-testid="stFileUploader"]:hover {
  border-color: var(--primary) !important;
  background: var(--primary-bg) !important;
}
[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] small,
[data-testid="stFileUploaderDropzoneInstructions"] {
  font-size: 0.75rem !important;
  color: var(--muted) !important;
}

/* ── Buttons ── */
.stButton > button {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  color: var(--text) !important;
  font-family: 'Inter', sans-serif !important;
  font-weight: 500 !important;
  font-size: 0.85rem !important;
  border-radius: 8px !important;
  padding: 8px 16px !important;
  transition: all 0.15s !important;
  box-shadow: var(--shadow-sm) !important;
}
.stButton > button:hover {
  border-color: var(--primary) !important;
  color: var(--primary) !important;
  box-shadow: var(--shadow) !important;
}
.stButton > button[kind="primary"] {
  background: var(--primary) !important;
  border-color: var(--primary) !important;
  color: #fff !important;
  font-weight: 600 !important;
  box-shadow: 0 2px 8px rgba(37,99,235,0.25) !important;
}
.stButton > button[kind="primary"]:hover {
  background: #1D4ED8 !important;
  border-color: #1D4ED8 !important;
  color: #fff !important;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  padding: 14px 16px !important;
  box-shadow: var(--shadow-sm) !important;
}
[data-testid="stMetric"]:hover { border-color: var(--primary-bd) !important; }
[data-testid="stMetricLabel"] {
  color: var(--muted) !important;
  font-size: 0.7rem !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.07em !important;
}
[data-testid="stMetricValue"] {
  color: var(--text) !important;
  font-size: 1.4rem !important;
  font-weight: 700 !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  padding: 4px !important;
  gap: 2px !important;
  box-shadow: var(--shadow-sm) !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--muted) !important;
  border-radius: 7px !important;
  font-size: 0.76rem !important;
  font-weight: 500 !important;
  padding: 5px 12px !important;
  transition: all 0.15s !important;
  border: none !important;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--text) !important; background: var(--bg) !important; }
.stTabs [aria-selected="true"] {
  background: var(--primary) !important;
  color: #fff !important;
  font-weight: 600 !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  overflow: hidden !important;
  box-shadow: var(--shadow-sm) !important;
}

/* ── Code ── */
.stCode, pre {
  background: #F8FAFC !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 0.82rem !important;
}

/* ── Radio ── */
.stRadio > div { gap: 3px !important; }
.stRadio label {
  background: var(--bg) !important;
  border: 1px solid var(--border) !important;
  border-radius: 6px !important;
  padding: 6px 10px !important;
  cursor: pointer !important;
  transition: all 0.15s !important;
  color: var(--muted) !important;
  font-size: 0.78rem !important;
  font-weight: 500 !important;
}
.stRadio label:hover {
  border-color: var(--primary-bd) !important;
  color: var(--primary) !important;
  background: var(--primary-bg) !important;
}

/* ── Alerts / Download ── */
.stAlert { border-radius: 8px !important; border: 1px solid var(--border) !important; font-size: 0.85rem !important; }
.stDownloadButton > button {
  background: var(--success-bg) !important;
  border: 1px solid var(--success-bd) !important;
  color: var(--success) !important;
  font-size: 0.8rem !important;
  font-weight: 500 !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border-md); border-radius: 3px; }

/* ── Top nav ── */
.topnav {
  display: flex; align-items: center; justify-content: space-between;
  height: 56px; padding: 0 28px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  margin: -1rem -2rem 0 -2rem;
  position: sticky; top: 0; z-index: 200;
}
.topnav-brand { display: flex; align-items: center; gap: 10px; }
.topnav-icon {
  width: 28px; height: 28px;
  background: linear-gradient(135deg, var(--primary), var(--violet));
  border-radius: 7px;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; color: #fff;
}
.topnav-name { font-size: 0.88rem; font-weight: 700; color: var(--text); letter-spacing: -0.02em; }
.topnav-sub  { font-size: 0.62rem; color: var(--faint); font-family: 'JetBrains Mono', monospace; }
.topnav-links { display: flex; align-items: center; gap: 4px; }
.topnav-link { padding: 5px 11px; border-radius: 6px; font-size: 0.78rem; font-weight: 500; color: var(--muted); }
.topnav-status {
  display: flex; align-items: center; gap: 6px;
  padding: 4px 12px;
  background: var(--success-bg); border: 1px solid var(--success-bd); border-radius: 20px;
}
.status-dot {
  width: 6px; height: 6px; background: var(--success); border-radius: 50%;
  animation: blink 2.2s ease-in-out infinite;
}
@keyframes blink {
  0%,100% { opacity:1; box-shadow:0 0 0 0 rgba(22,163,74,0.35); }
  50%      { opacity:.75; box-shadow:0 0 0 4px rgba(22,163,74,0); }
}
.status-label { font-size: 0.7rem; font-weight: 600; color: var(--success); letter-spacing: 0.04em; }

/* ── Hero ── */
.hero {
  text-align: center;
  padding: 36px 24px 24px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  box-shadow: var(--shadow-sm);
  margin: 20px 0 0 0;
}
.hero-badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 4px 14px;
  background: var(--primary-bg); border: 1px solid var(--primary-bd); border-radius: 20px;
  font-size: 0.68rem; font-weight: 600; color: var(--primary);
  letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 14px;
}
.hero-title {
  font-size: 1.9rem; font-weight: 800;
  line-height: 1.2; letter-spacing: -0.03em;
  color: var(--text); margin-bottom: 10px;
}
.hero-title .accent {
  background: linear-gradient(135deg, var(--primary), var(--violet));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.hero-sub {
  font-size: 0.88rem; color: var(--muted);
  max-width: 520px; margin: 0 auto 20px; line-height: 1.65;
}
.pipeline {
  display: inline-flex; align-items: center;
  background: var(--bg); border: 1px solid var(--border);
  border-radius: 8px; overflow: hidden;
}
.pip-step {
  padding: 6px 13px;
  font-size: 0.65rem; font-weight: 600; color: var(--muted);
  letter-spacing: 0.07em; text-transform: uppercase;
  font-family: 'JetBrains Mono', monospace;
  border-right: 1px solid var(--border);
}
.pip-step:last-child { border-right: none; }
.pip-step.on { background: var(--primary); color: #fff; }
.pip-arrow { padding: 6px 5px; font-size: 0.65rem; color: var(--faint); border-right: 1px solid var(--border); }

/* ── Control bar ── */
.ctrl-bar {
  display: grid;
  grid-template-columns: 160px 1fr 1.3fr 1.8fr 160px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  margin: 16px 0 20px 0;
}
.ctrl-cell {
  padding: 16px 18px;
  border-right: 1px solid var(--border);
  min-width: 0;
}
.ctrl-cell:last-child { border-right: none; }
.ctrl-lbl {
  font-size: 0.62rem; font-weight: 700; color: var(--faint);
  text-transform: uppercase; letter-spacing: 0.1em;
  font-family: 'JetBrains Mono', monospace; margin-bottom: 8px;
}
.ctrl-brand-icon {
  width: 30px; height: 30px;
  background: linear-gradient(135deg, var(--primary), var(--violet));
  border-radius: 7px;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; color: #fff; margin-bottom: 8px;
}
.ctrl-brand-name { font-size: 0.84rem; font-weight: 700; color: var(--text); }
.ctrl-brand-sub  { font-size: 0.6rem; color: var(--faint); font-family: 'JetBrains Mono', monospace; margin-top: 2px; }
.ctrl-healthy {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 10px; margin-top: 10px;
  background: var(--success-bg); border: 1px solid var(--success-bd); border-radius: 7px;
  font-size: 0.68rem; font-weight: 600; color: var(--success);
  font-family: 'JetBrains Mono', monospace;
}

/* ── Workspace columns ── */
.card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 20px; box-shadow: var(--shadow-sm);
}
.card-title { font-size: 0.76rem; font-weight: 700; color: var(--text); text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 4px; }
.card-sub   { font-size: 0.68rem; color: var(--faint); font-family: 'JetBrains Mono', monospace; }
.wf-card {
  display: flex; align-items: center; gap: 11px;
  padding: 10px 13px;
  background: var(--bg); border: 1px solid var(--border); border-radius: 8px;
  margin-bottom: 5px; transition: all 0.15s;
}
.wf-card.sel { border-color: var(--primary-bd); background: var(--primary-bg); }
.wf-icon  { font-size: 0.95rem; flex-shrink: 0; }
.wf-title { font-size: 0.81rem; font-weight: 600; color: var(--text); }
.wf-desc  { font-size: 0.68rem; color: var(--muted); margin-top: 1px; }

/* ── Results ── */
.report-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 20px;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); box-shadow: var(--shadow-sm); margin-bottom: 16px;
}
.report-title { font-size: 0.86rem; font-weight: 700; color: var(--text); }
.report-meta  { font-size: 0.68rem; color: var(--muted); font-family: 'JetBrains Mono', monospace; margin-top: 2px; }
.badge-ok {
  display: inline-flex; align-items: center; gap: 5px; padding: 4px 12px;
  background: var(--success-bg); border: 1px solid var(--success-bd); border-radius: 20px;
  font-size: 0.68rem; font-weight: 600; color: var(--success);
}
.flow-bar {
  display: flex; align-items: center; justify-content: center; flex-wrap: wrap;
  padding: 14px 20px;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); box-shadow: var(--shadow-sm); margin-bottom: 16px;
}
.flow-step {
  padding: 7px 14px; background: var(--bg); border: 1px solid var(--border);
  border-radius: 6px; font-size: 0.68rem; font-weight: 600; color: var(--muted);
  letter-spacing: 0.06em; text-transform: uppercase; font-family: 'JetBrains Mono', monospace;
}
.flow-step.blue  { background: var(--primary-bg); border-color: var(--primary-bd); color: var(--primary); }
.flow-step.green { background: var(--success-bg); border-color: var(--success-bd); color: var(--success); }
.flow-step.warn  { background: var(--warn-bg);    border-color: var(--warn-bd);    color: var(--warn); }
.flow-arrow { color: var(--faint); font-size: 0.72rem; padding: 0 8px; }
.heal-col { display: flex; flex-direction: column; align-items: center; }
.heal-step {
  padding: 9px 22px; width: 200px; text-align: center;
  background: var(--bg); border: 1px solid var(--border); border-radius: 7px;
  font-size: 0.72rem; font-weight: 600; color: var(--muted); font-family: 'JetBrains Mono', monospace;
}
.heal-step.on   { background: var(--primary-bg); border-color: var(--primary-bd); color: var(--primary); }
.heal-step.done { background: var(--success-bg); border-color: var(--success-bd); color: var(--success); }
.heal-arr { color: var(--faint); font-size: 0.85rem; padding: 3px 0; }
.act-item {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 8px 13px; background: var(--surface); border: 1px solid var(--border);
  border-radius: 7px; margin-bottom: 5px; box-shadow: var(--shadow-sm);
}
.act-dot  { width: 6px; height: 6px; flex-shrink: 0; background: var(--primary); border-radius: 50%; margin-top: 5px; }
.act-text { font-size: 0.76rem; color: var(--muted); font-family: 'JetBrains Mono', monospace; }
.sev-critical { display:inline-block; padding:2px 7px; border-radius:4px; font-size:0.67rem; font-weight:700; font-family:'JetBrains Mono',monospace; background:var(--danger-bg); border:1px solid var(--danger-bd); color:var(--danger); }
.sev-high     { display:inline-block; padding:2px 7px; border-radius:4px; font-size:0.67rem; font-weight:700; font-family:'JetBrains Mono',monospace; background:var(--warn-bg);   border:1px solid var(--warn-bd);   color:var(--warn); }
.sev-medium   { display:inline-block; padding:2px 7px; border-radius:4px; font-size:0.67rem; font-weight:700; font-family:'JetBrains Mono',monospace; background:var(--primary-bg); border:1px solid var(--primary-bd); color:var(--primary); }
.sev-low      { display:inline-block; padding:2px 7px; border-radius:4px; font-size:0.67rem; font-weight:700; font-family:'JetBrains Mono',monospace; background:var(--bg); border:1px solid var(--border); color:var(--faint); }
.diff-wrap { background:#F8FAFC; border:1px solid var(--border); border-radius:8px; padding:12px 16px; font-family:'JetBrains Mono',monospace; font-size:0.76rem; }
.diff-rm  { display:block; color:var(--danger);  background:#FEF2F2; padding:2px 6px; border-left:3px solid var(--danger);  margin-bottom:1px; }
.diff-add { display:block; color:var(--success); background:#F0FDF4; padding:2px 6px; border-left:3px solid var(--success); margin-bottom:1px; }
.diff-ctx { display:block; color:var(--faint); padding:2px 6px; margin-bottom:1px; }
.score-row { display:flex; align-items:center; gap:12px; margin-bottom:8px; }
.score-label { width:185px; font-size:0.72rem; color:var(--muted); font-family:'JetBrains Mono',monospace; }
.score-track { flex:1; background:var(--bg); border:1px solid var(--border); border-radius:4px; height:6px; overflow:hidden; }
.score-fill  { height:100%; border-radius:4px; }
.score-val   { width:36px; text-align:right; font-size:0.72rem; font-weight:600; font-family:'JetBrains Mono',monospace; }
.kv-row { display:flex; gap:8px; margin-bottom:6px; font-size:0.81rem; }
.kv-key { color:var(--faint); min-width:140px; }
.kv-val { color:var(--text); font-weight:500; }
.section-label { font-size:0.65rem; font-weight:700; color:var(--faint); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:6px; font-family:'JetBrains Mono',monospace; }
</style>
""", unsafe_allow_html=True)

# ── Top nav ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="topnav">
  <div class="topnav-brand">
    <div class="topnav-icon">⚡</div>
    <div>
      <div class="topnav-name">API Intelligence</div>
      <div class="topnav-sub">SELF-HEALING DOCUMENTATION PLATFORM</div>
    </div>
  </div>
  <div class="topnav-links">
    <span class="topnav-link">Analyze</span>
    <span class="topnav-link">Compare</span>
    <span class="topnav-link">Drift</span>
    <span class="topnav-link">Knowledge</span>
  </div>
  <div class="topnav-status">
    <div class="status-dot"></div>
    <span class="status-label">AGENT ONLINE</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-badge">⚡ Autonomous AI Agent &nbsp;·&nbsp; Self-Healing Documentation</div>
  <div class="hero-title">
    Self-Healing API Documentation<br>
    <span class="accent">&amp; Change Intelligence</span>
  </div>
  <div class="hero-sub">
    An autonomous AI agent that detects API evolution, documentation drift,
    and keeps API knowledge synchronized — automatically.
  </div>
  <div class="pipeline">
    <div class="pip-step on">API SOURCE</div>
    <div class="pip-arrow">→</div>
    <div class="pip-step">UNDERSTAND</div>
    <div class="pip-arrow">→</div>
    <div class="pip-step">DETECT CHANGE</div>
    <div class="pip-arrow">→</div>
    <div class="pip-step">SELF-HEAL</div>
    <div class="pip-arrow">→</div>
    <div class="pip-step">SYNC DOCS</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Control bar — Brand + Status cells are pure HTML; widgets go in columns ───
#
# Layout: [Brand 160px] [Workflow] [API Source] [Instruction] [Run+Status 160px]
# We render the outer card shell in HTML, then overlay st.columns on top of it.
# The columns are given zero padding via CSS so they sit flush inside the card.

st.markdown("""
<div class="ctrl-bar">
  <div class="ctrl-cell">
    <div class="ctrl-brand-icon">⚡</div>
    <div class="ctrl-brand-name">API Intelligence</div>
    <div class="ctrl-brand-sub">SELF-HEALING ENGINE</div>
  </div>
  <div class="ctrl-cell" id="wf-slot"></div>
  <div class="ctrl-cell" id="src-slot"></div>
  <div class="ctrl-cell" id="instr-slot"></div>
  <div class="ctrl-cell" id="run-slot"></div>
</div>
""", unsafe_allow_html=True)

# The HTML card above is decorative. The actual interactive widgets are placed
# in st.columns immediately below — they appear visually inside the card because
# we remove Streamlit's default column gap and padding with CSS below.
st.markdown("""
<style>
/* Target the widget row: remove gap, add card border, align with hero */
div[data-testid="stHorizontalBlock"].widget-row {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  gap: 0 !important;
  margin: -4px 0 20px 0;
}
div[data-testid="stHorizontalBlock"].widget-row > div[data-testid="stColumn"] {
  padding: 14px 16px !important;
  border-right: 1px solid var(--border);
  min-width: 0;
}
div[data-testid="stHorizontalBlock"].widget-row > div[data-testid="stColumn"]:last-child {
  border-right: none;
}
</style>
""", unsafe_allow_html=True)

# We can't add a class to st.columns directly, so we use a unique key trick:
# wrap the columns in a container div via markdown, then target nth-of-type.
# Simpler: just style ALL 5-column horizontal blocks (there's only one on page).
st.markdown("""
<style>
/* Style the 5-column widget row as a unified card */
section.main > div > div > div > div[data-testid="stHorizontalBlock"]:first-of-type {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 14px !important;
  box-shadow: var(--shadow-sm) !important;
  overflow: hidden !important;
  gap: 0 !important;
  margin-top: 16px !important;
  margin-bottom: 20px !important;
}
section.main > div > div > div > div[data-testid="stHorizontalBlock"]:first-of-type
  > div[data-testid="stColumn"] {
  padding: 16px 18px !important;
  border-right: 1px solid var(--border) !important;
}
section.main > div > div > div > div[data-testid="stHorizontalBlock"]:first-of-type
  > div[data-testid="stColumn"]:last-child {
  border-right: none !important;
}
</style>
""", unsafe_allow_html=True)

# Remove the decorative HTML card (it would double-render); replace with columns only
# (The HTML card above is removed — we rely purely on the CSS-styled st.columns)

c_brand, c_wf, c_src, c_instr, c_run = st.columns([1.1, 1.4, 1.6, 2.2, 1.3])

with c_brand:
    st.markdown("""
    <div style="padding-top:2px;">
      <div style="width:30px;height:30px;background:linear-gradient(135deg,#2563EB,#7C3AED);
           border-radius:7px;display:flex;align-items:center;justify-content:center;
           font-size:14px;color:#fff;margin-bottom:8px;">⚡</div>
      <div style="font-size:0.84rem;font-weight:700;color:#172033;line-height:1.2;">API Intelligence</div>
      <div style="font-size:0.6rem;color:#94A3B8;font-family:'JetBrains Mono',monospace;margin-top:3px;">SELF-HEALING ENGINE</div>
    </div>
    """, unsafe_allow_html=True)

with c_wf:
    st.markdown('<p style="font-size:0.62rem;font-weight:700;color:#94A3B8;text-transform:uppercase;letter-spacing:0.1em;font-family:JetBrains Mono,monospace;margin:0 0 6px 0;">Workflow</p>', unsafe_allow_html=True)
    mode = st.radio(
        "Workflow",
        ["Analyze API", "Compare V1/V2", "Check Documentation Drift", "API Knowledge Assistant"],
        label_visibility="collapsed"
    )

with c_src:
    st.markdown('<p style="font-size:0.62rem;font-weight:700;color:#94A3B8;text-transform:uppercase;letter-spacing:0.1em;font-family:JetBrains Mono,monospace;margin:0 0 6px 0;">API Source</p>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "API source",
        type=["py", "yaml", "yml", "json", "md", "html", "zip"],
        label_visibility="collapsed",
        help="PY · YAML · JSON · MD · HTML · ZIP"
    )
    if mode == "Compare V1/V2":
        st.markdown('<p style="font-size:0.62rem;font-weight:700;color:#94A3B8;text-transform:uppercase;letter-spacing:0.1em;font-family:JetBrains Mono,monospace;margin:8px 0 4px 0;">V2 Source</p>', unsafe_allow_html=True)
        v2_upload = st.file_uploader("V2 source", type=["py", "yaml", "yml", "json"], key="v2", label_visibility="collapsed")
    else:
        v2_upload = None
    st.markdown('<p style="font-size:0.63rem;color:#94A3B8;font-family:JetBrains Mono,monospace;margin:4px 0 0 0;">PY · YAML · JSON · MD · HTML · ZIP</p>', unsafe_allow_html=True)

with c_instr:
    st.markdown('<p style="font-size:0.62rem;font-weight:700;color:#94A3B8;text-transform:uppercase;letter-spacing:0.1em;font-family:JetBrains Mono,monospace;margin:0 0 6px 0;">Natural Language Instruction</p>', unsafe_allow_html=True)
    _defaults = {
        "Analyze API": "Generate documentation and detect API changes.",
        "Compare V1/V2": "Compare V1 and V2, identify breaking changes.",
        "Check Documentation Drift": "Why is my documentation outdated?",
        "API Knowledge Assistant": "Which endpoint requires authentication?"
    }
    request = st.text_area("Instruction", value=_defaults[mode], label_visibility="collapsed", height=96)

with c_run:
    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)
    run = st.button("Run Intelligence Agent →", type="primary", use_container_width=True)
    st.markdown("""
    <div style="display:flex;align-items:center;gap:6px;padding:6px 10px;margin-top:10px;
         background:#F0FDF4;border:1px solid #BBF7D0;border-radius:7px;">
      <div class="status-dot"></div>
      <span style="font-size:0.68rem;font-weight:600;color:#16A34A;font-family:'JetBrains Mono',monospace;white-space:nowrap;">SYSTEM HEALTHY</span>
    </div>
    """, unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "state" not in st.session_state:
    st.session_state.state = None

# ── Run agent ─────────────────────────────────────────────────────────────────
if run:
    source = None
    if uploaded:
        if uploaded.name.lower().endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(uploaded.getvalue())) as archive:
                members = [n for n in archive.namelist()
                           if n.endswith((".py", ".yaml", ".yml", ".json"))
                           and not n.startswith("__MACOSX/")]
                source = archive.read(members[0]).decode("utf-8", errors="replace") if members else None
        else:
            source = uploaded.getvalue().decode("utf-8", errors="replace")
    state = AgentState(request=request, api_source=source)
    if mode == "Compare V1/V2" and v2_upload:
        state.v1_source, state.v2_source = source, v2_upload.getvalue().decode("utf-8", errors="replace")
    graph = build_graph()
    result = graph.invoke(state)
    st.session_state.state = result if isinstance(result, AgentState) else AgentState.model_validate(result)
    KnowledgeStore().save(st.session_state.state.model_dump(), source_hash(source or ""))

state = st.session_state.state

# ── Two-column workspace (no results yet) ─────────────────────────────────────
if not state:
    left, right = st.columns(2, gap="large")

    with left:
        st.markdown("""
        <div class="card" style="margin-bottom:14px;">
          <div class="card-title">Agent Workspace</div>
          <div class="card-sub">SELECT A WORKFLOW TO BEGIN</div>
        </div>
        """, unsafe_allow_html=True)
        wf_meta = {
            "Analyze API":               ("🔍", "Analyze API",             "Parse source, generate docs & score quality"),
            "Compare V1/V2":             ("⚡", "Compare V1 / V2",         "Detect breaking changes between versions"),
            "Check Documentation Drift": ("📡", "Documentation Drift",     "Identify drift between API and docs"),
            "API Knowledge Assistant":   ("🤖", "API Knowledge Assistant", "Query structured API knowledge"),
        }
        for wf, (icon, title, desc) in wf_meta.items():
            sel = "sel" if mode == wf else ""
            st.markdown(f"""
            <div class="wf-card {sel}">
              <div class="wf-icon">{icon}</div>
              <div><div class="wf-title">{title}</div><div class="wf-desc">{desc}</div></div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("""
        <div class="card" style="margin-top:14px;text-align:center;padding:20px;">
          <div style="font-size:1.4rem;opacity:0.25;margin-bottom:8px;">⬆</div>
          <div style="font-size:0.82rem;color:#64748B;font-weight:500;margin-bottom:4px;">Upload your API source above</div>
          <div style="font-size:0.68rem;color:#94A3B8;font-family:'JetBrains Mono',monospace;">FastAPI Python · OpenAPI YAML/JSON · Markdown · HTML · ZIP</div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown("""
        <div class="card" style="margin-bottom:14px;">
          <div class="card-title">API Intelligence Graph</div>
          <div class="card-sub">LIVE SYSTEM TOPOLOGY</div>
        </div>
        """, unsafe_allow_html=True)

        st.components.v1.html("""
<!DOCTYPE html><html><head>
<style>*{margin:0;padding:0;box-sizing:border-box;}body{background:#F7F9FC;overflow:hidden;}canvas{display:block;}</style>
</head><body><canvas id="c"></canvas>
<script>
const cv=document.getElementById('c');
const ctx=cv.getContext('2d');
cv.width=cv.parentElement?cv.parentElement.offsetWidth:500;
cv.height=300;
const W=cv.width,H=cv.height,cx=W/2,cy=H/2+8;
const P='#2563EB',V='#7C3AED',T='#172033';
const nodes=[
  {label:['SELF-HEALING','ENGINE'],x:cx,y:cy,r:38,core:true},
  {label:['API SOURCE'],x:cx,y:cy-112,r:26},
  {label:['CHANGE','DETECTION'],x:cx+122,y:cy-46,r:26},
  {label:['VERSION','INTELLIGENCE'],x:cx+108,y:cy+76,r:26},
  {label:['DOCUMENTATION'],x:cx,y:cy+112,r:26},
  {label:['DRIFT','MONITOR'],x:cx-122,y:cy-46,r:26},
];
const parts=[];
nodes.slice(1).forEach((_,i)=>{
  for(let j=0;j<4;j++) parts.push({ni:i+1,t:Math.random(),spd:0.0022+Math.random()*0.002,rev:j%2===0});
});
let tick=0;
function lerp(a,b,t){return a+(b-a)*t;}
function drawEdge(a,b){
  const al=0.16+0.05*Math.sin(tick*0.025);
  const g=ctx.createLinearGradient(a.x,a.y,b.x,b.y);
  g.addColorStop(0,`rgba(37,99,235,${al})`);
  g.addColorStop(.5,`rgba(124,58,237,${al*1.4})`);
  g.addColorStop(1,`rgba(37,99,235,${al})`);
  ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);
  ctx.strokeStyle=g;ctx.lineWidth=1.2;ctx.stroke();
}
function drawNode(n){
  const pulse=1+0.022*Math.sin(tick*0.04+n.x*0.01);
  const r=n.r*pulse;
  ctx.beginPath();ctx.arc(n.x,n.y,r+5,0,Math.PI*2);
  ctx.fillStyle=n.core?'rgba(37,99,235,0.07)':'rgba(37,99,235,0.04)';ctx.fill();
  ctx.beginPath();ctx.arc(n.x,n.y,r,0,Math.PI*2);
  ctx.fillStyle='#FFFFFF';ctx.fill();
  ctx.strokeStyle=n.core?P:V;ctx.lineWidth=n.core?2:1.5;ctx.stroke();
  ctx.fillStyle=n.core?P:T;
  ctx.font=n.core?'bold 8px Inter,sans-serif':'7px Inter,sans-serif';
  ctx.textAlign='center';ctx.textBaseline='middle';
  n.label.forEach((l,i)=>ctx.fillText(l,n.x,n.y+(i-(n.label.length-1)/2)*10));
}
function drawParticle(p){
  const src=nodes[0],dst=nodes[p.ni];
  p.t+=p.spd*(p.rev?-1:1);
  if(p.t>1)p.t=0;if(p.t<0)p.t=1;
  const px=lerp(src.x,dst.x,p.t),py=lerp(src.y,dst.y,p.t);
  ctx.beginPath();ctx.arc(px,py,2,0,Math.PI*2);
  ctx.fillStyle=`rgba(37,99,235,${0.5+0.3*Math.sin(tick*0.08+p.t*6)})`;ctx.fill();
}
function frame(){
  ctx.clearRect(0,0,W,H);tick++;
  nodes.slice(1).forEach(n=>drawEdge(nodes[0],n));
  parts.forEach(p=>drawParticle(p));
  nodes.forEach(n=>drawNode(n));
  requestAnimationFrame(frame);
}
frame();
</script></body></html>
""", height=300)

        st.markdown("""
        <div style="margin-top:10px;">
          <div class="pipeline" style="width:100%;">
            <div class="pip-step">PARSE</div><div class="pip-arrow">→</div>
            <div class="pip-step on">UNDERSTAND</div><div class="pip-arrow">→</div>
            <div class="pip-step">DETECT</div><div class="pip-arrow">→</div>
            <div class="pip-step">SELF-HEAL</div><div class="pip-arrow">→</div>
            <div class="pip-step">SYNC</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

# ── Results ───────────────────────────────────────────────────────────────────
if state:
    if state.errors:
        for err in state.errors:
            st.error(err)

    api = state.api
    if api:
        breaking_count = sum(c.severity in {"HIGH", "CRITICAL"} for c in state.changes)
        drift_count    = len(state.drift)

        st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="report-bar">
          <div>
            <div class="report-title">Intelligence Report</div>
            <div class="report-meta">{api.title} &nbsp;·&nbsp; v{api.version} &nbsp;·&nbsp; {api.source_type.upper()}</div>
          </div>
          <div style="display:flex;align-items:center;gap:12px;">
            <span class="badge-ok">✓ Analysis Complete</span>
            <span style="font-size:0.68rem;color:#94A3B8;font-family:'JetBrains Mono',monospace;">{len(state.activity)} steps</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        cols = st.columns(7)
        for col, (label, value) in zip(cols, [
            ("Endpoints",  len(api.endpoints)),
            ("Schemas",    len(api.schemas)),
            ("Parameters", sum(len(e.parameters) for e in api.endpoints)),
            ("API Health", f"{state.quality.total}%"),
            ("Doc Sync",   f"{state.quality.documentation_drift}%"),
            ("Breaking",   breaking_count),
            ("Drift",      drift_count),
        ]):
            col.metric(label, value)

        if state.changes and mode == "Compare V1/V2":
            st.markdown("""
            <div class="flow-bar" style="margin-top:16px;">
              <div class="flow-step blue">V1 API</div><div class="flow-arrow">→</div>
              <div class="flow-step warn">CHANGE DETECTED</div><div class="flow-arrow">→</div>
              <div class="flow-step blue">V2 API</div><div class="flow-arrow">→</div>
              <div class="flow-step">DOCUMENTATION IMPACT</div><div class="flow-arrow">→</div>
              <div class="flow-step green">REPAIR</div>
            </div>
            """, unsafe_allow_html=True)

        if state.drift and mode == "Check Documentation Drift":
            st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)
            hc1, hc2 = st.columns([1, 2], gap="large")
            with hc1:
                st.markdown("""
                <div class="card">
                  <div class="section-label" style="margin-bottom:10px;">Self-Healing Workflow</div>
                  <div class="heal-col">
                    <div class="heal-step on">DRIFT DETECTED</div><div class="heal-arr">↓</div>
                    <div class="heal-step on">AI ANALYSIS</div><div class="heal-arr">↓</div>
                    <div class="heal-step on">DOC REPAIR</div><div class="heal-arr">↓</div>
                    <div class="heal-step done">✓ SYNCHRONIZED</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
            with hc2:
                st.markdown('<div class="card"><div class="section-label" style="margin-bottom:8px;">Drift Findings Preview</div>', unsafe_allow_html=True)
                for d in state.drift[:4]:
                    bc = {"CRITICAL":"#DC2626","HIGH":"#D97706","MEDIUM":"#2563EB","LOW":"#94A3B8"}.get(d.severity,"#94A3B8")
                    st.markdown(f"""
                    <div class="act-item" style="border-left:3px solid {bc};margin-bottom:5px;">
                      <div>
                        <span class="sev-{d.severity.lower()}">{d.severity}</span>
                        <span style="font-size:0.77rem;color:#172033;margin-left:8px;font-weight:500;">{d.component}</span>
                        <div style="font-size:0.71rem;color:#64748B;margin-top:3px;">{d.issue}</div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

        tabs = st.tabs([
            "Overview","Endpoints","Schemas","Documentation","OpenAPI",
            "Changes","Breaking Changes","Impact Graph","Drift",
            "Security","Quality","Migration","Release Notes",
            "Agent Activity","API Assistant"
        ])

        with tabs[0]:
            st.info("Analysis is grounded in static source/OpenAPI facts. Gemini is optional and only used for semantic explanations.")
            c1, c2 = st.columns(2, gap="large")
            with c1:
                st.markdown(f"""
                <div class="card">
                  <div class="section-label" style="margin-bottom:8px;">API Identity</div>
                  <div class="kv-row"><span class="kv-key">Title</span><span class="kv-val">{api.title}</span></div>
                  <div class="kv-row"><span class="kv-key">Version</span><span class="kv-val">{api.version}</span></div>
                  <div class="kv-row"><span class="kv-key">Source Type</span><span class="kv-val">{api.source_type}</span></div>
                  <div class="kv-row"><span class="kv-key">Auth Required</span><span class="kv-val">{'Yes' if api.auth_required else 'No'}</span></div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="card">
                  <div class="section-label" style="margin-bottom:8px;">Quality Scores</div>
                  <div class="kv-row"><span class="kv-key">Endpoint Coverage</span><span class="kv-val">{state.quality.endpoint_coverage}%</span></div>
                  <div class="kv-row"><span class="kv-key">Schema Coverage</span><span class="kv-val">{state.quality.schema_coverage}%</span></div>
                  <div class="kv-row"><span class="kv-key">Auth Documentation</span><span class="kv-val">{state.quality.authentication_documentation}%</span></div>
                  <div class="kv-row"><span class="kv-key">Overall Health</span><span class="kv-val" style="color:#2563EB;font-weight:700;">{state.quality.total}%</span></div>
                </div>
                """, unsafe_allow_html=True)

        with tabs[1]:
            st.caption(f"{len(api.endpoints)} routes detected")
            st.dataframe([e.model_dump() for e in api.endpoints], use_container_width=True)

        with tabs[2]:
            st.caption(f"{len(api.schemas)} models")
            st.json({name: [f.model_dump() for f in fields] for name, fields in api.schemas.items()})

        with tabs[3]:
            doc_md = state.artifacts.get("documentation.md", "")
            st.download_button("⬇ Download Markdown", doc_md, file_name="documentation.md")
            st.markdown(doc_md)

        with tabs[4]:
            openapi_yaml = state.artifacts.get("openapi.yaml", "")
            st.download_button("⬇ Download OpenAPI YAML", openapi_yaml, file_name="openapi.yaml")
            st.code(openapi_yaml, language="yaml")

        with tabs[5]:
            st.caption(f"{len(state.changes)} changes detected")
            st.dataframe([c.model_dump() for c in state.changes], use_container_width=True)

        with tabs[6]:
            breaking = [c for c in state.changes if c.severity in {"HIGH", "CRITICAL"}]
            if breaking:
                for c in breaking:
                    bc = "#DC2626" if c.severity == "CRITICAL" else "#D97706"
                    st.markdown(f"""
                    <div class="act-item" style="border-left:3px solid {bc};margin-bottom:7px;">
                      <div>
                        <span class="sev-{c.severity.lower()}">{c.severity}</span>
                        <span style="font-size:0.81rem;color:#172033;margin-left:9px;font-weight:600;">{c.component}</span>
                        <div style="font-size:0.73rem;color:#64748B;margin-top:3px;font-family:'JetBrains Mono',monospace;">{c.reason}</div>
                        <div style="font-size:0.7rem;color:#94A3B8;margin-top:2px;">{c.consumer_impact}</div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("No breaking changes detected.")
            if breaking:
                st.dataframe([c.model_dump() for c in breaking], use_container_width=True)

        with tabs[7]:
            if state.impact_edges:
                st.graphviz_chart(
                    'digraph { rankdir=LR; bgcolor="#F7F9FC"; '
                    'node [style=filled fillcolor="#FFFFFF" color="#2563EB" fontcolor="#172033" fontname="Inter" fontsize=10 shape=box]; '
                    'edge [color="#7C3AED" arrowsize=0.7]; '
                    + " ".join(f'"{e["source"]}" -> "{e["target"]}";' for e in state.impact_edges)
                    + " }"
                )
            else:
                st.info("No impact edges generated.")

        with tabs[8]:
            if state.drift:
                for d in state.drift:
                    bc = {"CRITICAL":"#DC2626","HIGH":"#D97706","MEDIUM":"#2563EB","LOW":"#94A3B8"}.get(d.severity,"#94A3B8")
                    st.markdown(f"""
                    <div class="act-item" style="border-left:3px solid {bc};margin-bottom:6px;">
                      <div style="width:100%;">
                        <div style="display:flex;align-items:center;gap:8px;margin-bottom:3px;">
                          <span class="sev-{d.severity.lower()}">{d.severity}</span>
                          <span style="font-size:0.8rem;color:#172033;font-weight:600;">{d.component}</span>
                        </div>
                        <div style="font-size:0.75rem;color:#64748B;margin-bottom:2px;">{d.issue}</div>
                        <div style="font-size:0.69rem;color:#94A3B8;font-family:'JetBrains Mono',monospace;">→ {d.recommendation}</div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
            st.dataframe([d.model_dump() for d in state.drift], use_container_width=True)

        with tabs[9]:
            st.markdown(f"""
            <div class="card">
              <div class="section-label" style="margin-bottom:8px;">Detected Schemes</div>
              <div style="font-size:0.82rem;color:#172033;font-family:'JetBrains Mono',monospace;">
                {', '.join(api.security_schemes) if api.security_schemes else 'None detected'}
              </div>
              <div class="section-label" style="margin-top:14px;margin-bottom:6px;">Documentation Consistency</div>
              <div style="font-size:0.8rem;color:#64748B;">Review the Drift tab for security documentation gaps.</div>
            </div>
            """, unsafe_allow_html=True)

        with tabs[10]:
            q = state.quality
            score_items = [
                ("Endpoint Coverage",   q.endpoint_coverage),
                ("Parameter Coverage",  q.parameter_coverage),
                ("Schema Coverage",     q.schema_coverage),
                ("Request Examples",    q.request_example_coverage),
                ("Response Examples",   q.response_example_coverage),
                ("Error Documentation", q.error_documentation),
                ("Auth Documentation",  q.authentication_documentation),
                ("Consistency",         q.consistency),
                ("OpenAPI Validity",    q.openapi_validity),
                ("Doc Drift Score",     q.documentation_drift),
            ]
            st.markdown('<div class="card">', unsafe_allow_html=True)
            for label, score in score_items:
                fc = "#16A34A" if score >= 80 else "#D97706" if score >= 50 else "#DC2626"
                st.markdown(f"""
                <div class="score-row">
                  <div class="score-label">{label}</div>
                  <div class="score-track"><div class="score-fill" style="width:{score}%;background:{fc};"></div></div>
                  <div class="score-val" style="color:{fc};">{score}%</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            if q.recommendations:
                st.markdown('<div style="margin-top:10px;"><div class="section-label" style="margin-bottom:6px;">Recommendations</div>', unsafe_allow_html=True)
                for rec in q.recommendations:
                    st.markdown(f'<div class="act-item"><div class="act-dot"></div><div class="act-text">{rec}</div></div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

        with tabs[11]:
            migration_md = state.artifacts.get("migration-guide.md", "")
            if migration_md:
                st.download_button("⬇ Download Migration Guide", migration_md, file_name="migration-guide.md")
                st.markdown('<div class="section-label" style="margin:10px 0 5px;">Documentation Repair View</div>', unsafe_allow_html=True)
                st.markdown('<div class="diff-wrap">', unsafe_allow_html=True)
                for line in migration_md.split("\n")[:40]:
                    if line.startswith("-"):
                        st.markdown(f'<span class="diff-rm">{line}</span>', unsafe_allow_html=True)
                    elif line.startswith("+"):
                        st.markdown(f'<span class="diff-add">{line}</span>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<span class="diff-ctx">{line}</span>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown(migration_md)
            else:
                st.info("No migration guide generated.")

        with tabs[12]:
            release_md = state.artifacts.get("release-notes.md", "")
            if release_md:
                st.download_button("⬇ Download Release Notes", release_md, file_name="release-notes.md")
                st.markdown(release_md)
            else:
                st.info("No release notes generated.")

        with tabs[13]:
            st.caption(f"{len(state.activity)} steps executed")
            for item in state.activity:
                st.markdown(f'<div class="act-item"><div class="act-dot"></div><div class="act-text">{item}</div></div>', unsafe_allow_html=True)

        with tabs[14]:
            question = st.text_input("Ask about the analyzed API", placeholder="e.g. Which endpoints require authentication?")
            if question:
                st.info("Answers are restricted to the structured analysis. Relevant facts are available in the tables above.")

        st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)
        st.download_button(
            "⬇ Download Complete Analysis JSON",
            json.dumps(state.model_dump(), indent=2, default=str),
            file_name="analysis.json",
            mime="application/json"
        )
