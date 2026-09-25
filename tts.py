"""
Stage 4: Text-to-Speech

Current prototype engine:
    gTTS

The function interface is kept simple so that the TTS engine
can later be replaced by IndicF5 or another multilingual TTS model.
"""

from dataclasses import dataclass
from pathlib import Path

from gtts import gTTS
import re

# gTTS language codes for the languages we currently want to test.
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
    "Assamese": "as",
    "Odia": "or",
}


@dataclass
class SpeechResult:
    language: str
    text: str
    filename: str

def prepare_tts_text(text):
    # Remove dots from initials such as C. P. Radhakrishnan
    text = re.sub(r'\b([A-Za-z])\.\s*([A-Za-z])\.', r'\1 \2', text)

    return text

def generate_speech(text, language, output_file):
    """
    Convert translated text into speech and save it as an MP3 file.
    """

    if language not in LANGUAGE_CODES:
        raise ValueError(f"Unsupported TTS language: {language}")

    if not text.strip():
        raise ValueError("Text cannot be empty")

    lang_code = LANGUAGE_CODES[language]

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    text = prepare_tts_text(text)

    print(f"Generating speech for {language}...")
    
    tts = gTTS(
        text=text,
        lang=lang_code
    )

    tts.save(str(output_path))

    print(f"Saved: {output_path}")

    return SpeechResult(
        language=language,
        text=text,
        filename=str(output_path)
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
        "output/audio/test_telugu.mp3"
    )

    print()
    print("TTS test completed!")
    print(f"Language: {result.language}")
    print(f"File: {result.filename}")