"""SQLAlchemy ORM models for Combuyn.

Importing this package registers all models on the declarative ``Base.metadata``,
which is what Alembic autogenerate and the test fixtures rely on.
"""

from app.models.ccf import (
    CommonControl,
    ControlRequirementMapping,
    Framework,
    FrameworkRequirement,
)
from app.models.ai_governance import (
    AIComplianceTask,
    AIDataPrivacyGuardrail,
    AIImpactAssessment,
    AIInfrastructureValidationCheck,
    AIRiskClassification,
    AISystemInventory,
    AISystemISOControlMapping,
    AIVendorProvider,
    ISO42001AnnexAControl,
    ISO42001ControlObjective,
    MedicalAIAlgorithmicRiskAssessment,
    MedicalSOUPComponent,
    TrustCenterAITransparencyMetric,
    TrustCenterDocumentRequest,
    TrustCenterFrameworkStatus,
)

__all__ = [
    "Framework",
    "FrameworkRequirement",
    "CommonControl",
    "ControlRequirementMapping",
    "AIComplianceTask",
    "AIDataPrivacyGuardrail",
    "AIImpactAssessment",
    "AIInfrastructureValidationCheck",
    "AIRiskClassification",
    "AISystemInventory",
    "AISystemISOControlMapping",
    "AIVendorProvider",
    "ISO42001AnnexAControl",
    "ISO42001ControlObjective",
    "MedicalAIAlgorithmicRiskAssessment",
    "MedicalSOUPComponent",
    "TrustCenterAITransparencyMetric",
    "TrustCenterDocumentRequest",
    "TrustCenterFrameworkStatus",
]
