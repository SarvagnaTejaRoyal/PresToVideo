"""
Stage 4: Text-to-Speech

gTTS:
    English and other supported languages.

Parler-TTS:
    Assamese, Odia, and Manipuri.
"""

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess

from gtts import gTTS


# Languages handled by gTTS.
LANGUAGE_CODES = {
    "English": "en",
    "Hindi": "hi",
    "Urdu": "ur",
    "Punjabi": "pa",
    "Gujarati": "gu",
    "Marathi": "mr",
    "Telugu": "te",
    "Kannada": "kn",
    "Malayalam": "ml",
    "Tamil": "ta",
    "Bengali": "bn",
}

# Languages handled by Parler-TTS.
PARLER_LANGUAGES = {
    "Assamese",
    "Odia",
    "Manipuri",
}

# Use the separate Parler-TTS environment.
PARLER_PYTHON = Path(
    "/home/sarvagna/.venvs/parler-tts/bin/python"
)

PARLER_HELPER = (
    Path(__file__).resolve().parent / "parler_tts_helper.py"
)


@dataclass
class SpeechResult:
    language: str
    text: str
    filename: str


def prepare_tts_text(text):
    # Remove dots from initials such as C. P. Radhakrishnan.
    return re.sub(
        r"\b([A-Za-z])\.\s*([A-Za-z])\.",
        r"\1 \2",
        text,
    )


def generate_speech(text, language, output_file):
    """
    Generate speech using gTTS or Parler-TTS.
    """

    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

    output_path = Path(output_file)

    # Parler-TTS generates WAV audio.
    if language in PARLER_LANGUAGES:

        output_path = output_path.with_suffix(".wav")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not PARLER_PYTHON.is_file():
            raise FileNotFoundError(
                f"Parler Python environment not found: {PARLER_PYTHON}"
            )

        if not PARLER_HELPER.is_file():
            raise FileNotFoundError(
                f"Parler helper not found: {PARLER_HELPER}"
            )

        narration = prepare_tts_text(text)

        print(f"Generating {language} speech with Parler-TTS...")

        subprocess.run(
            [
                str(PARLER_PYTHON),
                str(PARLER_HELPER),
                language,
                str(output_path),
            ],
            input=narration,
            text=True,
            check=True,
        )

        print(f"Saved: {output_path}")

        return SpeechResult(
            language=language,
            text=narration,
            filename=str(output_path),
        )

    # All other configured languages use gTTS.
    if language not in LANGUAGE_CODES:
        raise ValueError(f"Unsupported TTS language: {language}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    narration = prepare_tts_text(text)

    print(f"Generating {language} speech with gTTS...")

    tts = gTTS(
        text=narration,
        lang=LANGUAGE_CODES[language],
    )

    tts.save(str(output_path))

    print(f"Saved: {output_path}")

    return SpeechResult(
        language=language,
        text=narration,
        filename=str(output_path),
    )


if __name__ == "__main__":
    test_text = (
        "ఉపరాష్ట్రపతి శ్రీ సి. పి. రాధాకృష్ణన్ "
        "గౌహతిలోని శ్రీమంత శంకరదేవ యూనివర్శిటీ "
        "ఆఫ్ హెల్త్ సైన్సెస్ స్నాతకోత్సవాన్ని "
        "ఉద్దేశించి ప్రసంగించారు."
    )

    result = generate_speech(
        test_text,
        "Telugu",
        "output/audio/test_telugu.mp3",
    )

    print("\nTTS test completed!")
    print(f"Language: {result.language}")
    print(f"File: {result.filename}")