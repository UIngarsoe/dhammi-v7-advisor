# cttm_ledger_data.py

# --- SSISM V7 CTTM LEDGER: Counter-Tactical Trust Matrix ---
# This data acts as the "historical experience" feed for the RAG system.

# 1. SSISM CORE PRINCIPLES (Sīla Principles)
# These are the philosophical and operational constraints.
SILA_PRINCIPLES = {
    "P1_MANDATORY_LOCKOUT": {
        "description": "Institutionalize delay. All decisions where Phi < 0.2 require a 24-hour verification protocol.",
        "priority": "Critical",
        "action": "Delay & Verify"
    },
    "P2_NO_SHAME_ALERT": {
        "description": "Encourage reporting of suspicious activity without judgement to lower emotional barriers.",
        "priority": "High",
        "action": "Report"
    },
    "P3_DOING_NOTHING": {
        "description": "The principle of 'Doing Nothing as Value.' In uncertain high-risk situations (high Z-score), inaction is the safest default.",
        "priority": "Core",
        "action": "Inaction Default"
    }
}

# 2. DEFAULT WEIGHTING (Base Model Parameters - Used when RAG fails)
# These are the default weights (w_i) for the Z-Score calculation.
DEFAULT_FACTOR_WEIGHTS = {
    'Authority': 0.40,      # w_A: High weight due to confirmed systemic fraud (Nay Pyi Taw link)
    'Urgency': 0.25,        # w_U: Moderate weight
    'Linguistics': 0.10,    # w_L: Lower weight (focus is on system/data, not just grammar)
    'Link_File': 0.20,      # w_R: High weight due to critical forensic value (motherboards, phone traffic)
    'Time_Anomaly': 0.05    # w_DeltaT: Lowest weight
}

# 3. HISTORICAL SCAM PROFILES (Training Data/CTTM Entries)
# Example entries based on past SSISM briefings, which the RAG system retrieves.
HISTORICAL_PROFILES = [
    {
        "ID": "CTTM_2025_11_28_MINLETPAN",
        "outcome": "Success (KNU Seizure, Junta Exposure)",
        "input_factors": {'Authority': 1.0, 'Urgency': 0.8, 'Link_File': 1.0},
        "lesson": "Systemic crime confirmed. High A & R factors are critical predictors of state-level risk."
    },
    {
        "ID": "CTTM_2025_Q3_PHISHING",
        "outcome": "Failure (Attempted Theft)",
        "input_factors": {'Linguistics': 0.9, 'Time_Anomaly': 0.7, 'Authority': 0.1},
        "lesson": "High L & DeltaT with low A indicates standard social engineering attack profile."
    }
]

# Export all data structures for use by the main engine
CTTM_LEDGER = {
    "principles": SILA_PRINCIPLES,
    "weights": DEFAULT_FACTOR_WEIGHTS,
    "profiles": HISTORICAL_PROFILES
}

# --- END OF CTTM LEDGER ---
