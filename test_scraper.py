from datetime import date

from app.pib_scraper import list_releases


releases = list_releases(
    selected_date=date(2026, 9, 22)
)

print(f"Found {len(releases)} releases")

for release in releases[:5]:
    print(release.prid, "-", release.title)