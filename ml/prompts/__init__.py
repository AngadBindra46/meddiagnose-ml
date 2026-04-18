from ml.prompts.general_clinical import GENERAL_CLINICAL_PROMPT
from ml.prompts.radiology import RADIOLOGY_PROMPT
from ml.prompts.pathology import PATHOLOGY_PROMPT

PROMPT_REGISTRY = {
    "general": GENERAL_CLINICAL_PROMPT,
    "radiology": RADIOLOGY_PROMPT,
    "pathology": PATHOLOGY_PROMPT,
}


def get_prompt_template(specialty: str) -> str:
    return PROMPT_REGISTRY.get(specialty, GENERAL_CLINICAL_PROMPT)
