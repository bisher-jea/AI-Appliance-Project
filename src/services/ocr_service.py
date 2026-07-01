from openai import OpenAI
import base64
import json
import os
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


@dataclass
class NameplateFields:
    brand: str = ""
    model_number: str = ""
    serial_number: str = ""
    subtype: str = ""
    raw_text: str = ""
    needs_human_review: bool = False


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def process_nameplate(image_path: str) -> NameplateFields:
    image = encode_image(image_path)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """
You are reading an HVAC or water heater equipment nameplate.

Extract:
- brand
- model_number
- serial_number
- subtype
- raw_text
- needs_human_review

Subtype must be one of:
Air Conditioner
Heat Pump
Furnace
Air Handler
Tank
Tankless

Return ONLY valid JSON.
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
            raw_text="OpenAI returned no content."
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
        needs_human_review=data.get("needs_human_review", True),
    )