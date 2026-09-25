"""
summarizer.py

Stage 2 of the pipeline: takes a press release's title + body (from
the Stage 1 scraper) and produces a short, video-ready summary --
3 to 4 bullet points -- using a pretrained abstractive summarization
model (BART, fine-tuned on CNN/DailyMail news data).

NOTE ON API CHOICE: this uses AutoTokenizer + AutoModelForSeq2SeqLM
directly, NOT transformers.pipeline("summarization", ...). Newer
transformers releases (v5+) reorganized the pipeline task registry,
and "summarization" may raise KeyError: "Unknown task" depending on
your installed version. AutoTokenizer/AutoModelForSeq2SeqLM is the
lower-level, stable API that pipeline() itself is built on -- it
works the same way across transformers versions.
"""

import re
from dataclasses import dataclass
from typing import List

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

MODEL_NAME = "facebook/bart-large-cnn"

MIN_WORDS_FOR_MODEL = 60  # below this, sentence-split instead of model-summarize

_tokenizer = None
_model = None  # both lazy-loaded so importing this module doesn't
                # immediately trigger a slow model download


def _get_model_and_tokenizer():
    global _tokenizer, _model
    if _model is None:
        print(f"Loading summarization model ({MODEL_NAME})... "
              f"this can take a while on first run while it downloads.")
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    return _model, _tokenizer


@dataclass
class Summary:
    bullet_points: List[str]
    raw_summary: str
    original_word_count: int
    summary_word_count: int


def summarize_release(title: str, body: str, max_bullets: int = 4) -> Summary:
    """
    Summarizes a press release body into at most max_bullets short
    bullet points, ready to hand to the translation stage.
    """
    original_word_count = len(body.split())

    if original_word_count < MIN_WORDS_FOR_MODEL:
        sentences = _split_into_sentences(body)
        bullets = sentences[:max_bullets]
        raw_summary = " ".join(bullets)
    else:
        model, tokenizer = _get_model_and_tokenizer()

        inputs = tokenizer(
            body,
            return_tensors="pt",
            max_length=1024,
            truncation=True,
        )
        summary_ids = model.generate(
            inputs["input_ids"],
            max_length=130,
            min_length=30,
            num_beams=4,
            do_sample=False,
        )
        raw_summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True).strip()
        sentences = _split_into_sentences(raw_summary)
        bullets = sentences[:max_bullets]

    return Summary(
        bullet_points=bullets,
        raw_summary=raw_summary,
        original_word_count=original_word_count,
        summary_word_count=len(raw_summary.split()),
    )


def _split_into_sentences(text: str) -> List[str]:
    """
    Sentence splitter that protects common abbreviations and -- important
    for Indian official names -- single-letter initials (C. P. Radhakrishnan,
    A. P. J. Abdul Kalam, K. R. Narayanan, etc.) from being mistaken for
    sentence endings.
    """
    text = text.strip()
    protected = re.sub(r"\b(Dr|Shri|Smt|Mr|Mrs|Ms|Prof)\.", r"\1<DOT>", text)
    protected = re.sub(r"\b([A-Z])\.", r"\1<DOT>", protected)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", protected)
    return [p.replace("<DOT>", ".").strip() for p in parts if p.strip()]


if __name__ == "__main__":
    sample_title = "Vice President Shri C. P. Radhakrishnan attends SSUHS Convocation in Guwahati"
    sample_body = (
        "Vice President Shri C. P. Radhakrishnan today urged graduating healthcare "
        "professionals to uphold compassion, ethics and scientific excellence, and "
        "dedicate their knowledge and skills to the service of humanity, while "
        "addressing the convocation ceremony of Srimanta Sankaradeva University of "
        "Health Sciences (SSUHS), Guwahati. He also presented the Dr. John Berry "
        "White Award for the years 2023, 2024 and 2025.\n\n"
        "Addressing the convocation, he said that the University, named after "
        "Mahapurusha Srimanta Sankaradeva, has emerged as an important institution "
        "for health sciences education, research and public health.\n\n"
        "The Vice President highlighted the transformation of India's healthcare "
        "sector under the leadership of Prime Minister Shri Narendra Modi, referring "
        "to initiatives such as Ayushman Bharat. He noted that more than 44 crore "
        "Ayushman cards have been issued and recalled that the scheme has helped "
        "poor and middle-class families save an estimated Rs. 2 lakh crore in "
        "medical expenses.\n\n"
        "Highlighting Assam's healthcare progress, Shri C. P. Radhakrishnan said "
        "that the number of medical colleges in the State has more than doubled "
        "from seven in 2021 to 15, with another nine under construction.\n\n"
        "Calling upon youth to lead healthy and disciplined lives, Shri C. P. "
        "Radhakrishnan urged them to stay away from substance abuse and contribute "
        "towards building a Nasha Mukt Bharat."
    )

    result = summarize_release(sample_title, sample_body)

    print("Original word count:", result.original_word_count)
    print("Summary word count:", result.summary_word_count)
    print("\nRaw summary:\n", result.raw_summary)
    print("\nBullet points:")
    for i, bullet in enumerate(result.bullet_points, start=1):
        print(f"{i}. {bullet}")