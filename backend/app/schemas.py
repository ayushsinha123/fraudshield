from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ==============================================================
# Behaviour context
# ==============================================================

class BehaviourContext(BaseModel):
    """
    Behaviour-related context supplied with a transaction.

    The BehaviourEngine expects these contextual indicators.
    """

    new_recipient: int = Field(
        default=0,
        ge=0,
        le=1,
    )

    new_device: int = Field(
        default=0,
        ge=0,
        le=1,
    )

    unusual_hour: int = Field(
        default=0,
        ge=0,
        le=1,
    )

    burst: int = Field(
        default=0,
        ge=0,
        le=1,
    )

    location_jump: int = Field(
        default=0,
        ge=0,
        le=1,
    )

    network_change: int = Field(
        default=0,
        ge=0,
        le=1,
    )


# ==============================================================
# Device context
# ==============================================================

class DeviceContext(BaseModel):
    """
    Device/security context supplied with a transaction.
    """

    new_device: bool = False

    network_change: bool = False

    location_jump: bool = False

    sim_change: bool = False


# ==============================================================
# Voice result
# ==============================================================

class VoiceResult(BaseModel):
    """
    Voice-analysis result supplied to the risk-score endpoint.

    The voice engine may provide additional metadata such as
    language, transcript, or fraud probability. Those optional
    fields are preserved here when available.
    """

    voice_risk: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
    )

    risk_level: str = "LOW"

    reasons: List[str] = Field(
        default_factory=list
    )

    fraud_probability: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    language: Optional[str] = None

    transcript: Optional[str] = None

    model_config = ConfigDict(
        extra="allow"
    )


# ==============================================================
# Transaction request
# ==============================================================

class TransactionRequest(BaseModel):
    """
    Request body for:

        POST /api/v1/risk-score
    """

    step: int = Field(
        ...,
        ge=0,
    )

    type: str

    amount: float = Field(
        ...,
        ge=0.0,
    )

    nameDest: str

    behaviour: Optional[BehaviourContext] = None

    device: Optional[DeviceContext] = None

    voice: Optional[VoiceResult] = None


# ==============================================================
# Feedback request
# ==============================================================

class FeedbackRequest(BaseModel):
    """
    Reviewer/user feedback associated with a transaction.
    """

    transaction_id: str

    decision: str

    reviewer_note: Optional[str] = None

    model_config = ConfigDict(
        extra="allow"
    )


# ==============================================================
# Risk response
# ==============================================================

class RiskResponse(BaseModel):
    """
    Final response returned by:

        POST /api/v1/risk-score

    The nested module results remain flexible because each
    FraudShield service exposes its own explanatory metadata.
    """

    transaction_id: Optional[str] = None

    risk_score: float

    risk_level: str

    headline: str

    summary: str

    message: str

    reasons: List[str] = Field(
        default_factory=list
    )

    component_risks: Dict[str, float] = Field(
        default_factory=dict
    )

    weighted_contributions: Dict[str, float] = Field(
        default_factory=dict
    )

    base_fusion_risk: Optional[float] = None

    escalation_reasons: List[str] = Field(
        default_factory=list
    )

    requires_confirmation: bool = False

    high_friction: bool = False

    transaction_result: Dict[str, Any] = Field(
        default_factory=dict
    )

    behaviour_result: Dict[str, Any] = Field(
        default_factory=dict
    )

    device_result: Dict[str, Any] = Field(
        default_factory=dict
    )

    voice_result: Dict[str, Any] = Field(
        default_factory=dict
    )

    model_config = ConfigDict(
        extra="allow"
    )