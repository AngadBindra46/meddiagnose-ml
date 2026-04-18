"""
MedGemma client for Vertex AI inference.

Supports both the 4B multimodal model (images + text) and the 27B text-only model.
Falls back to mock responses when Vertex AI is not configured.
"""

import base64
import json
from pathlib import Path
from typing import Optional

from ml.inference.confidence_scorer import score_confidence
from ml.prompts import get_prompt_template


class MedGemmaClient:
    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        endpoint_id: Optional[str] = None,
    ):
        self.project_id = project_id
        self.location = location
        self.endpoint_id = endpoint_id
        self._client = None

    def _get_client(self):
        if self._client is None:
            from google.cloud import aiplatform
            aiplatform.init(project=self.project_id, location=self.location)
            self._client = aiplatform.Endpoint(self.endpoint_id)
        return self._client

    def diagnose(
        self,
        clinical_notes: str,
        symptoms: list[str],
        image_paths: list[str] | None = None,
        medical_history: dict | None = None,
        specialty: str = "general",
    ) -> dict:
        prompt = get_prompt_template(specialty)
        formatted_prompt = prompt.format(
            clinical_notes=clinical_notes,
            symptoms=", ".join(symptoms) if symptoms else "None reported",
            medical_history=json.dumps(medical_history or {}, indent=2),
        )

        if not self.endpoint_id:
            return self._mock_response(formatted_prompt, specialty)

        try:
            instances = [{"prompt": formatted_prompt}]

            if image_paths:
                encoded_images = []
                for img_path in image_paths[:5]:
                    img_data = self._encode_image(img_path)
                    if img_data:
                        encoded_images.append(img_data)
                if encoded_images:
                    instances[0]["images"] = encoded_images

            endpoint = self._get_client()
            response = endpoint.predict(instances=instances)

            raw_text = response.predictions[0] if response.predictions else ""
            parsed = self._parse_response(raw_text)
            parsed["confidence"] = score_confidence(parsed)
            parsed["model_version"] = f"medgemma-{'4b' if image_paths else '27b'}"
            return parsed

        except Exception as e:
            return {
                "diagnosis": "Error during inference",
                "reasoning": str(e),
                "confidence": 0.0,
                "findings": [],
                "model_version": "error",
                "error": True,
            }

    def _encode_image(self, image_path: str) -> Optional[str]:
        path = Path(image_path)
        if not path.exists():
            return None
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _parse_response(self, raw: str) -> dict:
        """Parse the model's text output into structured fields."""
        try:
            if isinstance(raw, str) and raw.strip().startswith("{"):
                return json.loads(raw)
        except json.JSONDecodeError:
            pass

        return {
            "diagnosis": raw[:500] if raw else "No diagnosis generated",
            "reasoning": raw[500:2000] if len(raw) > 500 else "",
            "findings": [],
        }

    def _mock_response(self, prompt: str, specialty: str) -> dict:
        return {
            "diagnosis": f"[MOCK] Preliminary assessment for {specialty} case",
            "reasoning": f"MedGemma endpoint not configured. Prompt was:\n{prompt[:200]}...",
            "confidence": 0.82,
            "findings": [
                {"finding": "Mock finding — configure Vertex AI for real analysis", "severity": "info"},
            ],
            "medications": [
                {"name": "Paracetamol", "dosage": "500mg", "frequency": "Every 6 hours", "duration": "3 days", "type": "tablet", "notes": "Take after meals"},
            ],
            "lifestyle_recommendations": ["Rest well", "Stay hydrated"],
            "precautions": ["Monitor symptoms"],
            "severity": "mild",
            "urgency": "routine",
            "when_to_see_doctor": "If symptoms persist beyond 5 days or worsen",
            "recommended_tests": ["CBC"],
            "model_version": "medgemma-mock",
        }
