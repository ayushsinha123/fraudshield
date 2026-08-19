from __future__ import annotations

from pathlib import Path
from typing import Any

import torch
from faster_whisper import WhisperModel


DEFAULT_WHISPER_MODEL = "small"


class VoiceTranscriber:
    """
    FraudShield audio transcription service.

    Converts an audio file into a transcript using faster-whisper.
    """

    def __init__(
        self,
        model_size: str = DEFAULT_WHISPER_MODEL,
    ) -> None:

        self.model_size = model_size

        if torch.cuda.is_available():
            self.device = "cuda"
            self.compute_type = "float16"
        else:
            self.device = "cpu"
            self.compute_type = "int8"

        self.model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
        )

    def transcribe(
        self,
        audio_path: str | Path,
    ) -> dict[str, Any]:

        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise FileNotFoundError(
                f"Audio file not found: {audio_path}"
            )

        if not audio_path.is_file():
            raise ValueError(
                f"Audio path is not a file: {audio_path}"
            )

        segments, info = self.model.transcribe(
            str(audio_path),
            beam_size=5,
        )

        transcript = " ".join(
            segment.text.strip()
            for segment in segments
            if segment.text.strip()
        ).strip()

        return {
            "transcript": transcript,
            "language": info.language,
            "language_probability": float(
                info.language_probability
            ),
            "audio_path": str(audio_path),
        }


if __name__ == "__main__":

    import sys

    if len(sys.argv) != 2:
        print(
            "Usage: python -m ml.voice.transcribe "
            "<audio_file>"
        )
        raise SystemExit(1)

    audio_file = sys.argv[1]

    transcriber = VoiceTranscriber()

    result = transcriber.transcribe(audio_file)

    print("\nTranscription result")
    print("=" * 60)

    print("Language:", result["language"])
    print(
        "Language probability:",
        f"{result['language_probability']:.4f}",
    )
    print("Transcript:")
    print(result["transcript"])