from __future__ import annotations

from pathlib import Path
from typing import Any

from ml.voice.features import VoiceRiskAnalyzer
from ml.voice.transcribe import VoiceTranscriber


class VoiceEngine:
    """
    FraudShield production voice-analysis pipeline.

    Audio
        -> Whisper transcription
        -> transcript risk analysis
        -> multilingual rule layer
        -> final voice/social-engineering risk
    """

    def __init__(
        self,
        whisper_model_size: str = "small",
    ) -> None:

        self.transcriber = VoiceTranscriber(
            model_size=whisper_model_size
        )

        self.analyzer = VoiceRiskAnalyzer()

    def analyze_audio(
        self,
        audio_path: str | Path,
    ) -> dict[str, Any]:

        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise FileNotFoundError(
                f"Audio file not found: {audio_path}"
            )

        # --------------------------------------------------
        # 1. Audio -> transcript
        # --------------------------------------------------
        transcription = self.transcriber.transcribe(
            audio_path
        )

        transcript = transcription["transcript"]

        # --------------------------------------------------
        # 2. Transcript -> fraud/social-engineering risk
        # --------------------------------------------------
        risk_result = self.analyzer.analyze(
            transcript
        )

        # --------------------------------------------------
        # 3. Combine transcription + risk information
        # --------------------------------------------------
        result = {
            "audio_path": str(audio_path),
            "language": transcription["language"],
            "language_probability": transcription[
                "language_probability"
            ],
            "transcript": transcript,

            "fraud_probability": risk_result[
                "fraud_probability"
            ],

            "ml_risk": risk_result[
                "ml_risk"
            ],

            "rule_risk": risk_result[
                "rule_risk"
            ],

            "voice_risk": risk_result[
                "voice_risk"
            ],

            "risk_level": risk_result[
                "risk_level"
            ],

            "risk_signals": risk_result[
                "risk_signals"
            ],

            "reasons": risk_result[
                "reasons"
            ],
        }

        return result


if __name__ == "__main__":

    import sys
    import json

    if len(sys.argv) != 2:
        print(
            "Usage:"
        )
        print(
            "python -m backend.app.services.voice_engine "
            "<audio_file>"
        )
        raise SystemExit(1)

    audio_file = sys.argv[1]

    print(
        "Loading FraudShield Voice Engine..."
    )

    engine = VoiceEngine()

    print(
        "Analyzing audio..."
    )

    result = engine.analyze_audio(
        audio_file
    )

    print(
        "\nVoice Analysis Result"
    )
    print(
        "=" * 80
    )

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )
    )