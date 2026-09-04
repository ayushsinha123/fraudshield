from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.app.schemas import (
    BehaviourContext,
    DeviceContext,
    FeedbackRequest,
    RiskResponse,
    TransactionRequest,
    VoiceResult,
)

from backend.app.services.behaviour_engine import BehaviourEngine
from backend.app.services.device_engine import DeviceEngine
from backend.app.services.explanation_engine import ExplanationEngine
from backend.app.services.risk_engine import RiskEngine
from backend.app.services.transaction_model import TransactionModel
from backend.app.services.voice_engine import VoiceEngine


app = FastAPI(
    title="FraudShield API",
    description=(
        "Explainable multimodal pre-transaction fraud-risk engine."
    ),
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------
# Core services
# ------------------------------------------------------------------

transaction_engine: Optional[TransactionModel] = None
behaviour_engine: Optional[BehaviourEngine] = None
device_engine: Optional[DeviceEngine] = None
risk_engine: Optional[RiskEngine] = None
explanation_engine: Optional[ExplanationEngine] = None
voice_engine: Optional[VoiceEngine] = None


@app.on_event("startup")
def load_services() -> None:
    """
    Load lightweight/core services when the API starts.

    VoiceEngine is loaded lazily because faster-whisper can be
    computationally expensive.
    """

    global transaction_engine
    global behaviour_engine
    global device_engine
    global risk_engine
    global explanation_engine

    try:
        transaction_engine = TransactionModel()
        behaviour_engine = BehaviourEngine()
        device_engine = DeviceEngine()
        risk_engine = RiskEngine()
        explanation_engine = ExplanationEngine()

        print("FraudShield core services loaded successfully.")

    except Exception as exc:
        print(f"Service initialization failed: {exc}")
        raise


# ------------------------------------------------------------------
# Health check
# ------------------------------------------------------------------

@app.get("/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "service": "FraudShield API",
    }


# ------------------------------------------------------------------
# Risk score endpoint
# ------------------------------------------------------------------

@app.post(
    "/api/v1/risk-score",
    response_model=RiskResponse,
)
def calculate_risk(request: TransactionRequest) -> RiskResponse:

    if (
        transaction_engine is None
        or behaviour_engine is None
        or device_engine is None
        or risk_engine is None
        or explanation_engine is None
    ):
        raise HTTPException(
            status_code=503,
            detail="FraudShield services are not initialized.",
        )

    try:
        # ----------------------------------------------------------
        # 1. Transaction model
        # ----------------------------------------------------------

        transaction_input = {
            "step": request.step,
            "type": request.type,
            "amount": request.amount,
            "nameDest": request.nameDest,
        }

        transaction_result = (
            transaction_engine.score_transaction(
                transaction_input,
                update_history=True,
            )
        )

        transaction_risk = float(
            transaction_result["transaction_risk"]
        )

        transaction_reasons = transaction_result.get(
            "reasons",
            [],
        )

        # ----------------------------------------------------------
        # 2. Behaviour engine
        # ----------------------------------------------------------

        behaviour_context = request.behaviour

        if behaviour_context is None:
            behaviour_context = BehaviourContext()

        behaviour_input = {
            "amount": request.amount,
            "hour": request.step % 24,
            **behaviour_context.model_dump(),
        }

        behaviour_result = (
            behaviour_engine.score_transaction(
                behaviour_input
            )
        )

        behaviour_risk = float(
            behaviour_result["behaviour_risk"]
        )

        behaviour_reasons = behaviour_result.get(
            "reasons",
            [],
        )

        # ----------------------------------------------------------
        # 3. Device engine
        # ----------------------------------------------------------

        device_context = request.device

        if device_context is None:
            device_context = DeviceContext()

        device_input = device_context.model_dump()

        device_result = (
            device_engine.calculate_risk(
                device_input
            )
        )

        device_risk = float(
            device_result["device_risk"]
        )

        device_reasons = device_result.get(
            "reasons",
            [],
        )

        # ----------------------------------------------------------
        # 4. Voice result
        # ----------------------------------------------------------

        if request.voice is not None:
            voice_result = request.voice.model_dump()

            voice_risk = float(
                request.voice.voice_risk
            )

            voice_reasons = request.voice.reasons

        else:
            voice_result = {
                "voice_risk": 0.0,
                "risk_level": "LOW",
                "reasons": [],
            }

            voice_risk = 0.0
            voice_reasons = []

        # ----------------------------------------------------------
        # 5. Risk fusion
        # ----------------------------------------------------------

        fused_result = risk_engine.calculate_risk(
            transaction_risk=transaction_risk,
            behaviour_risk=behaviour_risk,
            device_risk=device_risk,
            voice_risk=voice_risk,
            transaction_reasons=transaction_reasons,
            behaviour_reasons=behaviour_reasons,
            device_reasons=device_reasons,
            voice_reasons=voice_reasons,
        )

        # ----------------------------------------------------------
        # 6. Human-readable explanation
        # ----------------------------------------------------------

        explanation = explanation_engine.explain(
            fused_result
        )

        return RiskResponse(
            transaction_id=None,
            risk_score=explanation["risk_score"],
            risk_level=explanation["risk_level"],
            headline=explanation["headline"],
            summary=explanation["summary"],
            message=explanation["message"],
            reasons=explanation["reasons"],
            component_risks=explanation["component_risks"],
            weighted_contributions=(
                explanation["weighted_contributions"]
            ),

            base_fusion_risk=explanation.get(
                "base_fusion_risk"
            ),

            escalation_reasons=explanation.get(
                "escalation_reasons",
                [],
            ),

            requires_confirmation=(
                explanation["requires_confirmation"]
            ),
            high_friction=(
                explanation["high_friction"]
            ),
            transaction_result=transaction_result,
            behaviour_result=behaviour_result,
            device_result=device_result,
            voice_result=voice_result,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Risk calculation failed: {exc}",
        ) from exc


# ------------------------------------------------------------------
# Voice analysis endpoint
# ------------------------------------------------------------------

@app.post("/api/v1/voice-analysis")
async def analyze_voice(
    audio: UploadFile = File(...),
) -> dict:

    global voice_engine

    try:
        if voice_engine is None:
            voice_engine = VoiceEngine(
                whisper_model_size="small"
            )

        temp_dir = "data/temp_audio"
        import os

        os.makedirs(
            temp_dir,
            exist_ok=True,
        )

        file_path = os.path.join(
            temp_dir,
            audio.filename or "uploaded_audio.wav",
        )

        with open(file_path, "wb") as buffer:
            while True:
                chunk = await audio.read(1024 * 1024)

                if not chunk:
                    break

                buffer.write(chunk)

        result = voice_engine.analyze_audio(
            file_path
        )

        return result

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Voice analysis failed: {exc}",
        ) from exc


# ------------------------------------------------------------------
# Placeholder endpoints
# ------------------------------------------------------------------

@app.get("/api/v1/transactions")
def get_transactions() -> dict:
    return {
        "status": "not_implemented",
        "message": "Transaction history will be connected after database integration.",
    }


@app.get("/api/v1/transactions/{transaction_id}")
def get_transaction(
    transaction_id: str,
) -> dict:
    return {
        "status": "not_implemented",
        "transaction_id": transaction_id,
    }


@app.post("/api/v1/feedback")
def submit_feedback(
    feedback: FeedbackRequest,
) -> dict:
    return {
        "status": "received",
        "feedback": feedback.model_dump(),
    }