import base64
import json
import os
from openai import OpenAI
from dataclasses import dataclass
import httpx


@dataclass
class NameplateFields:
    brand: str = ""
    model_number: str = ""
    serial_number: str = ""
    subtype: str = ""
    raw_text: str = ""
    needs_human_review: bool = False
    review_reason: str = ""


os.environ["REQUESTS_CA_BUNDLE"] = r"C:\Users\bishes\Downloads\jea_root.pem.cer"


def load_api_key(filepath: str = r"C:\Users\bishes\Downloads/ella_api_key.txt") -> str:
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"❌ API key file not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        api_key = f.read().strip()
    if not api_key:
        raise ValueError("❌ API key file is empty. Please add your OpenAI API key.")
    return api_key  


API_KEY = load_api_key()
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}
API_URL = "https://api.openai.com/v1/responses"

client = OpenAI(api_key=load_api_key(), http_client=httpx.Client(verify=r"C:\Users\bishes\Downloads\jea_root.pem.cer"))


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def process_nameplate(image_path: str) -> NameplateFields:
    image = encode_image(image_path)

    response = client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """
You are reading an HVAC or water heater equipment nameplate.

Extract the following fields:

- brand
- model_number
- serial_number
- subtype
- raw_text
- needs_human_review
- review_reason

Return ONLY valid JSON in this format:

{
    "brand": "",
    "model_number": "",
    "serial_number": "",
    "subtype": "",
    "raw_text": "",
    "needs_human_review": true
    "review_reason": ""
}

If needs_human_review is true, explain specifically why in review_reason.
Examples include unreadable serial number, missing model number, unclear subtype,
or conflicting text on the nameplate.
If review is not needed, return an empty review_reason.
"""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image}"
                        }
                    }
                ]
            }
        ],
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    print(content)

    if content is None:
        return NameplateFields(
            brand="",
            model_number="",
            serial_number="",
            subtype="",
            raw_text="No response returned by OpenAI.",
            needs_human_review=True,
        )

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return NameplateFields(
            raw_text=content,
            needs_human_review=True,
        )

    if not isinstance(parsed, dict):
        return NameplateFields(
            raw_text=content,
            needs_human_review=True,
        )

    data: dict[str, object] = parsed

    return NameplateFields(
        brand=str(data.get("brand", "")),
        model_number=str(data.get("model_number", "")),
        serial_number=str(data.get("serial_number", "")),
        subtype=str(data.get("subtype", "")),
        raw_text=str(data.get("raw_text", "")),
        needs_human_review=bool(data.get("needs_human_review", True)),
        review_reason=str(data.get("review_reason", "")),
    )