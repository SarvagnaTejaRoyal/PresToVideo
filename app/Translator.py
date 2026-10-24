"""
translator.py

Stage 3 of the pipeline: translates the English summary bullet points
(from Stage 2) into any of the 13 target Indian regional languages,
using AI4Bharat's IndicTrans2.

MODEL CHOICE: we use the *distilled* checkpoint
(ai4bharat/indictrans2-en-indic-dist-200M) rather than the full 1B
model -- it's noticeably smaller/faster to download and run on a
CPU-only laptop, which matters given our zero-cost, free-tier-hardware
constraint. Swap MODEL_NAME to the 1B version later for higher
translation quality if time and hardware allow (see comment below).

IMPORTANT: IndicTrans2 needs a small preprocessing/postprocessing step
(via the IndicTransToolkit package) -- it isn't a plain
"tokenize -> generate -> decode" model like BART. The preprocessor
handles text normalization and prepends the special language-pair tags
the model expects (e.g. "eng_Latn" -> "hin_Deva").

Install (in addition to transformers/torch already in requirements.txt):
    pip install IndicTransToolkit sentencepiece
"""

from dataclasses import dataclass
from typing import List

from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from app.tts import generate_speech

# Distilled checkpoint -- ~200M params, much lighter than the full 1B
# model. If translation quality isn't good enough once you test it,
# swap to "ai4bharat/indictrans2-en-indic-1B" (bigger download, slower,
# better quality) -- same code below works for either.
MODEL_NAME = "ai4bharat/indictrans2-en-indic-dist-200M"
SRC_LANG = "eng_Latn"

# Our 13 target languages mapped to IndicTrans2's FLORES-200 language
# codes. If a translation call fails with an "unsupported language
# code" style error, double check this mapping against the model card
# on Hugging Face -- codes occasionally get revised between releases.
LANGUAGE_CODES = {
    "Hindi": "hin_Deva",
    "Urdu": "urd_Arab",
    "Punjabi": "pan_Guru",
    "Gujarati": "guj_Gujr",
    "Marathi": "mar_Deva",
    "Telugu": "tel_Telu",
    "Kannada": "kan_Knda",
    "Malayalam": "mal_Mlym",
    "Tamil": "tam_Taml",
    "Odia": "ory_Orya",
    "Bengali": "ben_Beng",
    "Assamese": "asm_Beng",
    "Manipuri": "mni_Beng",  # Meitei/Manipuri written in Bengali script
}

_tokenizer = None
_model = None
_processor = None  # IndicProcessor, lazy-loaded alongside the model


def _get_model_tokenizer_processor():
    global _tokenizer, _model, _processor
    if _model is None:
        print(f"Loading translation model ({MODEL_NAME})... "
              f"this can take a while on first run while it downloads.")
        from IndicTransToolkit import IndicProcessor

        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
        _model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME, trust_remote_code=True)
        _processor = IndicProcessor(inference=True)
    return _model, _tokenizer, _processor


@dataclass
class Translation:
    language: str
    language_code: str
    translated_bullets: List[str]


def translate_bullets(bullets: List[str], language: str) -> Translation:
    """
    Translates a list of English bullet-point strings into the given
    target language.

    Args:
        bullets: English sentences/bullets (e.g. Summary.bullet_points
                 from Stage 2).
        language: One of our 13 supported language names, e.g. "Telugu".
                  Must be a key in LANGUAGE_CODES.
    """
    if language not in LANGUAGE_CODES:
        raise ValueError(
            f"Unsupported language '{language}'. "
            f"Supported languages: {list(LANGUAGE_CODES.keys())}"
        )

    tgt_lang = LANGUAGE_CODES[language]
    model, tokenizer, ip = _get_model_tokenizer_processor()

    # IndicProcessor normalizes text and prepends the special
    # "eng_Latn hin_Deva" style tags the model was trained to expect.
    batch = ip.preprocess_batch(bullets, src_lang=SRC_LANG, tgt_lang=tgt_lang)

    inputs = tokenizer(
        batch,
        truncation=True,
        padding="longest",
        return_tensors="pt",
    )

    generated_tokens = model.generate(
        **inputs,
        max_length=256,
        num_beams=5,
        num_return_sequences=1,
    )

    decoded = tokenizer.batch_decode(
        generated_tokens,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=True,
    )

    # Postprocess converts the model's internal representation back
    # into normal, readable target-script text.
    translated = ip.postprocess_batch(decoded, lang=tgt_lang)

    return Translation(
        language=language,
        language_code=tgt_lang,
        translated_bullets=translated,
    )


if __name__ == "__main__":
    sample_bullets = [
        "Vice President Shri C. P. Radhakrishnan addressed the convocation ceremony of Srimanta Sankaradeva University of Health Sciences, Guwahati.",
        "He also presented the Dr. John Berry White Award for the years 2023, 2024 and 2025.",
    ]

    for lang in ["Telugu", "Hindi"]:
        print(f"\n{'=' * 60}")
        print(f"Translating to {lang}")
        print("=" * 60)

        # Step 1: Translate English bullets
        result = translate_bullets(sample_bullets, lang)

        for i, line in enumerate(result.translated_bullets, start=1):
            print(f"{i}. {line}")

        # Step 2: Combine translated bullets into one narration
        narration_text = ". ".join( line.rstrip(".") for line in result.translated_bullets ) + "."

        # Step 3: Send the translated text directly to TTS
        output_file = f"output/audio/test_{lang.lower()}.mp3"

        speech_result = generate_speech(
            narration_text,
            lang,
            output_file
        )

        print(f"Audio generated: {speech_result.filename}")