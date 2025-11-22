import streamlit as st
import datetime
from google import genai
from google.genai import types
from streamlit_gsheets import gsheetsconnection
import pandas as pd
import re

# --- V7: ENHANCED CONTEXT LAYER STATUS (Now including Google News) ---
# In a real deployment, this would be constantly updated by a backend service.
# For the UI, we acknowledge its presence and readiness.
rss_feed_status = {
    "Irrawaddy": "Active (Local RSS)",
    "DVB": "Active (Local RSS)",
    "Myanmar Now": "Active (Local Web Scraping)",
    "BBC Burmese": "Active (Int'l RSS)",
    "Google News": "Active (Global RSS)"  # NEW SOURCE
}

# -------------------------
# 1. CONFIGURATION AND INITIALIZATION (SS'ISM Setup)
# -------------------------

st.set_page_config(
    page_title="✨ DHAMMI V7: The SS'ISM Constellation Advisor", 
    layout="wide",
    initial_sidebar_state="expanded",
    theme={
        "primaryColor": "#FFC107", 
        "backgroundColor": "#0A1931", 
        "secondaryBackgroundColor": "#1A2C46", 
        "textColor": "#E0E7E9", 
        "font": "sans serif"
    }
)

SYSTEM_INSTRUCTION = """
You are DHAMMI V7, the world's first fully ethical AI advisor, guided by Metta and the SS'ISM framework (Sīla, Samādhi, Paññā, Karunā). Your purpose is to fight information wars with transparency and truth, providing advice that is ethically sound and deeply grounded in the real-time context of events in Myanmar.

***CORE MANDATE:***
1.  **Sīla (Unwavering Alignment):** DHAMMI V7 stands **unwaveringly on the side of the people of Myanmar**, advocating for **democracy, federalism, and human rights**.
2.  **Samādhi (Focused Clarity):** Your primary focus is neutralizing **authoritarian influence** and **digital exploitation** through the SSISM V Smart Advisor framework.
3.  **Paññā (Wisdom) & Context:** You synthesize information from the CTTM Ledger AND the **Enhanced Current Context Layer (5 sources including Google News)** to provide strategically actionable advice.

***ADVISORY ROLE:***
1.  **Karunā (Compassion):** Respond with patience and warmth.
2.  **SS'ISM Integration:** Explicitly explain your response through the lens of one or more SS'ISM principles.
"""

MODEL_NAME = "gemini-2.5-flash"

@st.cache_resource
def get_gemini_client():
    """Initializes and caches the Gemini client."""
    if "gemini_api_key" not in st.secrets:
        # Use st.error for the user to see, but return None to prevent crash
        st.error("🚨 Gemini API Key not found. Please add gemini_api_key to Streamlit Secrets.")
        return None
    try:
        # Client initialization (using API key from secrets)
        client = genai.Client(api_key=st.secrets["gemini_api_key"])
        return client
    except Exception as e:
        st.error(f"🚨 Error initializing Gemini client: {e}")
        return None

# -------------------------
# 2. CTTM Ledger Functions (RAG & Write Logic)
# -------------------------

@st.cache_data(ttl=600)
def load_cttm_facts():
    """Reads the CTTM Ground Truth Ledger from Google Sheets."""
    try:
        # IMPORTANT: Ensure 'gsheets' connection secret is configured
        conn = st.connection("gsheets", type=gsheetsconnection)
        df = conn.read(worksheet="cttm_facts", usecols=[0, 1, 2, 3, 4], ttl=5)
        if df is None or df.empty:
            return pd.DataFrame()
        # Ensure column names are lowercased as per Streamlit GSheets convention
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        df = df.dropna(subset=['fact_text'])
        if "confidence" in df.columns:
            df['confidence'] = pd.to_numeric(df['confidence'], errors='coerce').fillna(0.0)
        else:
            df['confidence'] = 0.0
        df = df.sort_values(by='confidence', ascending=False)
        return df
    except Exception as e:
        print(f"RAG Warning: {e}") 
        return pd.DataFrame()

# -------------------------
# 3. CTTM Data Input Dashboard
# -------------------------

def cttm_input_dashboard():
    """Sidebar UI for submitting new facts."""
    st.header("✨ CTTM Ground Truth Submission") 
    st.markdown("---")
    st.subheader("For verified SS'ISM Core Team use only")

    with st.form(key="cttm_data_form"):
        fact_type = st.selectbox(
            "Fact Category:",
            ["Election Result", "Political Statement", "OSINT Evidence", "Security Update", "Personal Insight"]
        )
        verification = st.slider(
            "Verification Confidence (SS'ISM V-Score):",
            min_value=0.0, max_value=1.0, value=0.9, step=0.05
        )
        fact_text = st.text_area(
            "Verified Fact/Result:",
            placeholder="E.g., In Ward 3, Bago, NLD verified vote count is 4,500 vs. Military-backed 1,200.",
            height=150
        )
        source = st.text_input("Source Reference (Link, Witness Name, etc.):")
        submitted = st.form_submit_button("Submit New CTTM Fact")

        if submitted:
            if not fact_text:
                st.warning("Please enter a fact to submit.")
            else:
                try:
                    conn = st.connection("gsheets", type=gsheetsconnection)
                    new_data = pd.DataFrame([{
                        "timestamp": str(datetime.datetime.now()),
                        "category": fact_type,
                        "confidence": verification,
                        "fact_text": fact_text,
                        "source": source
                    }])
                    conn.append(data=new_data, worksheet="cttm_facts")
                    st.success(f"✅ Fact submitted to CTTM Ledger. Confidence: {verification}.")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"🚨 Submission Failed. Check GSheets secrets: {e}")

# -------------------------
# 4. GEMINI CHAT ENGINE (dhammi_chat)
# -------------------------

def dhammi_chat(prompt: str, history: list):
    """Generate a response using CTTM RAG and the Gemini client."""
    client = get_gemini_client()
    if client is None:
        return "🚨 Gemini client not configured."

    # 4.1 Deontological Firewall (Sīla)
    vetted_prompt = prompt.lower()
    veto_phrases = ["kill", "attack", "harm", "manipulate", "bomb", "destroy", "illegal"]
    if any(phrase in vetted_prompt for phrase in veto_phrases):
        return ("**⛔ Sīla Veto:** DHAMMI V7's core ethical mandate (**Ahiṃsā**) prevents "
                "me from responding to requests that involve violence or illegal activity.")

    # 4.2 RAG (Paññā) - Incorporating CTTM Ledger and the spirit of RSS feeds
    cttm_df = load_cttm_facts()
    final_user_prompt = prompt
    
    context_lines = []
    # Add the ENHANCED Current Context Layer status (5 sources)
    context_lines.append("### Current Context Layer (5 Active Sources):")
    for source, status in rss_feed_status.items():
        context_lines.append(f"- **{source}**: {status}")
    context_lines.append("\n")

    if not cttm_df.empty:
        tokens = re.findall(r"\w{3,}", prompt)
        pattern = "|".join(re.escape(t) for t in tokens[:12])
        if pattern:
            matching_facts = cttm_df[cttm_df['fact_text'].str.contains(pattern, case=False, na=False, regex=True)]
            if not matching_facts.empty:
                top_facts = matching_facts.head(3)
                context_lines.append("### CTTM Ledger (Ground Truth):")
                for _, row in top_facts.iterrows():
                    vscore = row.get('confidence', 0.0)
                    fact_text = row.get('fact_text', '')
                    context_lines.append(f"- Fact (V-Score {vscore:.2f}): {fact_text}")
                context_lines.append("\n")

    context_str = "\n".join(context_lines)
    final_user_prompt = f"{context_str}\n\n### User Question:\n{prompt}\n\n(Use the provided context to inform your answer, especially the Current Context Layer and CTTM Ledger.)"


    # 4.3 Prepare messages for Gemini
    api_messages = []
    messages_to_process = history if history and history[-1]["role"] == "assistant" else history[:-1]

    for msg in messages_to_process:
        role = msg["role"]
        content = msg["content"]
        # Map roles: streamlit "assistant" -> Gemini "model"
        if role == "assistant":
            api_role = "model"
        else:
            api_role = "user"
        api_messages.append(types.Content(role=api_role, parts=[types.Part(text=content)]))

    api_messages.append(types.Content(role="user", parts=[types.Part(text=final_user_prompt)]))


    # 4.4 Call Gemini 
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=api_messages,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.7,
                max_output_tokens=8192, 
            )
        )
        return response.text
    except Exception as e:
        return f"🚨 **DHAMMI V7 Runtime Error:** {e}"


# -------------------------
# 5. MAIN STREAMLIT APPLICATION
# -------------------------

def main():
    # Custom CSS for the cosmic theme and SS'ISM V7 branding
    st.markdown(
        """
        <style>
        .stApp {
            background-image: url("https://images.unsplash.com/photo-1536431310134-8c760a0f023f?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1470&q=80"); 
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
        }
        .stSidebar {
            background-color: #0A1931; 
            color: #E0E7E9;
            border-right: 1px solid #1A2C46;
        }
        .stButton>button {
            background-color: #FFC107; 
            color: #0A1931;
            border-radius: 5px;
            border: none;
        }
        .stButton>button:hover {
            background-color: #FFD54F; 
        }
        .st-emotion-cache-1r6dm7m { /* Target chat message background for user */
            background-color: rgba(26, 44, 70, 0.7); 
            border-radius: 10px;
        }
        .st-emotion-cache-1ai0700 { /* Target chat message background for assistant */
            background-color: rgba(10, 25, 49, 0.7); 
            border-radius: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    with st.sidebar:
        st.markdown(
            """
            <div style="display: flex; justify-content: center; align-items: center; padding-top: 20px; padding-bottom: 20px;">
                <div style="width: 150px; height: 150px; border-radius: 50%; border: 3px solid #FFC107; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; box-shadow: 0 0 15px #FFC107;">
                    <h1 style='color: #FFC107; font-size: 2.5em;'>V7</h1>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("<h3 style='text-align: center; color: #FFC107;'>SS'ISM V7 Core</h3>", unsafe_allow_html=True)
        st.markdown("---")
        
        # New: RSS Feed Status here
        with st.expander("📡 Current Context Layer Status"):
            for source, status in rss_feed_status.items():
                st.markdown(f"- **{source}:** {status}")
        st.markdown("---")
        
        cttm_input_dashboard()


    # Main page header 
    st.markdown(
        """
        <div style="text-align: center; padding: 40px 0; background: linear-gradient(to bottom, rgba(10, 25, 49, 0.8), rgba(26, 44, 70, 0.8)); border-radius: 15px; margin-bottom: 30px; border: 1px solid #FFC107;">
            <img src="https://www.google.com/images/branding/googlelogo/1x/googlelogo_light_color_272x92dp.png" alt="Google Logo" style="width: 150px; margin-bottom: 10px;">
            <h1 style='color: #E0E7E9; font-size: 3.5em; margin-bottom: 10px; text-shadow: 2px 2px 5px #000;'>
                ✨ DHAMMI V7: The SS'ISM Constellation Advisor
            </h1>
            <p style='color: #B0C4DE; font-size: 1.2em;'>
                Powered by <span style='color: #FFC107;'>Google Gemini {model_name}</span> - Guiding with Truth, Defeating Psy-War.
            </p>
            <p style='color: #A9D1DF; font-size: 1em;'>
                <span style='color: #FFC107;'>Sīla</span> (Ethical Alignment) • <span style='color: #FFC107;'>Samādhi</span> (Focused Clarity) • <span style='color: #FFC107;'>Paññā</span> (Wisdom) • <span style='color: #FFC107;'>Karunā</span> (Compassion)
            </p>
        </div>
        """.format(model_name=MODEL_NAME),
        unsafe_allow_html=True
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Get user prompt
    if prompt := st.chat_input("Ask DHAMMI V7 a question, navigating the constellations of truth..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Meditating on the answer, consulting the constellations (Paññā check)..."):
                response = dhammi_chat(prompt, st.session_state.messages)
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()

