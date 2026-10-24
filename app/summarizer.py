"""
Stage 2 of the pipeline: summarize a PIB press release into video-ready
bullet points using BART, while preserving useful facts from the original.
"""

import re
from dataclasses import dataclass
from typing import List

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


MODEL_NAME = "facebook/bart-large-cnn"
MIN_WORDS_FOR_MODEL = 60

_tokenizer = None
_model = None


def _get_model_and_tokenizer():
    global _tokenizer, _model

    if _model is None:
        print(
            f"Loading summarization model ({MODEL_NAME})... "
            "this can take a while on first run while it downloads."
        )
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

    return _model, _tokenizer


@dataclass
class Summary:
    bullet_points: List[str]
    raw_summary: str
    original_word_count: int
    summary_word_count: int


def _is_footer_or_noise(sentence: str) -> bool:
    """Identify PIB footer codes and fragments that should not be narrated."""
    text = sentence.strip()

    # PIB reference codes, e.g. PR-177-TAR/KV/GA/RK
    if re.match(r"^(?:PR|PIB)-\d+(?:-[A-Z0-9]+)+$", text, flags=re.IGNORECASE):
        return True

    if len(text.split()) < 3:
        return True

    if re.match(r"^(?:for further information|interested people may visit)\b", text, re.I):
        return True

    return False


def _normalise_sentence(sentence: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", sentence.lower()).strip()


def _select_diverse_sentences(
    original_sentences: List[str],
    bart_sentences: List[str],
    max_sentences: int = 5,
) -> List[str]:
    """
    Select sentences covering distinct useful fact categories.
    Sentences are taken from the source or BART output; no new facts are created.
    """
    categories = {
        "reach": (
            "35 crore", "13.94 crore", "10.86 crore", "32 lakh",
            "people", "educational institutions",
        ),
        "launch": (
            "launched", "15 august", "vulnerable districts",
            "expanded its reach",
        ),
        "purpose": (
            "nasha mukt bharat", "drug demand reduction",
            "awareness programmes", "prevention",
        ),
        "support": (
            "treatment", "rehabilitation", "aftercare", "recovery",
        ),
        "help": ("14446", "helpline"),
        "community": (
            "community participation", "community-led", "youth clubs",
            "women's groups", "women’s groups",
        ),
    }

    candidates = []
    seen = set()

    # Prefer source sentences for factual precision, then BART sentences.
    for raw_sentence in original_sentences + bart_sentences:
        sentence = _compact_sentence(raw_sentence.strip())

        if _is_footer_or_noise(sentence):
            continue

        normalized = _normalise_sentence(sentence)
        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        candidates.append(sentence)

    selected = []
    covered_categories = set()

    # Choose at most one sentence for each category, preferring sentences
    # that add a new category. Categories without matching source content
    # are simply skipped.
    for category, keywords in categories.items():
        if len(selected) >= max_sentences:
            break

        for sentence in candidates:
            lower = sentence.lower()
            if any(keyword in lower for keyword in keywords):
                sentence_categories = {
                    name
                    for name, category_keywords in categories.items()
                    if any(keyword in lower for keyword in category_keywords)
                }

                if category not in sentence_categories:
                    continue

                # Avoid selecting another sentence if it adds no new topic.
                new_categories = sentence_categories - covered_categories
                if selected and not new_categories:
                    continue

                if sentence not in selected:
                    selected.append(sentence)
                    covered_categories.update(sentence_categories)
                break

    # Fill any remaining slots with distinct source/BART sentences.
    for sentence in candidates:
        if len(selected) >= max_sentences:
            break
        if sentence not in selected:
            selected.append(sentence)

    return selected[:max_sentences]


def summarize_release(title: str, body: str, max_bullets: int = 6) -> Summary:
    """
    Summarize a PIB press release into video-ready bullet points.
    Combines BART's summary with important sentences from the original.
    """
    original_word_count = len(body.split())

    if original_word_count < MIN_WORDS_FOR_MODEL:
        original_sentences = _split_into_sentences(body)
        clean_sentences = [
            sentence for sentence in original_sentences
            if not _is_footer_or_noise(sentence)
        ]
        bullets = clean_sentences[:max_bullets]
        raw_summary = " ".join(bullets)

    else:
        model, tokenizer = _get_model_and_tokenizer()

        # Include the title so the model knows the main topic.
        text_to_summarize = f"{title}. {body}"

        # Split into chunks so later paragraphs can also be processed.
        words = text_to_summarize.split()
        chunk_size = 350
        chunks = [
            " ".join(words[i:i + chunk_size])
            for i in range(0, len(words), chunk_size)
        ]

        chunk_summaries = []

        for chunk in chunks:
            inputs = tokenizer(
                chunk,
                return_tensors="pt",
                max_length=1024,
                truncation=True,
            )

            summary_ids = model.generate(
                inputs["input_ids"],
                max_length=150,
                min_length=35,
                num_beams=4,
                do_sample=False,
            )

            summary = tokenizer.decode(
                summary_ids[0],
                skip_special_tokens=True,
            ).strip()

            if summary:
                chunk_summaries.append(summary)

        bart_text = " ".join(chunk_summaries)
        bart_sentences = _split_into_sentences(bart_text)
        original_sentences = _split_into_sentences(body)

        bullets = _select_diverse_sentences(
            original_sentences,
            bart_sentences,
            max_sentences=min(max_bullets, 5),
        )

        # Keep complete sentences and apply a word budget.
        final_bullets = []
        seen = set()
        total_words = 0
        word_budget = 140

        for sentence in bullets:
            sentence = _compact_sentence(sentence)
            normalized = _normalise_sentence(sentence)

            if not normalized or normalized in seen:
                continue

            sentence_words = len(sentence.split())
            if total_words + sentence_words > word_budget:
                continue

            seen.add(normalized)
            final_bullets.append(sentence)
            total_words += sentence_words

            if len(final_bullets) >= min(max_bullets, 5):
                break

        bullets = final_bullets
        raw_summary = " ".join(bullets)

    return Summary(
        bullet_points=bullets,
        raw_summary=raw_summary,
        original_word_count=original_word_count,
        summary_word_count=len(raw_summary.split()),
    )


def _compact_sentence(sentence: str) -> str:
    """Simplify selected repetitive wording and clean up punctuation."""
    sentence = sentence.strip()

    replacements = [
        (
            r"\bVice President Shri C\.\s*P\.\s*Radhakrishnan\b",
            "Vice President C. P. Radhakrishnan",
        ),
        (
            r"\bShri C\.\s*P\.\s*Radhakrishnan\b",
            "C. P. Radhakrishnan",
        ),
        (r"\bShri Narendra Modi\b", "Narendra Modi"),
        (r"\btoday urged\b", "urged"),
        (
            r"\bHighlighting Assam's healthcare progress,\s*",
            "",
        ),
        (
            r"\bHighlighting the transformation of India's healthcare sector,\s*",
            "",
        ),
        (
            r"\bsaid that the number of medical colleges in the State\b",
            "said the number of medical colleges in Assam",
        ),
        (
            r"\breferring to initiatives such as Ayushman Bharat\b",
            "including Ayushman Bharat",
        ),
    ]

    for pattern, replacement in replacements:
        sentence = re.sub(pattern, replacement, sentence, flags=re.IGNORECASE)

    sentence = re.sub(r"\s+", " ", sentence).strip()
    sentence = re.sub(r"\s+([,.!?;:])", r"\1", sentence)
    sentence = re.sub(r",\s*[,.!?]", ".", sentence)
    sentence = re.sub(r"[,.!?;:]+$", "", sentence).strip()
    sentence = re.sub(r"\bmore\s*than\b", "more than", sentence, flags=re.IGNORECASE)

    if sentence:
        sentence += "."

    return sentence


def _split_into_sentences(text: str) -> List[str]:
    """
    Sentence splitter that protects common abbreviations and initials,
    including names such as C. P. Radhakrishnan and A. P. J. Abdul Kalam.
    """
    text = text.strip()
    protected = re.sub(
        r"\b(Dr|Shri|Smt|Mr|Mrs|Ms|Prof)\.",
        r"\1<DOT>",
        text,
    )
    protected = re.sub(r"\b([A-Z])\.", r"\1<DOT>", protected)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", protected)
    return [part.replace("<DOT>", ".").strip() for part in parts if part.strip()]


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

    result = summarize_release(sample_title, sample_body, max_bullets=6)

    print("Original word count:", result.original_word_count)
    print("Summary word count:", result.summary_word_count)
    print("\nRaw summary:\n", result.raw_summary)
    print("\nBullet points:")
    for i, bullet in enumerate(result.bullet_points, start=1):
        print(f"{i}. {bullet}")
