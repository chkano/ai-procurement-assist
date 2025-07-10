import os
import json
import requests
import tempfile
from fastapi import FastAPI, HTTPException, UploadFile, File, Form

app = FastAPI(
    title="Data Extraction Service",
    description="Extracts structured data from documents using AgentQL.",
)

AGENTQL_API_KEY = os.getenv("AGENTQL_API_KEY")
if not AGENTQL_API_KEY:
    raise RuntimeError("AGENTQL_API_KEY environment variable is not set.")

@app.post("/extract-quotation", summary="Extract Data from a Quotation File")
async def extract_quotation_data(
    vendor_name: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        # Save uploaded file to a temporary path
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        url = "https://api.agentql.com/v1/query-document"
        headers = {"X-API-Key": AGENTQL_API_KEY}
        
        # AgentQL query
        query_body = {
            "query": """{
                vendor_info { vendor_name contact_info address }
                quote_details { quote_number date valid_until }
                items[] { description quantity unit_price total_price specifications }
                totals { subtotal tax shipping total }
                terms { payment_terms delivery_time warranty }
            }""",
            "params": {"mode": "standard"}
        }

        with open(tmp_path, 'rb') as f:
            files_to_send = {
                'file': (file.filename, f, file.content_type),
                'body': (None, json.dumps(query_body))
            }
            response = requests.post(url, headers=headers, files=files_to_send, timeout=120)
        
        os.unlink(tmp_path) # Clean up the temp file

        if response.status_code == 200:
            result = response.json()
            if 'data' in result:
                extracted_data = result['data']
                extracted_data['vendor_name'] = vendor_name
                extracted_data['file_name'] = file.filename
                return extracted_data
            else:
                raise HTTPException(status_code=422, detail=f"API success, but no data extracted. Response: {response.text}")
        else:
            raise HTTPException(status_code=response.status_code, detail=f"AgentQL API Error: {response.text}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during extraction: {str(e)}")