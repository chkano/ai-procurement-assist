import openai
import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any

# Assuming prompts.py is in the same directory
import prompts

# --- Configuration & Initialization ---
app = FastAPI(
    title="Procurement Logic Service",
    description="Handles core procurement logic using OpenAI.",
)

# It's better to fetch the API key once at startup
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable is not set.")

openai.api_key = OPENAI_API_KEY

# --- Pydantic Models for Request Bodies ---
class CallOpenAIRequest(BaseModel):
    system_content: str
    user_content: str
    model: str = "gpt-4"
    temperature: float = 0.5

class RFQRequest(BaseModel):
    user_requirements: str
    company_config: Dict[str, Any]

class AnalysisRequest(BaseModel):
    quotations_data: Dict[str, Any]

class SummaryRequest(BaseModel):
    analysis_text: str

class PORequest(BaseModel):
    rfq_data: Dict[str, Any]
    selected_vendor: str
    recommendation_data: Dict[str, Any]
    company_config: Dict[str, Any]

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    company_config: Dict[str, Any]

# --- Helper Function ---
def _call_openai(system_content: str, user_content: str, model: str = "gpt-4", temperature: float = 0.5) -> str:
    """Generic helper function to call the OpenAI Chat Completions API."""
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content}
            ],
            temperature=temperature
        )
        return response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with OpenAI: {str(e)}")

# --- API Endpoints ---
@app.post("/generate-rfq", summary="Generate RFQ Document")
def generate_rfq_endpoint(request: RFQRequest):
    prompt = prompts.get_rfq_prompt(request.user_requirements, request.company_config)
    system_prompt = "You are a professional procurement specialist generating detailed RFQ documents as JSON."
    return {"content": _call_openai(system_prompt, prompt, temperature=0.7)}

@app.post("/analyze-quotes", summary="Analyze Vendor Quotations")
def analyze_quotes_endpoint(request: AnalysisRequest):
    prompt = prompts.get_vendor_analysis_prompt(request.quotations_data)
    system_prompt = "You are an expert procurement analyst. Provide thorough, objective vendor analysis as a JSON object."
    return {"analysis": _call_openai(system_prompt, prompt, temperature=0.3)}

@app.post("/extract-summary", summary="Extract Recommendation Summary")
def extract_summary_endpoint(request: SummaryRequest):
    prompt = prompts.get_recommendation_summary_prompt(request.analysis_text)
    system_prompt = "You are a procurement analyst. Extract the final recommendation summary in both English and Thai."
    return {"summary": _call_openai(system_prompt, prompt, temperature=0.1)}

@app.post("/generate-po", summary="Generate Purchase Order")
def generate_po_endpoint(request: PORequest):
    prompt = prompts.get_purchase_order_prompt(request.rfq_data, request.selected_vendor, request.recommendation_data, request.company_config)
    system_prompt = "You are a procurement specialist creating precise purchase orders as JSON."
    return {"content": _call_openai(system_prompt, prompt, temperature=0.2)}

@app.post("/chat", summary="Get Chatbot Response")
def chat_endpoint(request: ChatRequest):
    system_prompt = "You are a procurement specialist helping to gather requirements for an RFQ. Ask clarifying questions and provide professional advice. Respond in both Thai and English when appropriate."
    company_name = request.company_config.get('company_name')
    if company_name:
        system_prompt += f" You are working for {company_name}."

    try:
        full_messages = [{"role": "system", "content": system_prompt}] + request.messages
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=full_messages,
            temperature=0.7
        )
        return {"response": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in chat communication: {str(e)}")