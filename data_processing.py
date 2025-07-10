import requests
import tempfile
import os
import json
from config import AGENTQL_API_KEY

def extract_quotation_data(uploaded_file, vendor_name):
    """Extract quotation data using AgentQL REST API"""
    if not AGENTQL_API_KEY:
        return {"error": "AgentQL API key not found. Please set it in .streamlit/secrets.toml"}

    try:
        # Create a temporary file to hold the uploaded content
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{uploaded_file.name.split(".")[-1]}') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        url = "https://api.agentql.com/v1/query-document"
        headers = {"X-API-Key": AGENTQL_API_KEY}

        with open(tmp_path, 'rb') as file:
            files = {
                'file': (uploaded_file.name, file, uploaded_file.type),
                'body': (None, json.dumps({
                    "query": """{
                        vendor_info { vendor_name contact_info address }
                        quote_details { quote_number date valid_until }
                        items[] { description quantity unit_price total_price specifications }
                        totals { subtotal tax shipping total }
                        terms { payment_terms delivery_time warranty }
                    }""",
                    "params": {"mode": "standard"}
                }))
            }
            response = requests.post(url, headers=headers, files=files, timeout=120)

        os.unlink(tmp_path) # Clean up the temporary file

        if response.status_code == 200:
            result = response.json()
            if 'data' in result:
                extracted_data = result['data']
                # Ensure vendor_name and file_name are included for tracking
                extracted_data['vendor_name'] = vendor_name
                extracted_data['file_name'] = uploaded_file.name
                return extracted_data
            else:
                # Handle cases where the API returns 200 but no data was extracted
                return {"error": f"API returned success, but no data was extracted. Response: {response.text}"}
        else:
            return {"error": f"API Error: {response.status_code} - {response.text}"}

    except Exception as e:
        return {"error": f"An unexpected error occurred during extraction: {str(e)}"}

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
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        return {"success": True, "status_code": response.status_code, "response": response.text}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Failed to send data: {str(e)}"}