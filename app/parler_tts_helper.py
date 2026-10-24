import sys
import torch
import soundfile as sf
from pathlib import Path
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer

MODEL_ID = "ai4bharat/indic-parler-tts-pretrained"

LANGUAGE_DETAILS = {
    "Assamese": {
        "description": (
            "A speaker speaks Assamese at a moderate pace "
            "in a clear, natural-sounding voice."
        ),
        "sample_text": "নমস্কাৰ",
    },
    "Odia": {
        "description": (
            "A speaker speaks Odia at a moderate pace "
            "in a clear, natural-sounding voice."
        ),
        "sample_text": "ନମସ୍କାର",
    },
    "Manipuri": {
        "description": (
            "Laishram speaks Manipuri at a moderate pace "
            "in a clear, natural-sounding voice."
        ),
        "sample_text": "ꯅꯨꯡꯁꯤꯕꯥ",
    },
}


def generate_parler_speech(text, language, output_file):
    if language not in LANGUAGE_DETAILS:
        raise ValueError(f"Unsupported Parler language: {language}")

    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"Parler TTS: {language} | Device: {device}")

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("Loading Parler-TTS model...")

    model = ParlerTTSForConditionalGeneration.from_pretrained(
        MODEL_ID,
        torch_dtype=(
            torch.float16 if device == "cuda:0" else torch.float32
        ),
    ).to(device)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

    description_tokenizer = AutoTokenizer.from_pretrained(
        model.config.text_encoder._name_or_path
    )

    description = LANGUAGE_DETAILS[language]["description"]

    description_inputs = description_tokenizer(
        description,
        return_tensors="pt",
    ).to(device)

    prompt_inputs = tokenizer(
        text,
        return_tensors="pt",
    ).to(device)

    print(f"Generating {language} speech...")

    try:
        with torch.inference_mode():
            generation = model.generate(
                input_ids=description_inputs.input_ids,
                attention_mask=description_inputs.attention_mask,
                prompt_input_ids=prompt_inputs.input_ids,
                prompt_attention_mask=prompt_inputs.attention_mask,
            )

        audio = generation.float().cpu().numpy().squeeze()

        sf.write(
            str(output_path),
            audio,
            model.config.sampling_rate,
        )

    finally:
        del model
        if device == "cuda:0":
            torch.cuda.empty_cache()

    return str(output_path)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(
            "Usage: python app/parler_tts_helper.py "
            '"LANGUAGE" "OUTPUT_FILE"'
        )
        sys.exit(1)

    language = sys.argv[1]
    output_file = sys.argv[2]

    # Read the narration from standard input.
    text = sys.stdin.read()

    generate_parler_speech(text, language, output_file)
