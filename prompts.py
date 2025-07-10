import json

def get_rfq_prompt(user_requirements, company_config):
    """Returns the prompt for generating an RFQ."""
    company_info = f"""
    Company Information:
    - Company Name: {company_config.get('company_name', 'Not specified')}
    - Address: {company_config.get('company_address', 'Not specified')}
    - Contact: {company_config.get('company_contact', 'Not specified')}
    - Phone: {company_config.get('company_phone', 'Not specified')}
    - Default Payment Terms: {company_config.get('default_payment_terms', 'Net 30')}
    """
    return f"""
    Generate a professional Request for Quote (RFQ) document based on the following:
    {company_info}
    Requirements: {user_requirements}
    Please structure the RFQ with clear sections like Project Description,
    Detailed Requirements, Specifications, Delivery Requirements, and Terms.
    Format the response as a structured JSON.
    """

def get_recommendation_summary_prompt(analysis_text):
    """Returns the prompt for summarizing a vendor analysis."""
    return f"""
    From the following vendor analysis, extract ONLY the final recommendation.
    Provide:
    1. Recommended vendor name
    2. Key reasons (max 3 bullet points)
    3. Total cost/price
    Format as a clear, concise summary in both English and Thai.
    Analysis: {analysis_text}
    """

def get_vendor_analysis_prompt(quotations_data):
    """Returns the prompt for analyzing vendor quotations."""
    return f"""
    Analyze the following vendor quotations and provide a comprehensive recommendation.
    Format the entire output as a single JSON object.
    The JSON should include keys like "vendor_comparison", "price_analysis",
    "risk_assessment", and "final_recommendation".
    Quotation Data: {json.dumps(quotations_data, indent=2)}
    """

def get_purchase_order_prompt(rfq_data, selected_vendor, recommendation_data, company_config):
    """Returns the prompt for generating a Purchase Order."""
    company_info = f"""
    Buyer Company Information:
    - Company Name: {company_config.get('company_name', 'Not specified')}
    - Address: {company_config.get('company_address', 'Not specified')}
    - Contact: {company_config.get('company_contact', 'Not specified')}
    """
    return f"""
    Generate a professional Purchase Order as a structured JSON object.
    Use this information:
    {company_info}
    RFQ Data: {json.dumps(rfq_data, indent=2)}
    Selected Vendor: {selected_vendor}
    Include standard PO fields: PO Number, Vendor Info, Buyer Info, Item Details,
    Quantities, Prices, Terms, and Total Amounts.
    """