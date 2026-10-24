import torch
import soundfile as sf
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer

MODEL_ID = "ai4bharat/indic-parler-tts-pretrained"

# Use the GPU when available; otherwise use the CPU.
device = "cuda:0" if torch.cuda.is_available() else "cpu"

print(f"Device: {device}")
if device == "cuda:0":
    print(f"GPU: {torch.cuda.get_device_name(0)}")

print("Loading Parler-TTS model...")

model = ParlerTTSForConditionalGeneration.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float16 if device == "cuda:0" else torch.float32,
).to(device)

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

description_tokenizer = AutoTokenizer.from_pretrained(
    model.config.text_encoder._name_or_path
)

# Short Assamese sample sentence
prompt = "ꯅꯨꯡꯁꯤꯕꯥ"
# Voice description for the Assamese speaker Amit
description = (
    "Laishram speaks Manipuri at a moderate pace "
    "in a clear, natural-sounding voice."
)

print("Preparing text...")

description_inputs = description_tokenizer(
    description,
    return_tensors="pt",
).to(device)

prompt_inputs = tokenizer(
    prompt,
    return_tensors="pt",
).to(device)

print("Generating Assamese speech...")

with torch.inference_mode():
    generation = model.generate(
        input_ids=description_inputs.input_ids,
        attention_mask=description_inputs.attention_mask,
        prompt_input_ids=prompt_inputs.input_ids,
        prompt_attention_mask=prompt_inputs.attention_mask,
    )

audio = generation.float().cpu().numpy().squeeze()

output_file = "manipuri_test.wav"

sf.write(
    output_file,
    audio,
    model.config.sampling_rate,
)

print(f"Success! Audio saved to: {output_file}")
print(f"Sample rate: {model.config.sampling_rate} Hz")
