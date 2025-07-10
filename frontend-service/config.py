import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- API KEYS ---
# Load from Streamlit secrets first, otherwise from .env file
AGENTQL_API_KEY = st.secrets.get("AGENTQL_API_KEY", os.getenv("AGENTQL_API_KEY"))
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))

# --- PAGE CONFIGURATION ---
PAGE_CONFIG = {
    "layout": "wide",
    "page_title": "AI Procurement Assistant",
    "page_icon": "🤖",
    "initial_sidebar_state": "expanded"
}

# --- WORKFLOW STEPS ---
WORKFLOW_STEPS = [
    "1. 💬 สร้าง RFQ / Generate RFQ",
    "2. 📄 อัปโหลดใบเสนอราคา / Upload Quotations",
    "3. 🔍 วิเคราะห์ผู้ขาย / Vendor Analysis",
    "4. 📋 ใบสั่งซื้อ / Purchase Order",
    "5. 📤 ส่งออกและเชื่อมต่อ / Export & Integration"
]

# --- DEFAULT COMPANY SETTINGS ---
DEFAULT_COMPANY_CONFIG = {
    'company_name': '',
    'company_address': '',
    'company_contact': '',
    'company_phone': '',
    'rfq_validity_days': 30,
    'default_delivery_location': '',
    'default_payment_terms': 'Net 30'
}

# --- SESSION STATE KEYS ---
# Using constants for keys prevents typos and makes code more maintainable
S_WORKFLOW_STEP = 'workflow_step'
S_RFQ_DATA = 'rfq_data'
S_QUOTATIONS = 'quotations'
S_VENDOR_RECOMMENDATION = 'vendor_recommendation'
S_PURCHASE_ORDER = 'purchase_order'
S_CHAT_HISTORY = 'chat_history'
S_COMPANY_CONFIG = 'company_config'
S_CHAT_MESSAGES = 'chat_messages'