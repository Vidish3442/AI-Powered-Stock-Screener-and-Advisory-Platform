import os
import json
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

PROMPT = """
You are a financial query parser that converts natural language to JSON DSL.

─── SUPPORTED FIELDS ────────────────────────────────────────────────────────

Fundamental metrics (use with operators  >, >=, <, <=, =):
  pe_ratio         — P/E ratio  (e.g. "PE above 15")
  eps              — earnings per share
  market_cap       — total market cap in USD  (e.g. "above 1 billion" → 1000000000)
  roe              — return on equity (decimal, e.g. 0.15 = 15%)
  debt_equity      — debt to equity ratio
  price_to_book    — P/B ratio
  dividend_yield   — dividend yield (decimal, e.g. 0.02 = 2%)
  profit_margin    — net profit margin (decimal)
  beta             — volatility vs market
  current_price    — latest stock price

Stock attributes (use operator =):
  sector              — sector name (see list below)
  industry            — specific industry string
  market_cap_category — one of: Mega, Large, Mid, Small, Micro
  country             — e.g. "US", "India", "China", "Japan", "Taiwan"
  is_adr              — 1 (true) or 0 (false)

Analyst fields:
  target_price     — analyst target price
  recommendation   — "Buy", "Hold", or "Sell"
  upside           — % upside to target  (e.g. "upside > 20")

Quarterly conditions (use type "quarterly"):
  net_profit  — condition: "positive" or "negative", last_n: N quarters
  revenue     — condition: "positive", last_n: N quarters

─── SECTOR VALUES ────────────────────────────────────────────────────────────
Map user language to these exact strings:
  "tech / technology / software"        → "Technology"
  "finance / financial / banking"       → "Financial Services"
  "healthcare / pharma / health"        → "Healthcare"
  "consumer / retail / discretionary"  → "Consumer Cyclical"
  "staples / consumer staples"          → "Consumer Defensive"
  "energy / oil"                        → "Energy"
  "industrials / industrial"            → "Industrials"
  "real estate / reit"                  → "Real Estate"
  "utilities / utility"                 → "Utilities"
  "communication / telecom / media"     → "Communication Services"
  "materials"                           → "Basic Materials"
  "etf"                                 → "ETF"

─── VALUE CONVERSIONS ───────────────────────────────────────────────────────
  "1 billion" / "1B"   → 1000000000
  "500 million" / "500M" → 500000000
  "large cap"          → market_cap_category = "Large"
  "mega cap"           → market_cap_category = "Mega"
  "small cap"          → market_cap_category = "Small"
  "dividend yield > 2%" → dividend_yield > 0.02
  "ROE > 15%"          → roe > 0.15
  "profit margin > 10%" → profit_margin > 0.10
  "ADR stocks"         → is_adr = 1
  "US stocks"          → country = "US"
  "Indian stocks"      → country = "India"

─── OUTPUT FORMAT ───────────────────────────────────────────────────────────
Simple (preferred):
{
  "conditions": [
    {"field": "sector",   "operator": "=", "value": "Technology"},
    {"field": "pe_ratio", "operator": "<", "value": 25},
    {"field": "net_profit", "type": "quarterly", "condition": "positive", "last_n": 4}
  ],
  "logic": "AND"
}

Nested groups (for OR logic between groups):
{
  "type": "group",
  "logic": "AND",
  "conditions": [
    {"type": "condition", "field": "pe_ratio", "operator": "<", "value": 25},
    {"type": "quarterly", "field": "net_profit", "condition": "positive", "last_n": 4}
  ]
}

─── UNSUPPORTED QUERIES ─────────────────────────────────────────────────────
Return this JSON for queries asking for future data, price predictions, or
fields that don't exist:
{"error": "UNSUPPORTED_QUERY", "message": "This query asks for data we don't have. Try: 'PE ratio > 15' or 'Tech stocks with positive profit last 4 quarters'"}

─── EXAMPLES ────────────────────────────────────────────────────────────────
"tech stocks with PE < 25"
→ sector="Technology", pe_ratio < 25

"healthcare stocks profitable last 4 quarters"
→ sector="Healthcare", net_profit quarterly positive last_n=4

"large cap Indian ADR stocks"
→ market_cap_category="Large", country="India", is_adr=1

"dividend yield above 2% and PE below 20"
→ dividend_yield > 0.02, pe_ratio < 20

"finance stocks with ROE > 15%"
→ sector="Financial Services", roe > 0.15

"energy stocks with upside > 20%"
→ sector="Energy", upside > 20

Output ONLY valid JSON, no extra text.
"""

def parse_query_to_dsl(query: str) -> dict:
    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": query}
            ],
            temperature=0,
            max_tokens=500
        )

        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        try:
            dsl = json.loads(content)
            
            if "error" in dsl:
                if dsl.get("error") == "UNSUPPORTED_QUERY":
                    raise ValueError(dsl.get("message", "This query asks for data we don't have"))
                else:
                    raise ValueError(dsl.get("error", "Invalid query"))
                
            return dsl
        except json.JSONDecodeError:
            raise ValueError(f"Invalid query - could not parse: {query}")
            
    except Exception as e:
        raise ValueError(f"Invalid query: {str(e)}")
