import os

from app.pib_scraper import list_releases, fetch_press_release
from app.summarizer import summarize_release
from app.Translator import translate_bullets
from app.tts import generate_speech


if __name__ == "__main__":

    print("=" * 70)
    print("PIB → SUMMARY → TRANSLATION → TTS")
    print("=" * 70)

    # ------------------------------------------------------------
    # STEP 1: Find current PIB releases
    # ------------------------------------------------------------

    print("\nSTEP 1: Finding current PIB releases...")

    releases = list_releases()

    if not releases:
        print("No PIB releases found.")
        exit()

    print(f"Found {len(releases)} releases.")

    for i, release in enumerate(releases[:5], start=1):
        print(f"{i}. {release.title}")
        print(f"   PRID: {release.prid}")

    # For now, automatically select the first release
    selected = releases[0]

    print("\nSelected release:")
    print(selected.title)
    print(f"PRID: {selected.prid}")

    # ------------------------------------------------------------
    # Create release-specific output folder
    # ------------------------------------------------------------

    release_folder = f"output/release_{selected.prid}"
    translations_folder = os.path.join(
        release_folder,
        "translations"
    )
    audio_folder = os.path.join(
        release_folder,
        "audio"
    )

    os.makedirs(translations_folder, exist_ok=True)
    os.makedirs(audio_folder, exist_ok=True)

    print(f"\nOutput folder: {release_folder}")

    # ------------------------------------------------------------
    # STEP 2: Fetch complete press release
    # ------------------------------------------------------------

    print("\nSTEP 2: Fetching press release...")

    release = fetch_press_release(selected.prid)

    if release is None:
        print("Failed to fetch press release.")
        exit()

    print(f"Title: {release.title}")
    print(f"Original words: {release.word_count}")

    # Save original release
    original_file = os.path.join(
        release_folder,
        "original.txt"
    )

    with open(original_file, "w", encoding="utf-8") as f:
        f.write(f"TITLE: {release.title}\n")
        f.write(f"PRID: {release.prid}\n")
        f.write(f"WORD COUNT: {release.word_count}\n")
        f.write("\n")
        f.write(release.body)

    print(f"Saved original release: {original_file}")

    # ------------------------------------------------------------
    # STEP 3: Summarize
    # ------------------------------------------------------------

    print("\nSTEP 3: Summarizing press release...")

    summary = summarize_release(
        release.title,
        release.body
    )

    print(f"Original words: {summary.original_word_count}")
    print(f"Summary words: {summary.summary_word_count}")

    print("\nSummary:")

    for i, bullet in enumerate(
        summary.bullet_points,
        start=1
    ):
        print(f"{i}. {bullet}")

    # Save summary
    summary_file = os.path.join(
        release_folder,
        "summary.txt"
    )

    with open(summary_file, "w", encoding="utf-8") as f:

        f.write(f"TITLE: {release.title}\n")
        f.write(f"PRID: {release.prid}\n")
        f.write(
            f"ORIGINAL WORD COUNT: "
            f"{summary.original_word_count}\n"
        )
        f.write(
            f"SUMMARY WORD COUNT: "
            f"{summary.summary_word_count}\n"
        )

        f.write("\nSUMMARY:\n")

        for i, bullet in enumerate(
            summary.bullet_points,
            start=1
        ):
            f.write(f"{i}. {bullet}\n")

    print(f"Saved summary: {summary_file}")

    # ------------------------------------------------------------
    # STEP 4: Translate
    # ------------------------------------------------------------

    print("\nSTEP 4: Translating summary...")

    languages = [
        "Hindi",
        "Telugu"
    ]

    translations = {}

    for language in languages:

        print(f"\nTranslating to {language}...")

        result = translate_bullets(
            summary.bullet_points,
            language
        )

        translations[language] = result

        print(f"{language} translation:")

        for i, bullet in enumerate(
            result.translated_bullets,
            start=1
        ):
            print(f"{i}. {bullet}")

        # Save translation
        translation_file = os.path.join(
            translations_folder,
            f"{language.lower()}.txt"
        )

        with open(
            translation_file,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(f"LANGUAGE: {language}\n")
            f.write(f"PRID: {release.prid}\n")
            f.write("\nTRANSLATION:\n")

            for i, bullet in enumerate(
                result.translated_bullets,
                start=1
            ):
                f.write(f"{i}. {bullet}\n")

        print(
            f"Saved translation: "
            f"{translation_file}"
        )

    # ------------------------------------------------------------
    # STEP 5: Generate speech
    # ------------------------------------------------------------

    print("\nSTEP 5: Generating audio...")

    for language, result in translations.items():

        narration_text = ". ".join(
            line.rstrip(".")
            for line in result.translated_bullets
        ) + "."

        audio_file = os.path.join(
            audio_folder,
            f"{language.lower()}.mp3"
        )

        print(f"Generating {language} audio...")

        generate_speech(
            narration_text,
            language,
            audio_file
        )

    # ------------------------------------------------------------
    # COMPLETED
    # ------------------------------------------------------------

    print("\n" + "=" * 70)
    print("FULL PIPELINE COMPLETED")
    print("=" * 70)

    print("\nGenerated files:")

    print(f"Original release:")
    print(f"  {original_file}")

    print(f"\nSummary:")
    print(f"  {summary_file}")

    print("\nTranslations:")
    for language in translations:
        print(
            f"  {os.path.join(translations_folder, language.lower() + '.txt')}"
        )

    print("\nAudio:")
    for language in translations:
        print(
            f"  {os.path.join(audio_folder, language.lower() + '.mp3')}"
        )