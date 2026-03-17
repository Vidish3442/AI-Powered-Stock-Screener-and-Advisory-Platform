ALLOWED_FIELDS = {
    "pe_ratio", "eps", "market_cap", "roe", "debt_equity", 
    "price_to_book", "dividend_yield", "profit_margin", "beta", "current_price",
    "market_cap_category", "country", "is_adr", "sector", "industry",
    "target_price", "recommendation", "upside"
}
ALLOWED_OPERATORS = {">", ">=", "<", "<=", "="}
ALLOWED_QUARTERLY_CONDITIONS = {"positive", "negative"}
ALLOWED_QUARTERLY_FIELDS = {"net_profit", "revenue"}

def validate_dsl(dsl: dict):
    """Recursively validate DSL structure and content."""
    if not isinstance(dsl, dict):
        raise ValueError("DSL must be a dictionary")    
    if dsl.get("type") == "group":
        return validate_group(dsl)
    elif "conditions" in dsl:
        return validate_legacy_format(dsl)
    else:
        raise ValueError("Invalid DSL format")

def validate_group(group: dict, depth: int = 0):
    """Validate a group (nested structure)."""
    if depth > 5:  
        raise ValueError("Query too complex - maximum 5 levels of nesting")
    
    if not isinstance(group.get("conditions"), list):
        raise ValueError("Group must have 'conditions' list")
    
    if len(group["conditions"]) == 0:
        raise ValueError("Group must have at least one condition")
    
    logic = group.get("logic", "AND")
    if logic not in ["AND", "OR"]:
        raise ValueError("Logic must be 'AND' or 'OR'")
    
    for i, item in enumerate(group["conditions"]):
        if not isinstance(item, dict):
            raise ValueError(f"Condition {i} must be a dictionary")
        
        item_type = item.get("type")
        
        if item_type == "condition":
            validate_condition(item, i)
        elif item_type == "quarterly":
            validate_quarterly_condition(item, i)
        elif item_type == "group":
            validate_group(item, depth + 1)
        else:
            raise ValueError(f"Invalid condition type '{item_type}' at position {i}")
    
    return True

def validate_condition(cond: dict, index: int):
    """Validate a simple condition."""
    field = cond.get("field")
    if not field:
        raise ValueError(f"Condition {index} missing 'field'")    
    if field in ALLOWED_QUARTERLY_FIELDS:
        raise ValueError(f"Field '{field}' should use quarterly condition type, not regular condition")
    
    if field not in ALLOWED_FIELDS:
        raise ValueError(f"Invalid field '{field}'. Allowed fields: {', '.join(sorted(ALLOWED_FIELDS))}")
    
    operator = cond.get("operator")
    if operator not in ALLOWED_OPERATORS:
        raise ValueError(f"Invalid operator '{operator}'. Allowed: {', '.join(ALLOWED_OPERATORS)}")
    
    value = cond.get("value")
    if not isinstance(value, (int, float)):
        raise ValueError(f"Condition {index} value must be a number")
    
    if value < 0:
        raise ValueError(f"Condition {index} value must be non-negative")

def validate_quarterly_condition(cond: dict, index: int):
    """Validate a quarterly condition."""
    field = cond.get("field")
    if field not in ALLOWED_QUARTERLY_FIELDS:
        raise ValueError(f"Quarterly conditions only supported for: {', '.join(ALLOWED_QUARTERLY_FIELDS)}")
    
    condition = cond.get("condition")
    if condition not in ALLOWED_QUARTERLY_CONDITIONS:
        raise ValueError(f"Invalid quarterly condition '{condition}'. Allowed: {', '.join(ALLOWED_QUARTERLY_CONDITIONS)}")
    
    last_n = cond.get("last_n")
    if not isinstance(last_n, int) or last_n <= 0:
        raise ValueError("'last_n' must be a positive integer")
    
    if last_n > 20:
        raise ValueError("'last_n' cannot exceed 20 quarters")

def validate_legacy_format(dsl: dict):
    """Validate legacy DSL format for backward compatibility."""
    if not isinstance(dsl["conditions"], list):
        raise ValueError("'conditions' must be a list")
    
    if len(dsl["conditions"]) == 0:
        raise ValueError("At least one condition is required")

    for i, cond in enumerate(dsl["conditions"]):
        if not isinstance(cond, dict):
            raise ValueError(f"Condition {i} must be a dictionary")
        
        if cond.get("type") == "quarterly":
            validate_quarterly_condition(cond, i)
            continue
        
        field = cond.get("field")
        if not field:
            raise ValueError(f"Condition {i} missing 'field'")
        
        if field in ALLOWED_QUARTERLY_FIELDS:
            if "type" not in cond:
                raise ValueError(f"Field '{field}' requires 'type': 'quarterly'")
            continue
        
        if field not in ALLOWED_FIELDS:
            raise ValueError(f"Invalid field '{field}'. Allowed fields: {', '.join(sorted(ALLOWED_FIELDS))}")

        if "operator" in cond:
            operator = cond.get("operator")
            if operator not in ALLOWED_OPERATORS:
                raise ValueError(f"Invalid operator '{operator}'. Allowed: {', '.join(ALLOWED_OPERATORS)}")
            
            value = cond.get("value")
            if not isinstance(value, (int, float)):
                raise ValueError(f"Condition {i} value must be a number")
            
            if value < 0:
                raise ValueError(f"Condition {i} value must be non-negative")
        else:
            raise ValueError(f"Condition {i} must have 'operator'")
    
    logic = dsl.get("logic", "AND")
    if logic not in ["AND", "OR"]:
        raise ValueError("Logic must be 'AND' or 'OR'")
    
    return True
