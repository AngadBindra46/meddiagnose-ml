"""
Medical image preprocessor.

Handles DICOM-to-image conversion, normalization, and resizing
before sending to MedGemma for inference.
"""

import io
from pathlib import Path
from typing import Optional


def preprocess_image(
    file_path: str,
    target_size: tuple[int, int] = (512, 512),
    normalize: bool = True,
) -> Optional[bytes]:
    """
    Preprocess a medical image for AI inference.

    Supports: JPEG, PNG, WebP, DICOM (.dcm)
    Returns: processed image bytes in PNG format
    """
    path = Path(file_path)
    if not path.exists():
        return None

    ext = path.suffix.lower()

    if ext in (".dcm", ".dicom"):
        return _process_dicom(path, target_size, normalize)
    elif ext in (".jpg", ".jpeg", ".png", ".webp"):
        return _process_standard_image(path, target_size, normalize)
    else:
        return None


def _process_dicom(path: Path, target_size: tuple[int, int], normalize: bool) -> Optional[bytes]:
    """Convert DICOM to a normalized PNG."""
    try:
        import pydicom
        import numpy as np
        from PIL import Image

        ds = pydicom.dcmread(str(path))
        pixel_array = ds.pixel_array.astype(float)

        if normalize:
            pixel_array = (pixel_array - pixel_array.min()) / (pixel_array.max() - pixel_array.min() + 1e-8) * 255

        image = Image.fromarray(pixel_array.astype("uint8"))

        if image.mode != "RGB":
            image = image.convert("RGB")

        image = image.resize(target_size, Image.LANCZOS)

        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()

    except Exception as e:
        print(f"DICOM processing error: {e}")
        return None


def _process_standard_image(path: Path, target_size: tuple[int, int], normalize: bool) -> Optional[bytes]:
    """Resize and normalize a standard image."""
    try:
        from PIL import Image

        image = Image.open(path)

        if image.mode != "RGB":
            image = image.convert("RGB")

        image = image.resize(target_size, Image.LANCZOS)

        buf = io.BytesIO()
        image.save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    except Exception as e:
        print(f"Image processing error: {e}")
        return None


def get_image_metadata(file_path: str) -> dict:
    """Extract metadata from a medical image."""
    path = Path(file_path)
    ext = path.suffix.lower()
    metadata = {"filename": path.name, "format": ext, "size_bytes": path.stat().st_size}

    if ext in (".dcm", ".dicom"):
        try:
            import pydicom
            ds = pydicom.dcmread(str(path))
            metadata.update({
                "modality": getattr(ds, "Modality", "Unknown"),
                "study_description": getattr(ds, "StudyDescription", ""),
                "patient_position": getattr(ds, "PatientPosition", ""),
                "rows": getattr(ds, "Rows", 0),
                "columns": getattr(ds, "Columns", 0),
            })
        except Exception:
            pass
    else:
        try:
            from PIL import Image
            img = Image.open(path)
            metadata.update({"width": img.width, "height": img.height, "mode": img.mode})
        except Exception:
            pass

    return metadata
