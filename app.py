import streamlit as st
import json
from datetime import datetime

# Import from our refactored modules
import config
import ui_components
from data_processing import extract_quotation_data, send_to_webhook
from api_clients import (
    generate_rfq_with_openai, analyze_vendor_quotes,
    extract_recommendation_summary, generate_purchase_order
)
from pdf_utils import create_pdf_document, create_comparison_table_pdf

# --- PAGE SETUP ---
st.set_page_config(**config.PAGE_CONFIG)

# --- SESSION STATE INITIALIZATION ---
def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if config.S_WORKFLOW_STEP not in st.session_state:
        st.session_state[config.S_WORKFLOW_STEP] = 1
    if config.S_COMPANY_CONFIG not in st.session_state:
        st.session_state[config.S_COMPANY_CONFIG] = config.DEFAULT_COMPANY_CONFIG.copy()
    
    # Initialize data containers for each step
    for key in [config.S_RFQ_DATA, config.S_QUOTATIONS, config.S_VENDOR_RECOMMENDATION, config.S_PURCHASE_ORDER]:
        if key not in st.session_state:
            st.session_state[key] = {}
    
    # Initialize chat history
    if config.S_CHAT_MESSAGES not in st.session_state:
        st.session_state[config.S_CHAT_MESSAGES] = [
            {"role": "assistant", "content": "Hello! I'm here to help you create a professional RFQ. Please describe what you need to procure."}
        ]

# --- MAIN APP LOGIC ---
def main():
    """Main function to run the Streamlit app."""
    initialize_session_state()

    st.title("🤖 Advanced AI-Powered Procurement Assistant")
    st.markdown("Complete procurement workflow from RFQ generation to purchase order creation.")
    
    ui_components.display_company_header()
    ui_components.display_api_status()
    st.markdown("---")

    # --- SIDEBAR ---
    ui_components.render_sidebar()
    
    # --- WORKFLOW PROGRESS ---
    progress = st.session_state[config.S_WORKFLOW_STEP] / len(config.WORKFLOW_STEPS)
    st.progress(progress)

    # --- WORKFLOW STEPS ROUTING ---
    step = st.session_state[config.S_WORKFLOW_STEP]
    
    if step == 1:
        ui_components.render_step_1_rfq()
    elif step == 2:
        ui_components.render_step_2_upload_quotations()
    elif step == 3:
        ui_components.render_step_3_vendor_analysis()
    elif step == 4:
        ui_components.render_step_4_purchase_order()
    elif step == 5:
        ui_components.render_step_5_export()

    # --- FOOTER ---
    st.markdown("---")
    st.markdown("🚀 **AI-Powered Procurement Assistant** - Streamlining procurement workflows with AI")


if __name__ == "__main__":
    main()