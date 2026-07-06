import base64
import json
import os
from openai import OpenAI
from dataclasses import dataclass
from dotenv import load_dotenv
import httpx

load_dotenv()


def load_api_key(filepath: str = "C:/Users/bishes/Downloads/ella_api_key.txt")  -> str:
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"❌ API key file not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        api_key = f.read().strip()
    if not api_key:
        raise ValueError("❌ API key file is empty. Please add your OpenAI API key.")
    print("Loading API key from:", filepath)
    print("Exists:", os.path.isfile(filepath))
    return api_key   


CERT_PATH = r"C:\Users\bishes\Downloads\openai-ca.pem"


client = OpenAI(api_key=load_api_key(), http_client=httpx.Client(verify=CERT_PATH),)


@dataclass
class NameplateFields:
    brand: str = ""
    model_number: str = ""
    serial_number: str = ""
    subtype: str = ""
    raw_text: str = ""
    needs_human_review: bool = False
     

def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def process_nameplate(image_path: str) -> NameplateFields:
    image = encode_image(image_path)

    response = client.chat.completions.create(
        model="gpt-5.4-mini-2026-03-17",
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

Subtype must be exactly one of:

- Air Conditioner
- Heat Pump
- Furnace
- Air Handler
- Tank
- Tankless

If any value cannot be confidently determined, leave it blank and set
needs_human_review to true.

Return ONLY valid JSON in this format:

{
    "brand": "",
    "model_number": "",
    "serial_number": "",
    "subtype": "",
    "raw_text": "",
    "needs_human_review": true
}
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

    if content is None:
        return NameplateFields(
            needs_human_review=True,
            raw_text="No response returned by OpenAI."
        )

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return NameplateFields(
            raw_text=content,
            needs_human_review=True
        )

    return NameplateFields(
        brand=data.get("brand", ""),
        model_number=data.get("model_number", ""),
        serial_number=data.get("serial_number", ""),
        subtype=data.get("subtype", ""),
        raw_text=data.get("raw_text", ""),
        needs_human_review=bool(data.get("needs_human_review", True)),
    )