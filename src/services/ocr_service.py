"""
This module is responsible for extracting structured appliance information
from uploaded nameplate images using the OpenAI Vision API.

The rest of ApplianceIQ never performs OCR directly. Instead, it calls
`process_nameplate()` with the raw bytes of an uploaded image. This module
handles:

    1. Loading the OpenAI API key
    2. Encoding the image into Base64
    3. Sending the image to GPT Vision
    4. Prompting the model to extract appliance information
    5. Parsing the JSON response
    6. Returning strongly typed data to the caller

The returned NameplateFields object is then used by the appliance-specific
analysis services to determine equipment age, replacement recommendations,
and whether a human review is required.

Workflow
--------
Uploaded image
        │
        ▼
process_nameplate(image_bytes)
        │
        ▼
encode_image()
        │
        ▼
GPT Vision API
        │
        ▼
Structured JSON response
        │
        ▼
NameplateFields dataclass
        │
        ▼
HVAC / Water Heater analysis services

This module intentionally contains no business logic such as equipment age
decoding or replacement recommendations. Its only responsibility is OCR and
field extraction.
"""
from openai import OpenAI
from dataclasses import dataclass
import base64
import json
import httpx
import os
from dotenv import load_dotenv

load_dotenv()


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


def load_api_key() -> str:
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise RuntimeError(
            "API_KEY environment variable is missing."
        )
    return api_key


API_KEY = load_api_key()

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}
API_URL = "https://api.openai.com/v1/responses"


client = OpenAI(api_key=load_api_key(), http_client=httpx.Client(verify=r"C:\Users\bishes\Downloads\jea_root.pem.cer"))


def encode_image(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def process_nameplate(image_bytes: bytes) -> NameplateFields:
    image_base64 = encode_image(image_bytes)

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
                            "url": f"data:image/jpeg;base64,{image_base64}"
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