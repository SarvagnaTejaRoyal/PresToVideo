from app.pib_scraper import list_releases, fetch_press_release
from app.summarizer import summarize_release


if __name__ == "__main__":

    print("=" * 70)
    print("STEP 1: DISCOVERING CURRENT PIB PRESS RELEASES")
    print("=" * 70)

    listings = list_releases()

    if not listings:
        print("No PIB releases found.")
        exit()

    print(f"\nFound {len(listings)} releases.\n")

    # Show the first 10 currently available releases
    for i, listing in enumerate(listings[:10], start=1):
        print(f"{i}. {listing.title}")
        print(f"   PRID: {listing.prid}")

    # Select the newest release
    selected = listings[0]

    print("\n" + "=" * 70)
    print("STEP 2: FETCHING SELECTED PIB RELEASE")
    print("=" * 70)

    print(f"Selected title: {selected.title}")
    print(f"Selected PRID: {selected.prid}")

    release = fetch_press_release(selected.prid)

    if release is None:
        print("Failed to fetch the selected press release.")
        exit()

    print(f"\nTitle: {release.title}")
    print(f"Original words: {release.word_count}")

    print("\nOriginal Body:")
    print(release.body)

    print("\n" + "=" * 70)
    print("STEP 3: SUMMARIZING PRESS RELEASE")
    print("=" * 70)

    summary = summarize_release(
        release.title,
        release.body
    )

    print(f"Original word count: {summary.original_word_count}")
    print(f"Summary word count: {summary.summary_word_count}")

    print("\nSummary:")
    print(summary.raw_summary)

    print("\nBullet Points:")
    for i, bullet in enumerate(summary.bullet_points, start=1):
        print(f"{i}. {bullet}")

    print("\n" + "=" * 70)
    print("PIB → SUMMARIZER TEST COMPLETED")
    print("=" * 70)