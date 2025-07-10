import openai
import json

# Import from our other project modules
from config import OPENAI_API_KEY
from prompts import (
    get_rfq_prompt, get_recommendation_summary_prompt,
    get_vendor_analysis_prompt, get_purchase_order_prompt
)

# Initialize the OpenAI client if the key exists
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

def _call_openai(system_content, user_content, model="gpt-4", temperature=0.5):
    """Generic helper function to call the OpenAI Chat Completions API."""
    if not OPENAI_API_KEY:
        return "Error: OpenAI API key is not configured."
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
        return f"Error communicating with OpenAI: {str(e)}"

def generate_rfq_with_openai(user_requirements, company_config):
    """Generate RFQ using OpenAI."""
    prompt = get_rfq_prompt(user_requirements, company_config)
    system_prompt = "You are a professional procurement specialist generating detailed RFQ documents as JSON."
    return _call_openai(system_prompt, prompt, temperature=0.7)

def extract_recommendation_summary(analysis_text):
    """Extract final recommendation from vendor analysis."""
    prompt = get_recommendation_summary_prompt(analysis_text)
    system_prompt = "You are a procurement analyst. Extract the final recommendation summary in both English and Thai."
    return _call_openai(system_prompt, prompt, temperature=0.1)

def analyze_vendor_quotes(quotations_data):
    """Use OpenAI to analyze and recommend the best vendor."""
    prompt = get_vendor_analysis_prompt(quotations_data)
    system_prompt = "You are an expert procurement analyst. Provide thorough, objective vendor analysis as a JSON object."
    return _call_openai(system_prompt, prompt, temperature=0.3)

def generate_purchase_order(rfq_data, selected_vendor, recommendation_data, company_config):
    """Generate purchase order using OpenAI."""
    prompt = get_purchase_order_prompt(rfq_data, selected_vendor, recommendation_data, company_config)
    system_prompt = "You are a procurement specialist creating precise purchase orders as JSON."
    return _call_openai(system_prompt, prompt, temperature=0.2)

def get_chat_response(messages, company_config):
    """Gets a conversational response from OpenAI for the RFQ chatbot."""
    if not OPENAI_API_KEY:
        return "Error: OpenAI API key is not configured."

    system_prompt = "You are a procurement specialist helping to gather requirements for an RFQ. Ask clarifying questions and provide professional advice. Respond in both Thai and English when appropriate."
    company_name = company_config.get('company_name')
    if company_name:
        system_prompt += f" You are working for {company_name}."

    try:
        # The first message is the system prompt, followed by the chat history
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=full_messages,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error communicating with OpenAI: {str(e)}"