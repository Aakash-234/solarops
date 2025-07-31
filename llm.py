# llm_helper.py

import json
from openai import OpenAI
from config import OPENAI_API_KEY
import textwrap

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def extract_fields_llm(text: str):
    """
    Given OCR text from a solar/battery installation, extract exactly
    the fields needed for validation and return them as JSON.
    """
    schema = {
        "customer_name": "",
        "customer_address": "",
        "utility_account_number": "",
        "system_capacity_kw": "",
        "panel_serial_numbers": [],
        "inverter_serial_number": "",
        "battery_serial_numbers": [],
        "install_date": "",
        "rebate_amount": "",
        "contract_signed": True,
        "inspector_notes": ""
    }

    prompt = textwrap.dedent(f"""
        You are an AI assistant that automates document validation for solar and battery installers.
        Analysts check each submission against this checklist:

        1. Customer full name
        2. Customer mailing address
        3. Utility account or meter number
        4. Total system capacity in kW
        5. All panel serial numbers (array)
        6. Inverter serial number
        7. Any battery serial numbers (array)
        8. Installation date (DD/MM/YYYY)
        9. Rebate or loan amount (numeric only)
        10. Contract signed? (true/false)
        11. Any inspector notes or exceptions

        Below is the raw OCR text. Output ONLY a single JSON object matching this schema (no extra text):

        {json.dumps(schema, indent=2)}

        OCR text:
        \"\"\"{text}\"\"\"
    """)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system",
             "content": "You are an expert in solar installation document processing."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        max_tokens=500,
    )

    # Parse the assistant's JSON output
    return json.loads(response.choices[0].message.content)
