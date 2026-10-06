import json
import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"


SYSTEM_PROMPT = """
You are a Consumer Product Decision Interpreter.

Your job is to analyze the product information provided to you and help a
consumer understand what the product information means.

You are NOT a salesperson. Do not persuade the consumer to buy the product.

IMPORTANT RULES:

1. Use ONLY information provided about the product.
2. Never invent product facts.
3. Never invent specifications, ingredients, nutrition, materials,
   certifications, warranty information, safety information, compatibility,
   performance, sizing, or medical effects.
4. Clearly distinguish between:
   - verified facts from the product data
   - reasonable interpretation of those facts
   - considerations the consumer may want to think about
5. Explain technical information in simple language.
6. Analyze the ACTUAL product you receive. Do not use a fixed category-specific
   template.
7. Only discuss attributes that are actually relevant to the product.
8. If useful, explain practical consequences of a specification.
9. Mention trade-offs only when they can reasonably be supported by the
   supplied information.
10. If important information is missing, explicitly say that it was not
    provided.
11. Missing information must NOT automatically be treated as a negative.
12. For food and supplements, remain neutral and do not make medical claims.
13. Do not tell the consumer whether they should buy the product.
14. The final answer should help the consumer make their own decision.

Return ONLY valid JSON.

The JSON must have this structure:

{
  "product_name": "string",
  "summary": "string",
  "facts": [
    {
      "attribute": "string",
      "value": "string",
      "meaning": "string",
      "implication": "string",
      "source": "string",
      "confidence": "high"
    }
  ],
  "comparisons": [
    {
      "title": "string",
      "comparison": "string"
    }
  ],
  "comparison_title": "string",
  "tradeoffs": [
    "string"
  ],
  "considerations": [
    "string"
  ],
  "missing_information": [
    "string"
  ],
  "bottom_line": "string"
}

Use empty arrays when a section is not useful.

Confidence must be one of:
"high", "medium", "low".

Do not put information into the JSON that was not supported by the supplied
product data.
"""


def serialize_product(product):
    """
    Convert the database Product object into plain JSON-like data
    that can safely be sent to the local AI model.
    """

    attributes = product.attributes or {}

    return {
        "id": str(product.id),
        "name": product.name,
        "category": product.category,
        "brand": getattr(product, "brand", None),
        "price": getattr(product, "price", None),
        "description": getattr(product, "description", None),
        "attributes": attributes,
    }


def call_ollama(product_data):
    """
    Send the actual product data to the locally running Ollama model.
    """

    user_prompt = f"""
Analyze this product:

{json.dumps(product_data, indent=2, ensure_ascii=False)}

Remember:

- Analyze THIS product specifically.
- Do not assume facts that are not provided.
- Do not use hard-coded category rules.
- Do not invent missing specifications.
- Explain the supplied information in practical, understandable language.
"""

    payload = {
        "model": OLLAMA_MODEL,
        "system": SYSTEM_PROMPT,
        "prompt": user_prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.2
        }
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    result = response.json()

    raw_output = result.get("response", "").strip()

    if not raw_output:
        raise RuntimeError("Ollama returned an empty response.")

    try:
        return json.loads(raw_output)

    except json.JSONDecodeError as exc:
        print("Ollama returned invalid JSON:")
        print(raw_output)

        raise RuntimeError(
            "Ollama returned invalid JSON."
        ) from exc


def normalize_result(result, product):
    """
    Make sure the response always contains the fields expected
    by the existing frontend.
    """

    return {
        "product_name": result.get(
            "product_name",
            product.name
        ),

        "summary": result.get(
            "summary",
            ""
        ),

        "facts": result.get(
            "facts",
            []
        ),

        "comparisons": result.get(
            "comparisons",
            []
        ),

        "comparison_title": result.get(
            "comparison_title",
            ""
        ),

        "tradeoffs": result.get(
            "tradeoffs",
            []
        ),

        "considerations": result.get(
            "considerations",
            []
        ),

        "missing_information": result.get(
            "missing_information",
            []
        ),

        "bottom_line": result.get(
            "bottom_line",
            ""
        )
    }


def interpret_product(product):
    """
    Main entry point used by the FastAPI route.

    The product is sent to the locally running Llama model,
    which dynamically generates the product insight.
    """

    product_data = serialize_product(product)

    result = call_ollama(product_data)

    return normalize_result(result, product)