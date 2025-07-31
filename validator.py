def validate_fields(fields):
    result = {"valid": True, "issues": []}

    # Name and address must exist
    if "customer_name" not in fields or not fields["customer_name"]:
        result["valid"] = False
        result["issues"].append("Missing customer name")

    if "customer_address" not in fields or not fields["customer_address"]:
        result["valid"] = False
        result["issues"].append("Missing customer address")

    # Utility account format
    if "utility_account_number" not in fields or not fields["utility_account_number"]:
        result["valid"] = False
        result["issues"].append("Missing utility account number")

    # System size reasonable
    try:
        kw = float(fields.get("system_capacity_kw", 0))
        if not (0.5 <= kw <= 20.0):
            result["valid"] = False
            result["issues"].append(f"System capacity {kw} kW out of range")
    except:
        result["valid"] = False
        result["issues"].append("Invalid or missing system capacity")

    # Must have at least 1 panel SN
    if "panel_serial_numbers" not in fields or not fields["panel_serial_numbers"]:
        result["valid"] = False
        result["issues"].append("No panel serial numbers found")

    # Must have inverter SN
    if "inverter_serial_number" not in fields or not fields["inverter_serial_number"]:
        result["valid"] = False
        result["issues"].append("Missing inverter serial number")

    # Install date required
    if "install_date" not in fields or not fields["install_date"]:
        result["valid"] = False
        result["issues"].append("Missing install date")

    # Signature check
    if not fields.get("signature_found", False):
        result["valid"] = False
        result["issues"].append("Missing customer signature")

    # ✅ Add confidence score — simple heuristic
    base_score = 100
    penalty_per_issue = 10
    score = base_score - len(result["issues"]) * penalty_per_issue
    result["confidence"] = max(score, 0)

    return result
def generate_ai_suggestion(fields, issues):
    """
    Generate a simple suggestion for fixing issues.
    You can later replace this with an LLM call.
    """
    suggestions = []
    for issue in issues:
        if "customer name" in issue.lower():
            suggestions.append("Verify customer name field.")
        elif "address" in issue.lower():
            suggestions.append("Ensure full customer address is present.")
        elif "utility" in issue.lower():
            suggestions.append("Add valid utility account number.")
        elif "panel serial" in issue.lower():
            suggestions.append("Attach correct panel serial numbers.")
        else:
            suggestions.append(f"Check: {issue}")
    return " | ".join(suggestions)
