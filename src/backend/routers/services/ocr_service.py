from typing import Any
import re
import cv2
from cv2.typing import MatLike
from doctr.io import DocumentFile
from doctr.models import ocr_predictor

from backend.schema import HVACAnalysis, WaterHeaterAnalysis


OCR_MODEL = ocr_predictor(
    det_arch="db_resnet50",
    reco_arch="crnn_vgg16_bn",
    pretrained=True,
    assume_straight_pages=True
)


def preprocess_image(image_path: str) -> str:
    image: MatLike | None = cv2.imread(image_path)

    if image is None:
        raise ValueError(f"Could not read image: {image_path}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    gray = cv2.resize(
        gray,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_CUBIC
    )

    gray = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    output_path = image_path.replace(".", "_processed.")
    cv2.imwrite(output_path, gray)

    return output_path


def run_ocr(image_path: str) -> str:
    processed_path = preprocess_image(image_path)

    doc = DocumentFile.from_images(processed_path)
    result = OCR_MODEL(doc)
    exported = result.export()

    extracted_lines: list[str] = []

    for page in exported["pages"]:
        for block in page["blocks"]:
            for line in block["lines"]:
                words = [word["value"] for word in line["words"]]
                extracted_lines.append(" ".join(words))

    return "\n".join(extracted_lines)


def extract_nameplate_fields(raw_text: str) -> dict[str, Any]:
    text = raw_text.upper()

    model_patterns = [
        r"MODEL(?:\sNO\.?|\sNUMBER)?[:\s#-]*([A-Z0-9\-\.]+)",
        r"M\/N[:\s#-]*([A-Z0-9\-\.]+)",
        r"MOD(?:EL)?[:\s#-]*([A-Z0-9\-\.]+)",
    ]

    serial_patterns = [
        r"SERIAL(?:\sNO\.?|\sNUMBER)?[:\s#-]*([A-Z0-9\-\.]+)",
        r"S\/N[:\s#-]*([A-Z0-9\-\.]+)",
        r"SN[:\s#-]*([A-Z0-9\-\.]+)",
    ]

    brand_keywords = [
        "RHEEM", "RUUD", "GOODMAN", "AMANA", "CARRIER", "BRYANT",
        "BRADFORD WHITE", "DAIKIN", "LENNOX", "ARMSTRONG",
        "A.O. SMITH", "AO SMITH", "RINNAI", "PAYNE",
        "TRANE", "AMERICAN STANDARD"
    ]

    brand = ""
    for keyword in brand_keywords:
        if keyword in text:
            brand = keyword
            break

    model_number = ""
    for pattern in model_patterns:
        match = re.search(pattern, text)
        if match:
            model_number = match.group(1)
            break

    serial_number = ""
    for pattern in serial_patterns:
        match = re.search(pattern, text)
        if match:
            serial_number = match.group(1)
            break

    return {
        "brand": brand,
        "model_number": model_number,
        "serial_number": serial_number,
        "raw_text": raw_text,
        "needs_human_review": (
            not brand or not model_number or not serial_number
        )
    }


def detect_appliance_type(
    raw_text: str,
    brand: str = "",
    model_number: str = ""
) -> dict[str, Any]:
    text = f"{raw_text} {brand} {model_number}".upper()
    model = model_number.upper()

    if "HEAT PUMP" in text or " HP " in f" {model} ":
        return {"subtype": "Heat Pump"}

    if (
        "AIR CONDITIONER" in text
        or "CONDENSING UNIT" in text
        or "A/C" in text
    ):
        return {"subtype": "Air Conditioner"}

    if "FURNACE" in text or "GAS FURNACE" in text or "FORCED AIR" in text:
        return {"subtype": "Furnace"}

    if "AIR HANDLER" in text or "FAN COIL" in text:
        return {"subtype": "Air Handler"}

    if "TANKLESS" in text or "ON-DEMAND" in text or "ON DEMAND" in text:
        return {"subtype": "Tankless"}

    if (
        "WATER HEATER" in text
        or "STORAGE WATER HEATER" in text
        or " TANK " in f" {text} "
    ):
        return {"subtype": "Tank"}

    return {
        "subtype": "",
        "needs_human_review": True
    }


def process_nameplate(image_path: str) -> dict[str, Any]:
    raw_text = run_ocr(image_path)
    result = extract_nameplate_fields(raw_text)

    brand = result.get("brand", "")
    model_number = result.get("model_number", "")
    serial_number = result.get("serial_number", "")

    type_info = detect_appliance_type(
        raw_text=raw_text,
        brand=brand,
        model_number=model_number
    )

    result["raw_text"] = raw_text
    result["subtype"] = type_info.get("subtype", "")

    result["needs_human_review"] = (
        result.get("needs_human_review", False)
        or not brand
        or not model_number
        or not serial_number
        or not result["subtype"]
    )

    return result


def save_hvac_ocr_results(
    db,
    submission_id,
    ocr_result: dict[str, Any],
    age_info: dict[str, Any] | None,
    recommendation: Any
) -> HVACAnalysis:
    analysis = (
        db.query(HVACAnalysis)
        .filter(HVACAnalysis.submission_id == submission_id)
        .first()
    )

    if not analysis:
        analysis = HVACAnalysis(submission_id=submission_id)
        db.add(analysis)

    analysis.brand = ocr_result.get("brand")
    analysis.model_number = ocr_result.get("model_number")
    analysis.serial_number = ocr_result.get("serial_number")
    analysis.subtype = ocr_result.get("subtype")
    analysis.age = age_info.get("age_years") if age_info else None
    analysis.replacement_recommendation = recommendation.recommendation

    db.commit()
    db.refresh(analysis)

    return analysis


def save_water_heater_ocr_results(
    db,
    submission_id,
    ocr_result: dict[str, Any],
    age_info: dict[str, Any] | None,
    recommendation: Any
) -> WaterHeaterAnalysis:
    analysis = (
        db.query(WaterHeaterAnalysis)
        .filter(WaterHeaterAnalysis.submission_id == submission_id)
        .first()
    )

    if not analysis:
        analysis = WaterHeaterAnalysis(submission_id=submission_id)
        db.add(analysis)

    analysis.brand = ocr_result.get("brand")
    analysis.model_number = ocr_result.get("model_number")
    analysis.serial_number = ocr_result.get("serial_number")
    analysis.subtype = ocr_result.get("subtype")
    analysis.age = age_info.get("age_years") if age_info else None
    analysis.replacement_recommendation = recommendation.recommendation

    db.commit()
    db.refresh(analysis)

    return analysis

