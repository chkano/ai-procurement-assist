import requests
import streamlit as st
import json
import pandas as pd
from datetime import datetime

# Import from our other project modules
import config

# --- API Service URLs ---
# These URLs are based on the service names in docker-compose
PROCUREMENT_SERVICE_URL = "http://procurement-service:8000"
DATA_EXTRACTION_URL = "http://data-extraction-service:8001"
PDF_SERVICE_URL = "http://pdf-service:8002"

def send_to_webhook(data, webhook_url):
    """Send data to a specified webhook endpoint."""
    if not webhook_url:
        return {"success": False, "error": "Webhook URL is not provided."}
    try:
        response = requests.post(
            webhook_url,
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        response.raise_for_status() # Raise an exception for bad status codes
        return {"success": True, "status_code": response.status_code, "response": response.text}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Failed to send data: {str(e)}"}
    
# --- Helper function to handle API calls ---
def handle_api_request(method, url, **kwargs):
    try:
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        if 'application/json' in response.headers.get('Content-Type', ''):
            return response.json()
        return response.content
    except requests.exceptions.RequestException as e:
        st.error(f"API Request Failed: {e.response.text if e.response else str(e)}")
        return None

# --- UI Rendering Functions (No changes to display_company_header, display_api_status, render_sidebar) ---
def display_company_header():
    """Displays the company information header if it exists."""
    company_name = st.session_state[config.S_COMPANY_CONFIG].get('company_name')
    if company_name:
        with st.expander(f"🏢 Company: {company_name}", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Address:** {st.session_state[config.S_COMPANY_CONFIG].get('company_address', 'Not set')}")
                st.write(f"**Contact:** {st.session_state[config.S_COMPANY_CONFIG].get('company_contact', 'Not set')}")
            with col2:
                st.write(f"**Phone:** {st.session_state[config.S_COMPANY_CONFIG].get('company_phone', 'Not set')}")
                st.write(f"**Payment Terms:** {st.session_state[config.S_COMPANY_CONFIG].get('default_payment_terms', 'Not set')}")
    else:
        st.info("👈 Please configure your company information in the sidebar to get started.")

def display_api_status():
    """Shows the status of the required API keys."""
    col1, col2 = st.columns(2)
    with col1:
        if config.AGENTQL_API_KEY:
            st.success("✅ AgentQL API Ready")
        else:
            st.error("❌ AgentQL API Key Required")
    with col2:
        if config.OPENAI_API_KEY:
            st.success("✅ OpenAI API Ready")
        else:
            st.error("❌ OpenAI API Key Required")

def render_sidebar():
    """Renders the entire sidebar, including navigation and configuration."""
    st.sidebar.header("Procurement Workflow")
    selected_step = st.sidebar.selectbox(
        "Current Step:",
        config.WORKFLOW_STEPS,
        index=st.session_state[config.S_WORKFLOW_STEP] - 1
    )
    st.session_state[config.S_WORKFLOW_STEP] = config.WORKFLOW_STEPS.index(selected_step) + 1

    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Company Configuration")

    with st.sidebar.expander("🏢 Company Information", expanded=True):
        st.session_state[config.S_COMPANY_CONFIG]['company_name'] = st.text_input(
            "Company Name", value=st.session_state[config.S_COMPANY_CONFIG].get('company_name', ''))
        st.session_state[config.S_COMPANY_CONFIG]['company_address'] = st.text_area(
            "Company Address", value=st.session_state[config.S_COMPANY_CONFIG].get('company_address', ''), height=80)
        st.session_state[config.S_COMPANY_CONFIG]['company_contact'] = st.text_input(
            "Contact Email", value=st.session_state[config.S_COMPANY_CONFIG].get('company_contact', ''))
        st.session_state[config.S_COMPANY_CONFIG]['company_phone'] = st.text_input(
            "Phone Number", value=st.session_state[config.S_COMPANY_CONFIG].get('company_phone', ''))

    with st.sidebar.expander("📋 Default RFQ Settings"):
        st.session_state[config.S_COMPANY_CONFIG]['default_payment_terms'] = st.selectbox(
            "Default Payment Terms",
            options=["Net 15", "Net 30", "Net 45", "Net 60"],
            index=2 # 'Net 45'
        )

    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Start New Procurement", use_container_width=True):
        # Clear all session state data
        keys_to_clear = [
            config.S_RFQ_DATA, config.S_QUOTATIONS, config.S_VENDOR_RECOMMENDATION,
            config.S_PURCHASE_ORDER, config.S_CHAT_MESSAGES
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state[config.S_WORKFLOW_STEP] = 1
        st.rerun()


# --- REFACTORED WORKFLOW STEP FUNCTIONS ---

def render_step_1_rfq():
    st.header("💬 Step 1: Generate Request for Quote (RFQ)")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Chat with AI to Define Requirements")
        for message in st.session_state[config.S_CHAT_MESSAGES]:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        if prompt := st.chat_input("Describe your procurement needs..."):
            st.session_state[config.S_CHAT_MESSAGES].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    payload = {
                        "messages": st.session_state[config.S_CHAT_MESSAGES],
                        "company_config": st.session_state[config.S_COMPANY_CONFIG]
                    }
                    response_data = handle_api_request("POST", f"{PROCUREMENT_SERVICE_URL}/chat", json=payload)
                    if response_data:
                        response = response_data.get("response")
                        st.write(response)
                        st.session_state[config.S_CHAT_MESSAGES].append({"role": "assistant", "content": response})

    with col2:
        st.subheader("Finalize and Generate")
        requirements_text = st.text_area("Final Requirements Summary:", height=250, placeholder="Summarize the final requirements here...")
        if st.button("🤖 Generate RFQ Document", type="primary", use_container_width=True):
            if requirements_text:
                with st.spinner("Generating RFQ document..."):
                    payload = {
                        "user_requirements": requirements_text,
                        "company_config": st.session_state[config.S_COMPANY_CONFIG]
                    }
                    response_data = handle_api_request("POST", f"{PROCUREMENT_SERVICE_URL}/generate-rfq", json=payload)
                    if response_data:
                        st.session_state[config.S_RFQ_DATA] = {
                            "requirements": requirements_text,
                            "content": response_data.get("content"),
                            "generated_at": datetime.now().isoformat()
                        }
                        st.success("RFQ Generated!")
            else:
                st.error("Please provide a summary of requirements.")

    if st.session_state[config.S_RFQ_DATA]:
        st.subheader("Generated RFQ")
        with st.expander("View RFQ Content", expanded=False):
            st.json(st.session_state[config.S_RFQ_DATA].get("content", "{}"))

        payload = {
            "content": st.session_state[config.S_RFQ_DATA],
            "title": "Procurement Request",
            "doc_type": "RFQ"
        }
        pdf_buffer = handle_api_request("POST", f"{PDF_SERVICE_URL}/generate-standard-pdf", json=payload)
        if pdf_buffer:
            st.download_button(label="📄 Download RFQ as PDF", data=pdf_buffer, file_name=f"RFQ_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf", use_container_width=True)

def render_step_2_upload_quotations():
    st.header("📄 Step 2: Upload and Extract Quotations")
    uploaded_files = st.file_uploader("Upload vendor quotation files (PDF, PNG, JPG)", type=["pdf", "png", "jpg", "jpeg"], accept_multiple_files=True)
    if uploaded_files:
        for uploaded_file in uploaded_files:
            vendor_name = st.text_input(f"Vendor Name for `{uploaded_file.name}`", key=f"vendor_{uploaded_file.name}")
            if vendor_name and st.button(f"Extract from {uploaded_file.name}", key=f"extract_{uploaded_file.name}"):
                with st.spinner(f"Extracting data from {vendor_name}'s quote..."):
                    files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    data = {'vendor_name': vendor_name}
                    extracted_data = handle_api_request("POST", f"{DATA_EXTRACTION_URL}/extract-quotation", files=files, data=data)
                    if extracted_data:
                        st.session_state[config.S_QUOTATIONS][vendor_name] = extracted_data
                        st.success(f"Successfully extracted data for {vendor_name}!")
                        st.rerun()

    if st.session_state[config.S_QUOTATIONS]:
        st.subheader("Extracted Quotations")
        for vendor, data in st.session_state[config.S_QUOTATIONS].items():
            with st.expander(f"📋 {vendor} - Summary"):
                st.json(data)

def render_step_3_vendor_analysis():
    st.header("🔍 Step 3: AI-Powered Vendor Analysis")
    if not st.session_state[config.S_QUOTATIONS]:
        st.warning("Please upload and extract quotations in Step 2.")
        return

    if st.button("🤖 Analyze Vendors with AI", type="primary", use_container_width=True):
        with st.spinner("AI is analyzing vendor quotes..."):
            # First, get the detailed analysis
            analysis_payload = {"quotations_data": st.session_state[config.S_QUOTATIONS]}
            analysis_data = handle_api_request("POST", f"{PROCUREMENT_SERVICE_URL}/analyze-quotes", json=analysis_payload)
            if analysis_data:
                analysis_json = analysis_data.get('analysis')
                # Then, get the summary from the analysis
                summary_payload = {"analysis_text": analysis_json}
                summary_data = handle_api_request("POST", f"{PROCUREMENT_SERVICE_URL}/extract-summary", json=summary_payload)
                if summary_data:
                    st.session_state[config.S_VENDOR_RECOMMENDATION] = {
                        "analysis": analysis_json,
                        "summary": summary_data.get('summary')
                    }
                    st.success("Analysis complete!")

    if st.session_state[config.S_VENDOR_RECOMMENDATION]:
        st.subheader("🎯 Final Recommendation")
        st.info(st.session_state[config.S_VENDOR_RECOMMENDATION].get("summary", "No summary."))
        with st.expander("View Detailed Analysis Report"):
            st.text_area("Full AI Analysis:", st.session_state[config.S_VENDOR_RECOMMENDATION].get("analysis", ""), height=300)

        payload = {"quotations_data": st.session_state[config.S_QUOTATIONS]}
        pdf_buffer = handle_api_request("POST", f"{PDF_SERVICE_URL}/generate-comparison-pdf", json=payload)
        if pdf_buffer:
            st.download_button(label="📊 Download Comparison as PDF", data=pdf_buffer, file_name="Vendor_Comparison.pdf", mime="application/pdf", use_container_width=True)


def render_step_4_purchase_order():
    st.header("📋 Step 4: Generate Purchase Order")
    if not st.session_state[config.S_VENDOR_RECOMMENDATION]:
        st.warning("Please analyze vendors in Step 3.")
        return
    vendors = list(st.session_state[config.S_QUOTATIONS].keys())
    selected_vendor = st.selectbox("Select a vendor for the Purchase Order:", vendors)
    if st.button(f"Generate PO for {selected_vendor}", type="primary", use_container_width=True):
        with st.spinner(f"Generating Purchase Order for {selected_vendor}..."):
            payload = {
                "rfq_data": st.session_state[config.S_RFQ_DATA],
                "selected_vendor": selected_vendor,
                "recommendation_data": st.session_state[config.S_VENDOR_RECOMMENDATION],
                "company_config": st.session_state[config.S_COMPANY_CONFIG]
            }
            po_data = handle_api_request("POST", f"{PROCUREMENT_SERVICE_URL}/generate-po", json=payload)
            if po_data:
                st.session_state[config.S_PURCHASE_ORDER] = {
                    "vendor": selected_vendor,
                    "content": po_data.get('content'),
                    "generated_at": datetime.now().isoformat()
                }
                st.success("Purchase Order generated!")

    if st.session_state[config.S_PURCHASE_ORDER]:
        st.subheader("Generated Purchase Order")
        with st.expander("View PO Content"):
            st.text_area("PO JSON Content", st.session_state[config.S_PURCHASE_ORDER].get("content", ""), height=300)
        
        payload = {
            "content": st.session_state[config.S_PURCHASE_ORDER],
            "title": f"PO for {st.session_state[config.S_PURCHASE_ORDER]['vendor']}",
            "doc_type": "Purchase Order"
        }
        pdf_buffer = handle_api_request("POST", f"{PDF_SERVICE_URL}/generate-standard-pdf", json=payload)
        if pdf_buffer:
            st.download_button(label="📄 Download PO as PDF", data=pdf_buffer, file_name=f"PO_{st.session_state[config.S_PURCHASE_ORDER]['vendor']}.pdf", mime="application/pdf", use_container_width=True)

def render_step_5_export():
    """Renders the UI for Step 5: Export & Integration with enhanced webhook."""
    st.header("📤 Step 5: Export & Integration")

    st.subheader("Export All Data")
    complete_data = {
        "rfq": st.session_state.get(config.S_RFQ_DATA, {}),
        "quotations": st.session_state.get(config.S_QUOTATIONS, {}),
        "analysis": st.session_state.get(config.S_VENDOR_RECOMMENDATION, {}),
        "purchase_order": st.session_state.get(config.S_PURCHASE_ORDER, {}),
        "exported_at": datetime.now().isoformat()
    }
    st.download_button(
        label="📦 Download All Data as JSON",
        data=json.dumps(complete_data, indent=2),
        file_name=f"procurement_data_{datetime.now().strftime('%Y%m%d')}.json",
        mime="application/json",
        use_container_width=True
    )

    st.markdown("---")
    st.subheader("🔗 Webhook Integration")

    # Helper link to create a Beeceptor endpoint
    st.markdown(
        'For testing, you can create a free webhook endpoint at <a href="https://beeceptor.com/webhook-integration/" target="_blank">Beeceptor</a>.',
        unsafe_allow_html=True
    )
    webhook_url = st.text_input("Webhook URL:", placeholder="https://your-endpoint.beeceptor.com")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📡 Send Full Data to Webhook", use_container_width=True):
            if webhook_url:
                with st.spinner("Sending data..."):
                    result = send_to_webhook(complete_data, webhook_url)
                    if result["success"]:
                        st.success(f"✅ Data sent! Status: {result['status_code']}")
                    else:
                        st.error(f"❌ Failed to send data: {result['error']}")
            else:
                st.warning("Please enter a webhook URL.")

    with col2:
        if st.button("🧪 Test Webhook", use_container_width=True):
            if webhook_url:
                test_data = {"test": True, "message": "Webhook test successful!", "timestamp": datetime.now().isoformat()}
                with st.spinner("Sending test..."):
                    result = send_to_webhook(test_data, webhook_url)
                    if result["success"]:
                        st.success("✅ Webhook test successful!")
                    else:
                        st.error(f"❌ Webhook test failed: {result['error']}")
            else:
                st.warning("Please enter a webhook URL to test.")