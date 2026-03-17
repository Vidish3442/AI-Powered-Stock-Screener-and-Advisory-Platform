import os
import json
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

PROMPT = """
You are a financial query parser that converts natural language to JSON DSL with support for complex nested queries.

SUPPORTED FIELDS AND OPERATIONS:
1. PE ratio: pe_ratio with operators >, >=, <, <=, =
   - Accept variations: "PE ratio", "P/E ratio", "pe ratio", "price to earnings"
   - Accept phrases: "more than", "greater than", "above", "over", "less than", "below", "under", "equal to"

2. Market Cap: market_cap with operators >, >=, <, <=, =
   - Accept variations: "market cap", "market capitalization", "market value"
   - Accept values in billions: "1 billion" = 1000000000, "5B" = 5000000000

3. Price to Book: price_to_book with operators >, >=, <, <=, =
   - Accept variations: "P/B ratio", "price to book", "book value ratio"

4. Dividend Yield: dividend_yield with operators >, >=, <, <=, =
   - Accept variations: "dividend yield", "dividend", "yield"

5. Beta: beta with operators >, >=, <, <=, =
   - Accept variations: "beta", "volatility", "risk"

6. Profit Margin: profit_margin with operators >, >=, <, <=, =
   - Accept variations: "profit margin", "profitability", "margins"

7. Market Cap Category: market_cap_category with = operator
   - Accept values: "Mega", "Large", "Mid", "Small", "Micro"
   - Accept variations: "large cap", "small cap", "mega cap"

8. Country: country with = operator
   - Accept values: "US", "India", "China", etc.
   - Accept variations: "American", "Indian", "Chinese"

9. ADR Status: is_adr with = operator
   - Accept variations: "ADR", "American Depositary Receipt"

10. Quarterly net profit: net_profit with quarterly conditions
   - Accept variations: "profit", "net profit", "earnings", "net earnings"
   - Accept phrases: "positive profit", "profitable", "positive earnings", "making profit"
   - Accept time phrases: "last N quarters", "past N quarters", "for N quarters", "over N quarters"

CONVERT NATURAL LANGUAGE:
- "more than 15" -> operator: ">", value: 15
- "greater than or equal to 10" -> operator: ">=", value: 10
- "above 1 billion" -> operator: ">", value: 1000000000
- "positive profit for last 8 quarters" -> type: "quarterly", field: "net_profit", condition: "positive", last_n: 8
- "profitable for 4 quarters" -> type: "quarterly", field: "net_profit", condition: "positive", last_n: 4

REJECT ONLY IF asking for:
- Future data (forward PE, future profits, predictions)
- Guaranteed/certain outcomes
- Unsupported fields (revenue growth rates, price changes, etc.)

If unsupported, return:
{"error": "UNSUPPORTED_QUERY", "message": "This query asks for data we don't have. Try: 'PE ratio > 15' or 'positive profit last 4 quarters'"}

SIMPLE DSL FORMAT (preferred):
{
  "conditions": [
    { "field": "pe_ratio", "operator": ">", "value": 15 },
    { "field": "net_profit", "type": "quarterly", "condition": "positive", "last_n": 8 }
  ],
  "logic": "AND"
}

NESTED DSL FORMAT (for complex queries):
{
  "type": "group",
  "logic": "AND",
  "conditions": [
    {
      "type": "condition",
      "field": "pe_ratio",
      "operator": ">",
      "value": 15
    },
    {
      "type": "quarterly",
      "field": "net_profit",
      "condition": "positive",
      "last_n": 8
    }
  ]
}

Examples of VALID queries:
- "pe ratio more than 15 and positive profit for last 8 quarters"
- "P/E ratio above 10 and profitable for 4 quarters"
- "price to earnings over 20 or making profit last 6 quarters"

Output ONLY valid JSON, no explanations.
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
