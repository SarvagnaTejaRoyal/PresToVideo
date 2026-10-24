from app.pib_scraper import fetch_press_release

release = fetch_press_release("2306930")

if release:
    print("Title:", release.title)
    print("Word count:", release.word_count)
    print("\nBody:\n", release.body)
else:
    print("Failed to fetch PRID 2306930")