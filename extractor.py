import re
def extract_fields(text: str):
    fields = {}

    # 1️⃣ Customer name (assume they always use "Name: John Doe")
    name_match = re.search(r"Name[:\s]+([A-Za-z ]+)", text)
    if name_match:
        fields["customer_name"] = name_match.group(1).strip()

    # 2️⃣ Customer address (look for "Address: ....")
    address_match = re.search(r"Address[:\s]+(.+)", text)
    if address_match:
        fields["customer_address"] = address_match.group(1).strip()

    # 3️⃣ Utility account number (simple pattern, 8–12 digits)
    utility_match = re.search(r"Utility Account[:\s]+(\d{8,12})", text)
    if utility_match:
        fields["utility_account_number"] = utility_match.group(1)

    # 4️⃣ System capacity (e.g., "5.5 kW")
    kw_match = re.search(r"(\d{1,2}\.\d{1,2})\s*kW", text, re.IGNORECASE)
    if kw_match:
        fields["system_capacity_kw"] = kw_match.group(1)

    # 5️⃣ Panel serial numbers (look for "Panel SN: ABC123456")
    panel_sn = re.findall(r"Panel SN[:\s]+([A-Z0-9\-]+)", text)
    if panel_sn:
        fields["panel_serial_numbers"] = panel_sn

    # 6️⃣ Inverter serial (same style)
    inverter_sn = re.search(r"Inverter SN[:\s]+([A-Z0-9\-]+)", text)
    if inverter_sn:
        fields["inverter_serial_number"] = inverter_sn.group(1)

    # 7️⃣ Install date (e.g., "Install Date: 01/07/2025")
    date_match = re.search(r"Install Date[:\s]+(\d{1,2}/\d{1,2}/\d{4})", text)
    if date_match:
        fields["install_date"] = date_match.group(1)

    # 8️⃣ Amount (e.g., "Rebate Amount: Rs 10,000.00")
    amount_match = re.search(r"Rebate Amount[:\s]+Rs[\s]?([\d,]+\.\d+)", text)
    if amount_match:
        fields["rebate_amount"] = amount_match.group(1)

    # 9️⃣ Look for signature keyword
    if "Customer Signature" in text:
        fields["signature_found"] = True
    else:
        fields["signature_found"] = False

    return fields
