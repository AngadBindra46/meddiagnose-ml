# meddiagnose-ml

ML inference library for the MedDiagnose platform. Provides MedGemma client, confidence scoring, image preprocessing, and specialty-specific prompt templates.

## Installation

```bash
pip install -e .
# or from git
pip install git+https://github.com/AngadBindra46/meddiagnose-ml.git
```

## Usage

```python
from ml.inference.medgemma_client import MedGemmaClient

client = MedGemmaClient(
    project_id="your-gcp-project",
    location="us-central1",
    endpoint_id="your-vertex-endpoint-id",
)

result = client.diagnose(
    clinical_notes="Patient presents with chest pain and shortness of breath",
    symptoms=["chest pain", "dyspnea", "fatigue"],
    image_paths=["xray.png"],       # optional: up to 5 images
    medical_history={"allergies": "Penicillin"},
    specialty="radiology",           # general, radiology, pathology
)

print(result["diagnosis"])
print(result["confidence"])
```

## Package Structure

```
ml/
  inference/
    medgemma_client.py      # Vertex AI MedGemma client (4B multimodal + 27B text)
    confidence_scorer.py    # Post-inference confidence scoring
    image_preprocessor.py   # Medical image preprocessing (DICOM, X-ray, photos)
  prompts/
    general_clinical.py     # General clinical diagnosis prompts
    radiology.py            # Radiology-specific prompts
    pathology.py            # Pathology-specific prompts
```

## Components

### MedGemmaClient

Sends clinical data to Google Vertex AI MedGemma endpoints. Supports:
- **4B multimodal model** -- text + medical images (X-rays, CT, skin photos, lab reports)
- **27B text-only model** -- higher accuracy for text-based diagnosis
- Automatic fallback to mock responses when Vertex AI is not configured

### Confidence Scorer

Post-processes model output to compute a calibrated confidence score based on:
- Specificity of the diagnosis
- Consistency between findings and diagnosis
- Number and quality of supporting evidence

### Prompt Templates

Specialty-specific prompt templates that structure the clinical context for optimal model performance:
- **General clinical** -- broad symptom-based diagnosis
- **Radiology** -- imaging-focused analysis (X-ray, CT, MRI findings)
- **Pathology** -- lab results and tissue analysis

## Requirements

- Python >= 3.10
- `google-cloud-aiplatform` (for Vertex AI inference)

## Related Repos

- [meddiagnose-api](https://github.com/AngadBindra46/meddiagnose-api) -- Backend API (primary consumer)
- [meddiagnose-airflow](https://github.com/AngadBindra46/meddiagnose-airflow) -- Batch pipelines (also imports this library)
