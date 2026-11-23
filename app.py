import os
import time
import json
import datetime
import requests
import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader

# Load environment variables
load_dotenv()

# Streamlit Page Configuration
st.set_page_config(
    page_title="AI Study Buddy | Smart Revision Platform",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# LOCAL HISTORY PERSISTENCE
# ---------------------------------------------------------
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "study_history.json")

def load_local_history():
    """Loads study history from local JSON file."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            return []
    return []

def save_local_history(history_list):
    """Saves study history to local JSON file."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history_list, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Failed to save history locally: {e}")

# ---------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"
if "history" not in st.session_state:
    st.session_state["history"] = load_local_history()
if "current_notes" not in st.session_state:
    st.session_state["current_notes"] = ""
if "pasted_notes" not in st.session_state:
    st.session_state["pasted_notes"] = ""
if "pdf_extracted_notes" not in st.session_state:
    st.session_state["pdf_extracted_notes"] = ""
if "revision_pack" not in st.session_state:
    st.session_state["revision_pack"] = ""
if "model_used" not in st.session_state:
    st.session_state["model_used"] = ""
if "is_generating" not in st.session_state:
    st.session_state["is_generating"] = False
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "🏠 Home"
if "pending_page" not in st.session_state:
    st.session_state["pending_page"] = None
if "pending_input_mode" not in st.session_state:
    st.session_state["pending_input_mode"] = None
if "input_method_choice" not in st.session_state:
    st.session_state["input_method_choice"] = "📝 Paste Notes"

# Process any pending navigation requests BEFORE widgets are instantiated!
if st.session_state["pending_page"] is not None:
    target_page = st.session_state["pending_page"]
    st.session_state["current_page"] = target_page
    st.session_state["sidebar_nav_radio"] = target_page
    st.session_state["pending_page"] = None

if st.session_state["pending_input_mode"] is not None:
    target_mode = st.session_state["pending_input_mode"]
    st.session_state["input_method_choice"] = target_mode
    st.session_state["input_mode_radio_key"] = target_mode
    st.session_state["pending_input_mode"] = None

# ---------------------------------------------------------
# NAVIGATION HELPER
# ---------------------------------------------------------
def navigate_to(page_name: str, input_mode: str = None):
    """Schedules navigation to a target page and triggers a rerun without touching instantiated widgets."""
    st.session_state["pending_page"] = page_name
    if input_mode:
        st.session_state["pending_input_mode"] = input_mode
    st.rerun()

# ---------------------------------------------------------
# THEME & CUSTOM CSS (Modern Glassmorphism & SaaS Design)
# ---------------------------------------------------------
is_dark = st.session_state["theme"] == "dark"

bg_color = "#0B0F19" if is_dark else "#F8FAFC"
card_bg = "rgba(18, 24, 39, 0.75)" if is_dark else "rgba(255, 255, 255, 0.9)"
border_color = "rgba(255, 255, 255, 0.08)" if is_dark else "rgba(226, 232, 240, 0.8)"
text_main = "#F9FAFB" if is_dark else "#0F172A"
text_sub = "#94A3B8" if is_dark else "#475569"
input_bg = "rgba(15, 23, 42, 0.6)" if is_dark else "#FFFFFF"
card_shadow = "0 8px 32px 0 rgba(0, 0, 0, 0.4)" if is_dark else "0 8px 30px 0 rgba(0, 0, 0, 0.06)"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    .stApp {{
        background-color: {bg_color};
        color: {text_main};
    }}

    /* Hero Section */
    .hero-container {{
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(139, 92, 246, 0.12) 50%, rgba(59, 130, 246, 0.08) 100%);
        border: 1px solid {border_color};
        border-radius: 20px;
        padding: 2.2rem 2.5rem;
        margin-bottom: 2rem;
        backdrop-filter: blur(16px);
        box-shadow: {card_shadow};
        position: relative;
        overflow: hidden;
    }}
    .hero-container::before {{
        content: "";
        position: absolute;
        top: -50px;
        right: -50px;
        width: 200px;
        height: 200px;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.3) 0%, rgba(139, 92, 246, 0) 70%);
        border-radius: 50%;
        pointer-events: none;
    }}
    .hero-title {{
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #818CF8 0%, #C084FC 50%, #60A5FA 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.4rem;
        letter-spacing: -0.02em;
    }}
    .hero-subtitle {{
        font-size: 1.1rem;
        color: {text_sub};
        font-weight: 500;
        max-width: 650px;
        line-height: 1.6;
    }}

    /* Glass Cards */
    .glass-card {{
        background: {card_bg};
        border: 1px solid {border_color};
        border-radius: 16px;
        padding: 1.5rem;
        backdrop-filter: blur(14px);
        box-shadow: {card_shadow};
        transition: transform 0.2s ease, border-color 0.2s ease;
        margin-bottom: 1.2rem;
    }}
    .glass-card:hover {{
        border-color: rgba(99, 102, 241, 0.35);
        transform: translateY(-2px);
    }}

    /* Stat Card */
    .stat-card {{
        background: {card_bg};
        border: 1px solid {border_color};
        border-radius: 16px;
        padding: 1.4rem;
        backdrop-filter: blur(12px);
        box-shadow: {card_shadow};
        text-align: left;
    }}
    .stat-label {{
        color: {text_sub};
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.3rem;
    }}
    .stat-value {{
        font-size: 1.9rem;
        font-weight: 800;
        color: {text_main};
        letter-spacing: -0.02em;
    }}

    /* Section Cards for AI Output */
    .output-card {{
        background: {card_bg};
        border: 1px solid {border_color};
        border-radius: 16px;
        padding: 1.8rem;
        backdrop-filter: blur(16px);
        box-shadow: {card_shadow};
        margin-bottom: 1.5rem;
    }}
    .output-header {{
        display: flex;
        align-items: center;
        gap: 0.6rem;
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid {border_color};
    }}
    .output-header.summary {{ color: #60A5FA; }}
    .output-header.mcq {{ color: #A78BFA; }}
    .output-header.terms {{ color: #34D399; }}

    /* Badges */
    .model-badge {{
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.35rem 0.8rem;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        background: rgba(99, 102, 241, 0.15);
        border: 1px solid rgba(99, 102, 241, 0.3);
        color: #A5B4FC;
    }}
    .meta-badge {{
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        padding: 0.25rem 0.65rem;
        border-radius: 8px;
        font-size: 0.8rem;
        font-weight: 600;
        background: {input_bg};
        border: 1px solid {border_color};
        color: {text_sub};
        margin-right: 0.4rem;
    }}

    /* Streamlit Input Overrides */
    div[data-baseweb="textarea"] textarea {{
        background-color: {input_bg} !important;
        color: {text_main} !important;
        border: 1px solid {border_color} !important;
        border-radius: 12px !important;
        font-family: inherit !important;
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
    }}
    div[data-baseweb="textarea"] textarea:focus {{
        border-color: #6366F1 !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.25) !important;
    }}

    /* Primary Generate Button Styling */
    div.stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #3B82F6 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.8rem !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.01em !important;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4) !important;
        transition: all 0.25s ease !important;
    }}
    div.stButton > button[kind="primary"]:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 28px rgba(99, 102, 241, 0.6) !important;
    }}

    /* Secondary Buttons */
    div.stButton > button:not([kind="primary"]) {{
        background-color: {input_bg} !important;
        color: {text_main} !important;
        border: 1px solid {border_color} !important;
        border-radius: 10px !important;
        transition: all 0.2s ease !important;
    }}
    div.stButton > button:not([kind="primary"]):hover {{
        border-color: #6366F1 !important;
        color: #818CF8 !important;
    }}

    /* Sidebar Logo */
    .sidebar-logo {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.5rem 0 1.2rem 0;
        border-bottom: 1px solid {border_color};
        margin-bottom: 1.2rem;
    }}
    .logo-icon {{
        width: 38px;
        height: 38px;
        border-radius: 10px;
        background: linear-gradient(135deg, #6366F1, #8B5CF6);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.25rem;
        box-shadow: 0 0 15px rgba(99, 102, 241, 0.5);
    }}
    .logo-text {{
        font-size: 1.2rem;
        font-weight: 800;
        color: {text_main};
        letter-spacing: -0.01em;
    }}

    /* Footer */
    .platform-footer {{
        text-align: center;
        padding: 2.5rem 0 1.5rem 0;
        color: {text_sub};
        font-size: 0.9rem;
        border-top: 1px solid {border_color};
        margin-top: 3rem;
    }}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------
def parse_revision_sections(text: str):
    """Parses generated text into Summary, MCQs, and Key Terms."""
    summary_text = ""
    mcq_text = ""
    terms_text = ""

    s1_idx = text.find("### SECTION 1:")
    if s1_idx == -1:
        s1_idx = text.find("SECTION 1:")

    s2_idx = text.find("### SECTION 2:")
    if s2_idx == -1:
        s2_idx = text.find("SECTION 2:")

    s3_idx = text.find("### SECTION 3:")
    if s3_idx == -1:
        s3_idx = text.find("SECTION 3:")

    if s1_idx != -1 and s2_idx != -1 and s3_idx != -1 and s1_idx < s2_idx < s3_idx:
        summary_text = text[s1_idx:s2_idx].strip()
        mcq_text = text[s2_idx:s3_idx].strip()
        terms_text = text[s3_idx:].strip()
    else:
        summary_text = text
        mcq_text = ""
        terms_text = ""

    return summary_text, mcq_text, terms_text

SAMPLE_NOTES = (
    "Photosynthesis is the biological process used by plants, algae, and certain bacteria "
    "to convert light energy into chemical energy. This chemical energy is stored in carbohydrate "
    "molecules, such as sugars like glucose, synthesized from carbon dioxide and water.\n\n"
    "The process takes place primarily within chloroplasts, which contain the green pigment chlorophyll. "
    "Photosynthesis occurs in two stages: light-dependent reactions and the Calvin cycle (light-independent reactions).\n\n"
    "During the light reactions, sunlight splits water molecules, releasing oxygen as a byproduct and creating ATP and NADPH. "
    "In the Calvin cycle, ATP and NADPH are utilized to fix atmospheric carbon dioxide into glucose.\n\n"
    "Photosynthesis is fundamental to life on Earth as it produces virtually all oxygen in the atmosphere and forms the basis of global food chains."
)

# ---------------------------------------------------------
# SIDEBAR NAVIGATION & CONTROLS
# ---------------------------------------------------------
nav_options = [
    "🏠 Home",
    "✨ Create Revision Pack",
    "📝 My Notes",
    "🕒 Study History",
    "⚙️ Settings",
    "ℹ️ About"
]

with st.sidebar:
    # Logo
    st.markdown("""
    <div class="sidebar-logo">
        <div class="logo-icon">📚</div>
        <div>
            <div class="logo-text">AI Study Buddy</div>
            <div style="font-size: 0.72rem; color: #818CF8; font-weight: 600;">PRO AI PLATFORM</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Synchronize sidebar radio with session_state
    if st.session_state["current_page"] not in nav_options:
        st.session_state["current_page"] = "🏠 Home"

    # Radio widget linked with explicit on_change handler
    def on_nav_change():
        st.session_state["current_page"] = st.session_state["sidebar_nav_radio"]

    st.radio(
        "Navigation",
        nav_options,
        index=nav_options.index(st.session_state["current_page"]),
        key="sidebar_nav_radio",
        on_change=on_nav_change,
        label_visibility="collapsed"
    )

    st.write("---")

    # Model & Engine Status
    st.markdown("""
    <div style="font-size: 0.8rem; font-weight: 700; color: #94A3B8; margin-bottom: 0.5rem; text-transform: uppercase;">
        ⚡ AI Engine Status
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="model-badge" style="width: 100%; margin-bottom: 0.4rem; justify-content: flex-start;">
        <span style="color: #34D399;">●</span> Primary: <strong>Gemini 3.8 Flash</strong>
    </div>
    <div class="model-badge" style="width: 100%; justify-content: flex-start; background: rgba(59, 130, 246, 0.1); border-color: rgba(59, 130, 246, 0.25); color: #93C5FD;">
        <span style="color: #60A5FA;">●</span> Fallback: <strong>Gemini 3.5 Flash</strong>
    </div>
    """, unsafe_allow_html=True)

    st.write("---")

    # Quick Theme Switcher
    theme_choice = st.toggle("🌙 Dark Mode", value=(st.session_state["theme"] == "dark"))
    new_theme = "dark" if theme_choice else "light"
    if new_theme != st.session_state["theme"]:
        st.session_state["theme"] = new_theme
        st.rerun()

    # Reset / Clear All Button
    if st.button("🗑️ Reset Workspace", use_container_width=True):
        st.session_state["revision_pack"] = ""
        st.session_state["current_notes"] = ""
        st.session_state["pasted_notes"] = ""
        st.session_state["pdf_extracted_notes"] = ""
        st.session_state["model_used"] = ""
        st.rerun()

# Get current active page
current_page = st.session_state["current_page"]


# ---------------------------------------------------------
# PAGE 1: 🏠 HOME DASHBOARD
# ---------------------------------------------------------
if current_page == "🏠 Home":
    # Hero Welcome Section
    st.markdown("""
    <div class="hero-container">
        <div class="hero-title">Welcome back, Student! 👋</div>
        <div class="hero-subtitle">
            Your personal AI-powered study companion. Transform messy textbooks and lecture notes into concise 5-point summaries, 5 exam MCQs, and key term definitions in seconds.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Key Metric Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_packs = len(st.session_state["history"])
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Revision Packs</div>
            <div class="stat-value">{total_packs}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        curr_words = len(st.session_state["current_notes"].split()) if st.session_state["current_notes"] else 0
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Current Notes Words</div>
            <div class="stat-value">{curr_words:,}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-label">AI Availability</div>
            <div class="stat-value" style="color: #34D399;">99.9%</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-label">Study Efficiency</div>
            <div class="stat-value" style="color: #818CF8;">+4.5x</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    st.write("")

    # Quick Action Cards with functional navigation
    st.subheader("🚀 Quick Actions")
    qcol1, qcol2, qcol3 = st.columns(3)

    with qcol1:
        st.markdown("""
        <div class="glass-card">
            <div style="font-size: 1.6rem; margin-bottom: 0.5rem;">✨</div>
            <div style="font-size: 1.15rem; font-weight: 700; margin-bottom: 0.4rem;">Create Revision Pack</div>
            <div style="color: #94A3B8; font-size: 0.9rem; margin-bottom: 1rem;">
                Paste chapter notes to generate your 3-part exam revision pack.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Generating →", key="home_btn_gen", use_container_width=True):
            navigate_to("✨ Create Revision Pack", input_mode="📝 Paste Notes")

    with qcol2:
        st.markdown("""
        <div class="glass-card">
            <div style="font-size: 1.6rem; margin-bottom: 0.5rem;">📄</div>
            <div style="font-size: 1.15rem; font-weight: 700; margin-bottom: 0.4rem;">Upload Study PDF</div>
            <div style="color: #94A3B8; font-size: 0.9rem; margin-bottom: 1rem;">
                Extract text from lecture slides and chapters using PyPDF.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Upload Document →", key="home_btn_pdf", use_container_width=True):
            navigate_to("✨ Create Revision Pack", input_mode="📄 Upload PDF Document")

    with qcol3:
        st.markdown("""
        <div class="glass-card">
            <div style="font-size: 1.6rem; margin-bottom: 0.5rem;">🕒</div>
            <div style="font-size: 1.15rem; font-weight: 700; margin-bottom: 0.4rem;">Study History</div>
            <div style="color: #94A3B8; font-size: 0.9rem; margin-bottom: 1rem;">
                Access previously generated summaries, MCQs, and downloads.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open History →", key="home_btn_hist", use_container_width=True):
            navigate_to("🕒 Study History")

    # Recent Study Activity
    if st.session_state["history"]:
        st.write("")
        st.subheader("📚 Recently Generated Packs")
        for idx, item in enumerate(reversed(st.session_state["history"][-3:])):
            with st.expander(f"📦 {item['timestamp']} — {item['title']}", expanded=(idx == 0)):
                st.caption(f"⚡ Model: {item.get('model', 'Gemini AI')}")
                st.markdown(item["content"])
                h_c1, h_c2 = st.columns([1, 1])
                with h_c1:
                    if st.button(f"👁️ Open in Workspace", key=f"home_open_{idx}", use_container_width=True):
                        st.session_state["revision_pack"] = item["content"]
                        st.session_state["model_used"] = item.get("model", "Gemini AI")
                        navigate_to("✨ Create Revision Pack")
                with h_c2:
                    st.download_button(
                        label="📥 Download Pack (.txt)",
                        data=item["content"],
                        file_name=f"revision_pack_{idx+1}.txt",
                        mime="text/plain",
                        key=f"home_dl_{idx}",
                        use_container_width=True
                    )


# ---------------------------------------------------------
# PAGE 2: ✨ CREATE REVISION PACK (CORE WORKSPACE)
# ---------------------------------------------------------
elif current_page == "✨ Create Revision Pack":

    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <h1 style="font-size: 2rem; font-weight: 800; margin-bottom: 0.2rem;">✨ Create AI Revision Pack</h1>
        <p style="color: #94A3B8; font-size: 1.05rem;">
            Provide your study materials to automatically generate a 5–6 point Summary, 5 MCQs, and 3 Key Terms.
        </p>
    </div>
    """, unsafe_allow_html=True)

    input_options = ["📝 Paste Notes", "📄 Upload PDF Document"]
    current_input_mode = st.session_state.get("input_method_choice", "📝 Paste Notes")
    if current_input_mode not in input_options:
        current_input_mode = "📝 Paste Notes"

    def on_input_mode_change():
        st.session_state["input_method_choice"] = st.session_state["input_mode_radio_key"]

    selected_input_method = st.radio(
        "Choose your input method:",
        input_options,
        index=input_options.index(current_input_mode),
        key="input_mode_radio_key",
        on_change=on_input_mode_change,
        horizontal=True
    )

    notes = ""

    # Option 1: Paste Notes
    if "Paste" in selected_input_method:
        col_t1, col_t2, col_t3 = st.columns([4, 1.2, 1])
        with col_t2:
            if st.button("💡 Sample Notes", key="btn_sample_notes", use_container_width=True):
                st.session_state["pasted_notes"] = SAMPLE_NOTES
                st.session_state["current_notes"] = SAMPLE_NOTES
                st.rerun()
        with col_t3:
            if st.button("🧹 Clear", key="btn_clear_notes", use_container_width=True):
                st.session_state["pasted_notes"] = ""
                st.session_state["current_notes"] = ""
                st.rerun()

        pasted_text = st.text_area(
            "Paste your lecture notes, textbook chapters, or articles here:",
            value=st.session_state.get("pasted_notes", ""),
            height=240,
            placeholder="Paste chapter notes, lecture transcripts, or textbook text here...",
            key="text_area_notes"
        )
        if pasted_text != st.session_state.get("pasted_notes"):
            st.session_state["pasted_notes"] = pasted_text
            st.session_state["current_notes"] = pasted_text
        notes = pasted_text

    # Option 2: Upload PDF Document
    else:
        pdf_file = st.file_uploader(
            "Upload your study notes in PDF format:",
            type=["pdf"],
            help="Upload syllabus chapters, lecture slides, or reading materials.",
            key="pdf_uploader_widget"
        )

        if pdf_file is not None:
            try:
                with st.spinner("Extracting text with PyPDF..."):
                    pdf_reader = PdfReader(pdf_file)
                    total_pages = len(pdf_reader.pages)
                    extracted_pages = []

                    for page in pdf_reader.pages:
                        txt = page.extract_text() or ""
                        if txt.strip():
                            extracted_pages.append(txt)

                    pdf_notes = "\n".join(extracted_pages)
                    st.session_state["pdf_extracted_notes"] = pdf_notes
                    st.session_state["current_notes"] = pdf_notes
                    notes = pdf_notes

                    if pdf_notes.strip():
                        st.success(f"✅ Extracted text successfully from {len(extracted_pages)} of {total_pages} page(s) ({pdf_file.name}).")
                    else:
                        st.warning("⚠️ No readable text found. This PDF may contain scanned images without OCR.")

            except Exception as e:
                st.error(f"❌ Error reading PDF file: {e}")
        else:
            notes = st.session_state.get("pdf_extracted_notes", "")

    # Real-time Metrics & Actions Bar
    if notes.strip():
        words = len(notes.split())
        chars = len(notes)
        reading_time = max(1, round(words / 200))

        mcol1, mcol2, mcol3, mcol4 = st.columns([2, 2, 2, 2])
        with mcol1:
            st.markdown(f'<span class="meta-badge">📝 {words:,} Words</span>', unsafe_allow_html=True)
        with mcol2:
            st.markdown(f'<span class="meta-badge">🔤 {chars:,} Characters</span>', unsafe_allow_html=True)
        with mcol3:
            st.markdown(f'<span class="meta-badge">⏱️ ~{reading_time} min read</span>', unsafe_allow_html=True)
        with mcol4:
            if st.button("🗑️ Reset Notes", key="btn_reset_active_notes"):
                st.session_state["current_notes"] = ""
                st.session_state["pasted_notes"] = ""
                st.session_state["pdf_extracted_notes"] = ""
                st.rerun()

    st.write("")

    # Primary Action: Generate Revision Pack
    generate_clicked = st.button(
        "✨ Generate Revision Pack",
        type="primary",
        use_container_width=True,
        disabled=st.session_state["is_generating"],
        key="btn_generate_revision_pack"
    )

    if generate_clicked:
        if not notes.strip():
            st.warning("⚠️ Please enter study notes or upload a PDF document first!")
        else:
            api_key = os.getenv("GEMINI_API_KEY")

            if not api_key:
                st.error("❌ Gemini API key not found. Please verify `GEMINI_API_KEY` in your `.env` file.")
            else:
                st.session_state["is_generating"] = True

                prompt = f"""You are an expert, friendly AI study tutor helping a student prepare for exams.

Analyze the study notes below and generate a revision pack formatted strictly into the following three sections. Do not include any extra sections.

---
### SECTION 1: SUMMARY
- Write between 5 and 6 important, easy-to-understand bullet points summarizing the core concepts.

---
### SECTION 2: MULTIPLE-CHOICE QUESTIONS
Create exactly 5 multiple-choice questions based on the notes.
Format each question clearly as:
**Question [Number]: [Question Text]**
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
**Correct Answer:** [Letter and brief explanation]

---
### SECTION 3: KEY TERMS
Identify and explain exactly 3 important terms from the notes using simple English.
Format each term as:
- **[Term 1]:** [Clear, simple definition/explanation]
- **[Term 2]:** [Clear, simple definition/explanation]
- **[Term 3]:** [Clear, simple definition/explanation]

---
RULES:
1. Rely strictly on the information in the provided study notes. Do not hallucinate or make up outside facts.
2. Ensure there are exactly 5 to 6 summary bullets, exactly 5 MCQs (4 options each with correct answer), and exactly 3 key terms.

STUDY NOTES:
{notes}
"""

                try:
                    status_placeholder = st.empty()
                    generated_text = None
                    successful_model_label = None

                    # Primary and verified fallback models
                    models_to_try = [
                        {"id": "gemini-3.8-flash", "label": "Gemini 3.8 Flash (Primary)", "is_primary": True},
                        {"id": "gemini-3.5-flash", "label": "Gemini 3.5 Flash (Fallback)", "is_primary": False}
                    ]

                    for model in models_to_try:
                        model_id = model["id"]
                        model_label = model["label"]
                        is_primary = model["is_primary"]

                        with st.spinner(f"🤖 Generating revision pack using {model_label}..."):
                            try:
                                api_response = requests.post(
                                    f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent",
                                    headers={
                                        "Content-Type": "application/json",
                                        "x-goog-api-key": api_key.strip()
                                    },
                                    json={
                                        "contents": [
                                            {
                                                "parts": [
                                                    {"text": prompt}
                                                ]
                                            }
                                        ]
                                    },
                                    timeout=120
                                )
                            except requests.exceptions.RequestException as net_err:
                                st.error(f"❌ Network connection error with {model_label}: {net_err}")
                                break

                        # Case 1: Authentication / Invalid Key (Do NOT switch models)
                        if api_response.status_code in (400, 401, 403):
                            error_detail = ""
                            try:
                                err_json = api_response.json()
                                if "error" in err_json and "message" in err_json["error"]:
                                    error_detail = f": {err_json['error']['message']}"
                            except Exception:
                                pass
                            st.error(f"❌ Gemini Authentication Error ({api_response.status_code}){error_detail}")
                            break

                        # Case 2: High Demand (503) or Rate Limit (429) -> Fallback
                        if api_response.status_code in (503, 429):
                            reason = "high demand (503)" if api_response.status_code == 503 else "rate limit (429)"
                            if is_primary:
                                status_placeholder.warning(
                                    f"⏳ **{model_label}** is experiencing {reason}. Switching to fallback model **Gemini 3.5 Flash**..."
                                )
                                time.sleep(1.2)
                                continue
                            else:
                                status_placeholder.empty()
                                st.error(
                                    "⚠️ **Both primary and fallback models are currently busy.** "
                                    "Please try again in a moment."
                                )
                                break

                        # Case 3: Other unexpected error
                        if api_response.status_code != 200:
                            if is_primary:
                                status_placeholder.warning(
                                    f"⚠️ {model_label} returned {api_response.status_code}. Trying fallback model..."
                                )
                                time.sleep(1.0)
                                continue
                            else:
                                status_placeholder.empty()
                                st.error(f"❌ API Error ({api_response.status_code}): {api_response.text[:200]}")
                                break

                        # Case 4: Success (200 OK)
                        status_placeholder.empty()
                        data = api_response.json()
                        candidates = data.get("candidates", [])
                        if not candidates:
                            st.warning("⚠️ No response candidates returned by Gemini. Content may have been blocked by safety filters.")
                            break

                        parts = candidates[0].get("content", {}).get("parts", [])
                        text_parts = [p.get("text", "") for p in parts if not p.get("thought", False)]
                        if not text_parts:
                            text_parts = [p.get("text", "") for p in parts]

                        generated_text = "".join(text_parts).strip()
                        successful_model_label = model_label
                        break

                    if generated_text:
                        st.session_state["revision_pack"] = generated_text
                        st.session_state["model_used"] = successful_model_label

                        # Save into session and local JSON history
                        title_snip = notes.strip().split("\n")[0][:45] or "Study Notes"
                        new_item = {
                            "id": str(int(time.time() * 1000)),
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "title": title_snip,
                            "content": generated_text,
                            "model": successful_model_label
                        }
                        st.session_state["history"].append(new_item)
                        save_local_history(st.session_state["history"])

                except Exception as e:
                    st.error(f"❌ An error occurred: {e}")
                finally:
                    st.session_state["is_generating"] = False

    # ---------------------------------------------------------
    # DISPLAY AI GENERATED RESULTS IN DEDICATED CARDS
    # ---------------------------------------------------------
    if st.session_state["revision_pack"]:
        st.write("---")

        # Result Header with Model Tag & Export Options
        head_c1, head_c2 = st.columns([3, 2])
        with head_c1:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 0.8rem; margin-bottom: 0.5rem;">
                <h2 style="margin: 0; font-size: 1.6rem; font-weight: 800;">🎉 Revision Pack Ready</h2>
                <span class="model-badge">⚡ {st.session_state.get('model_used', 'Gemini AI')}</span>
            </div>
            """, unsafe_allow_html=True)

        with head_c2:
            dl_c1, dl_c2 = st.columns(2)
            with dl_c1:
                st.download_button(
                    label="📥 Download .txt",
                    data=st.session_state["revision_pack"],
                    file_name="revision_pack.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="dl_pack_txt_main"
                )
            with dl_c2:
                st.download_button(
                    label="📥 Download .md",
                    data=st.session_state["revision_pack"],
                    file_name="revision_pack.md",
                    mime="text/markdown",
                    use_container_width=True,
                    key="dl_pack_md_main"
                )

        # Parse output into dedicated structured cards
        summary_sec, mcq_sec, terms_sec = parse_revision_sections(st.session_state["revision_pack"])

        # Display Tabbed & Card Views
        view_tabs = st.tabs(["📑 All Cards", "📌 Section 1: Summary", "❓ Section 2: MCQs", "🔑 Section 3: Key Terms", "📋 Raw Document"])

        with view_tabs[0]:
            # Card A: Summary
            st.markdown("""
            <div class="output-card">
                <div class="output-header summary">
                    <span>📌</span> SECTION 1: SUMMARY (5–6 Bullet Points)
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(summary_sec or "Summary section not detected.")

            st.write("")

            # Card B: Multiple Choice Questions
            st.markdown("""
            <div class="output-card">
                <div class="output-header mcq">
                    <span>❓</span> SECTION 2: MULTIPLE-CHOICE QUESTIONS (5 MCQs & Answers)
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(mcq_sec or "MCQ section not detected.")

            st.write("")

            # Card C: Key Terms
            st.markdown("""
            <div class="output-card">
                <div class="output-header terms">
                    <span>🔑</span> SECTION 3: KEY TERMS (3 Definitions)
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(terms_sec or "Key terms section not detected.")

        with view_tabs[1]:
            st.markdown(summary_sec)
        with view_tabs[2]:
            st.markdown(mcq_sec)
        with view_tabs[3]:
            st.markdown(terms_sec)
        with view_tabs[4]:
            st.markdown(st.session_state["revision_pack"])
            st.caption("Copy raw markdown text:")
            st.code(st.session_state["revision_pack"], language="markdown")


# ---------------------------------------------------------
# PAGE 3: 📝 MY NOTES
# ---------------------------------------------------------
elif current_page == "📝 My Notes":
    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <h1 style="font-size: 2rem; font-weight: 800; margin-bottom: 0.2rem;">📝 My Study Notes</h1>
        <p style="color: #94A3B8; font-size: 1.05rem;">
            Review and edit your active study notes before generating a revision pack.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state["current_notes"]:
        st.info("ℹ️ No active notes found. Go to **✨ Create Revision Pack** to paste notes or upload a PDF.")
        if st.button("Go to Create Revision Pack →", key="btn_my_notes_goto_create"):
            navigate_to("✨ Create Revision Pack", input_mode="📝 Paste Notes")
    else:
        edited_notes = st.text_area(
            "Active Notes Editor:",
            value=st.session_state["current_notes"],
            height=380,
            key="my_notes_editor"
        )
        st.session_state["current_notes"] = edited_notes
        st.session_state["pasted_notes"] = edited_notes

        ncol1, ncol2 = st.columns([2, 2])
        with ncol1:
            if st.button("✨ Generate Pack with these Notes", type="primary", use_container_width=True, key="btn_generate_from_my_notes"):
                navigate_to("✨ Create Revision Pack", input_mode="📝 Paste Notes")
        with ncol2:
            st.download_button(
                label="📥 Export Notes (.txt)",
                data=edited_notes,
                file_name="my_notes.txt",
                mime="text/plain",
                use_container_width=True,
                key="btn_download_my_notes"
            )


# ---------------------------------------------------------
# PAGE 4: 🕒 STUDY HISTORY
# ---------------------------------------------------------
elif current_page == "🕒 Study History":
    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <h1 style="font-size: 2rem; font-weight: 800; margin-bottom: 0.2rem;">🕒 Study History & Past Packs</h1>
        <p style="color: #94A3B8; font-size: 1.05rem;">
            Access all revision packs generated during your study sessions. Saved locally for offline persistence.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state["history"]:
        st.markdown("""
        <div class="glass-card" style="text-align: center; padding: 3rem;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📂</div>
            <div style="font-size: 1.2rem; font-weight: 700; margin-bottom: 0.3rem;">No Study History Yet</div>
            <div style="color: #94A3B8; font-size: 0.95rem; margin-bottom: 1rem;">Generate your first revision pack to track your session history here.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Create Your First Pack →", key="btn_create_first_pack"):
            navigate_to("✨ Create Revision Pack", input_mode="📝 Paste Notes")
    else:
        hcol1, hcol2 = st.columns([4, 1.2])
        with hcol1:
            st.caption(f"Showing {len(st.session_state['history'])} saved revision pack(s).")
        with hcol2:
            if st.button("🗑️ Clear All History", key="btn_clear_all_history", use_container_width=True):
                st.session_state["history"] = []
                save_local_history([])
                st.rerun()

        for idx, item in enumerate(reversed(st.session_state["history"])):
            item_id = item.get("id", str(idx))
            with st.expander(f"📦 {item['timestamp']} — {item['title']}", expanded=(idx == 0)):
                st.markdown(f'<span class="model-badge">⚡ {item.get("model", "Gemini AI")}</span>', unsafe_allow_html=True)
                st.write("")
                st.markdown(item["content"])

                act_col1, act_col2, act_col3 = st.columns([1.5, 1.5, 1])
                with act_col1:
                    if st.button("👁️ Open in Workspace", key=f"hist_open_{item_id}", use_container_width=True):
                        st.session_state["revision_pack"] = item["content"]
                        st.session_state["model_used"] = item.get("model", "Gemini AI")
                        navigate_to("✨ Create Revision Pack")
                with act_col2:
                    st.download_button(
                        label="📥 Download (.txt)",
                        data=item["content"],
                        file_name=f"revision_pack_{item['timestamp'].replace(' ', '_').replace(':', '-')}.txt",
                        mime="text/plain",
                        key=f"hist_dl_{item_id}",
                        use_container_width=True
                    )
                with act_col3:
                    if st.button("🗑️ Delete", key=f"hist_del_{item_id}", use_container_width=True):
                        st.session_state["history"] = [h for h in st.session_state["history"] if h.get("id") != item_id]
                        save_local_history(st.session_state["history"])
                        st.rerun()


# ---------------------------------------------------------
# PAGE 5: ⚙️ SETTINGS
# ---------------------------------------------------------
elif current_page == "⚙️ Settings":
    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <h1 style="font-size: 2rem; font-weight: 800; margin-bottom: 0.2rem;">⚙️ Platform Settings</h1>
        <p style="color: #94A3B8; font-size: 1.05rem;">
            Configure your AI preferences and platform options.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="glass-card">
        <h3 style="margin-top: 0; font-size: 1.2rem; font-weight: 700;">🔑 API Configuration & Status</h3>
    """, unsafe_allow_html=True)

    env_key = os.getenv("GEMINI_API_KEY", "")
    if env_key:
        masked_key = env_key[:6] + "..." + env_key[-4:] if len(env_key) > 10 else "******"
        st.success(f"✅ Gemini API Key detected in `.env` (`{masked_key}`)")

        if st.button("🧪 Test API Connection Live", key="btn_test_api"):
            with st.spinner("Pinging Gemini API..."):
                try:
                    t_resp = requests.post(
                        "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent",
                        headers={"Content-Type": "application/json", "x-goog-api-key": env_key.strip()},
                        json={"contents": [{"parts": [{"text": "ping"}]}]},
                        timeout=10
                    )
                    if t_resp.status_code == 200:
                        st.success("🎉 Connection Test Passed! Gemini API is active & responsive.")
                    else:
                        st.warning(f"⚠️ API returned status {t_resp.status_code}: {t_resp.text[:150]}")
                except Exception as ex:
                    st.error(f"❌ Connection error: {ex}")
    else:
        st.error("❌ No `GEMINI_API_KEY` detected in `.env`. Please add your key to `.env`.")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="glass-card">
        <h3 style="margin-top: 0; font-size: 1.2rem; font-weight: 700;">🤖 AI Engine Failover Routing</h3>
        <p style="color: #94A3B8; font-size: 0.95rem;">
            The platform is configured with smart automatic failover:
        </p>
        <ul>
            <li><strong>Primary Model:</strong> <code>gemini-3.8-flash</code> (Highest reasoning quality and context)</li>
            <li><strong>Fallback Model:</strong> <code>gemini-3.5-flash</code> (Activated automatically if 503 high demand or 429 rate limit is detected)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------
# PAGE 6: ℹ️ ABOUT
# ---------------------------------------------------------
elif current_page == "ℹ️ About":
    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <h1 style="font-size: 2rem; font-weight: 800; margin-bottom: 0.2rem;">ℹ️ About AI Study Buddy</h1>
        <p style="color: #94A3B8; font-size: 1.05rem;">
            College assignment project engineered as a modern AI SaaS study platform.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="glass-card">
        <h3 style="margin-top: 0; font-size: 1.2rem; font-weight: 700;">🎯 Project Mission</h3>
        <p style="color: #94A3B8; line-height: 1.6;">
            AI Study Buddy helps students synthesize extensive educational material into high-yield revision resources.
            By extracting text from PDFs and applying Gemini AI prompt engineering, it produces structured revision packs:
        </p>
        <ol style="color: #94A3B8; line-height: 1.7;">
            <li><strong>Core Summary:</strong> 5 to 6 concise bullet points.</li>
            <li><strong>Exam Practice:</strong> Exactly 5 Multiple Choice Questions with 4 options and answers.</li>
            <li><strong>Key Terms:</strong> 3 critical definitions explained in simple English.</li>
        </ol>
    </div>
    <div class="glass-card">
        <h3 style="margin-top: 0; font-size: 1.2rem; font-weight: 700;">🛠️ Tech Stack</h3>
        <ul>
            <li><strong>Frontend / UI:</strong> Streamlit with custom glassmorphism styling</li>
            <li><strong>PDF Parser:</strong> PyPDF (<code>pypdf.PdfReader</code>)</li>
            <li><strong>AI Inference:</strong> Google Generative Language REST API (Gemini 3.8 Flash & Gemini 3.5 Flash)</li>
            <li><strong>Local Persistence:</strong> JSON file storage (<code>study_history.json</code>)</li>
            <li><strong>Environment:</strong> Python dotenv</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------
# PLATFORM FOOTER
# ---------------------------------------------------------
st.markdown("""
<div class="platform-footer">
    Made with ❤️ for smarter learning.
</div>
""", unsafe_allow_html=True)
