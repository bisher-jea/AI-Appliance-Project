from dataclasses import dataclass
import re
import cv2
from cv2.typing import MatLike
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from typing import Protocol, TypedDict, cast


@dataclass
class NameplateFields:
    brand: str = ""
    model_number: str = ""
    serial_number: str = ""
    subtype: str = ""
    raw_text: str = ""
    needs_human_review: bool = False


@dataclass
class ApplianceType:
    subtype: str = ""
    needs_human_review: bool = False


class OCRWord(TypedDict):
    value: str


class OCRLine(TypedDict):
    words: list[OCRWord]


class OCRBlock(TypedDict):
    lines: list[OCRLine]


class OCRPage(TypedDict):
    blocks: list[OCRBlock]


class OCRExport(TypedDict):
    pages: list[OCRPage]


class OCRResultProtocol(Protocol):
    def export(self) -> object:
        ...


class OCRModelProtocol(Protocol):
    def __call__(self, doc: object) -> OCRResultProtocol:
        ...


OCR_MODEL = cast(
    OCRModelProtocol,
    ocr_predictor(
        det_arch="db_resnet50",
        reco_arch="crnn_vgg16_bn",
        pretrained=True,
        assume_straight_pages=True
    )
)


def preprocess_image(image_path: str) -> str:
    """_summary_

    Args:
        image_path (str): _description_

    Raises:
        ValueError: _description_
        RuntimeError: _description_

    Returns:
        str: _description_
    """
    image: MatLike | None = cv2.imread(image_path)

    if image is None:
        raise ValueError(f"Could not read image: {image_path}")

    gray: MatLike = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    resized: MatLike = cv2.resize(
        gray,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_CUBIC
    )

    thresholded: MatLike = cv2.threshold(
        resized,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    output_path = image_path.replace(".", "_processed.", 1)
    success = cv2.imwrite(output_path, thresholded)
    if not success:
        raise RuntimeError(f"Failed to write image: {output_path}")

    return output_path


def run_ocr(image_path: str) -> str:
    """_summary_

    Args:
        image_path (str): _description_

    Returns:
        str: _description_
    """
    processed_path = preprocess_image(image_path)

    doc: object = DocumentFile.from_images(processed_path)  # pyright: ignore[reportUnknownMemberType]
    result = OCR_MODEL(doc)
    exported = cast(OCRExport, result.export())

    extracted_lines: list[str] = []

    for page in exported["pages"]:
        for block in page["blocks"]:
            for line in block["lines"]:
                words = [
                    word["value"]
                    for word in line["words"]
                ]
                extracted_lines.append(" ".join(words))

    return "\n".join(extracted_lines)


def extract_nameplate_fields(raw_text: str) -> NameplateFields:
    """_summary_

    Args:
        raw_text (str): _description_

    Returns:
        NameplateFields: _description_
    """
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

    brand = next(
        (keyword for keyword in brand_keywords if keyword in text),
        ""
    )

    model_number = ""
    for pattern in model_patterns:
        match = re.search(pattern, text)
        if match is not None:
            model_number = match.group(1)
            break

    serial_number = ""
    for pattern in serial_patterns:
        match = re.search(pattern, text)
        if match is not None:
            serial_number = match.group(1)
            break

    return NameplateFields(
        brand=brand,
        model_number=model_number,
        serial_number=serial_number,
        raw_text=raw_text,
        needs_human_review=not brand or not model_number or not serial_number
    )


def detect_appliance_type(
    raw_text: str,
    brand: str = "",
    model_number: str = ""
) -> ApplianceType:
    """_summary_

    Args:
        raw_text (str): _description_
        brand (str, optional): _description_. Defaults to "".
        model_number (str, optional): _description_. Defaults to "".

    Returns:
        ApplianceType: _description_
    """
    text = f"{raw_text} {brand} {model_number}".upper()
    model = model_number.upper()

    if "HEAT PUMP" in text or " HP " in f" {model} ":
        return ApplianceType(subtype="Heat Pump")

    if (
        "AIR CONDITIONER" in text
        or "CONDENSING UNIT" in text
        or "A/C" in text
    ):
        return ApplianceType(subtype="Air Conditioner")

    if "FURNACE" in text or "GAS FURNACE" in text or "FORCED AIR" in text:
        return ApplianceType(subtype="Furnace")

    if "AIR HANDLER" in text or "FAN COIL" in text:
        return ApplianceType(subtype="Air Handler")

    if "TANKLESS" in text or "ON-DEMAND" in text or "ON DEMAND" in text:
        return ApplianceType(subtype="Tankless")

    if (
        "WATER HEATER" in text
        or "STORAGE WATER HEATER" in text
        or " TANK " in f" {text} "
    ):
        return ApplianceType(subtype="Tank")

    return ApplianceType(
        subtype="",
        needs_human_review=True
    )


def process_nameplate(image_path: str) -> NameplateFields:
    """_summary_

    Args:
        image_path (str): _description_

    Returns:
        NameplateFields: _description_
    """
    raw_text = run_ocr(image_path)
    result = extract_nameplate_fields(raw_text)

    type_info = detect_appliance_type(
        raw_text=raw_text,
        brand=result.brand,
        model_number=result.model_number
    )

    result.subtype = type_info.subtype

    result.needs_human_review = (
        result.needs_human_review
        or type_info.needs_human_review
        or not result.subtype
    )

    return result
