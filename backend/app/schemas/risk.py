from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TransactionRequest(BaseModel):
    """
    Core transaction information required by the transaction model.
    """

    step: int = Field(..., ge=0)
    type: str
    amount: float = Field(..., ge=0)
    nameDest: str = Field(..., min_length=1)

    # Behaviour context
    behaviour: Optional["BehaviourContext"] = None

    # Device context
    device: Optional["DeviceContext"] = None

    # Optional voice result produced by /voice-analysis
    voice: Optional["VoiceResult"] = None


class BehaviourContext(BaseModel):
    """
    Contextual behaviour signals used by BehaviourEngine.
    """

    new_recipient: int = Field(default=0, ge=0, le=1)
    new_device: int = Field(default=0, ge=0, le=1)
    unusual_hour: int = Field(default=0, ge=0, le=1)
    burst: int = Field(default=0, ge=0, le=1)
    location_jump: int = Field(default=0, ge=0, le=1)
    network_change: int = Field(default=0, ge=0, le=1)


class DeviceContext(BaseModel):
    """
    Device/network/location signals used by DeviceEngine.
    """

    new_device: bool = False
    network_change: bool = False
    location_jump: bool = False
    sim_change: bool = False


class VoiceResult(BaseModel):
    """
    Voice/social-engineering result.

    This can either come from the voice-analysis endpoint
    or be supplied by another trusted internal service.
    """

    voice_risk: float = Field(default=0.0, ge=0, le=100)
    risk_level: str = "LOW"

    language: Optional[str] = None
    language_probability: Optional[float] = None
    fraud_probability: Optional[float] = None

    ml_risk: Optional[float] = None
    rule_risk: Optional[float] = None

    transcript: Optional[str] = None
    risk_signals: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)


class RiskResponse(BaseModel):
    """
    Final FraudShield multimodal risk response.
    """

    transaction_id: Optional[str] = None

    risk_score: float
    risk_level: str

    headline: str
    summary: str
    message: str

    reasons: List[str]

    component_risks: Dict[str, float]
    weighted_contributions: Dict[str, float]

    requires_confirmation: bool
    high_friction: bool

    transaction_result: Dict[str, Any]
    behaviour_result: Dict[str, Any]
    device_result: Dict[str, Any]
    voice_result: Dict[str, Any]


class FeedbackRequest(BaseModel):
    """
    Reviewer/user feedback for a scored transaction.
    """

    transaction_id: str
    decision: str
    reviewer_note: Optional[str] = None