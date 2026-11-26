"""
pib_scraper.py

Stage 1 of the pipeline: discovers today's PIB press releases and
extracts a clean title + body for any given release.

Two capabilities:
  - list_releases(): discovers all currently-listed releases (title +
    PRID) from PIB's "All Releases" page. Powers the browsable list
    in the UI -- no polling/scheduling needed, called live whenever
    the user opens the app or clicks refresh.
  - fetch_press_release(prid): fetches and extracts one release's
    full title + body, given its PRID.

KEY FINDING (from the team's own exploration): the URL you see in a
browser's address bar, PressReleaseDetail.aspx, is a JS wrapper page
that fetches the real article via AJAX from a different URL:

    PressReleasePage.aspx?PRID=<prid>

That inner page is plain, server-rendered HTML -- fetchable directly
with `requests`, no headless browser required. Hitting the wrapper
URL directly is what caused "JavaScript must be enabled" fallback
content in earlier debugging; hitting the real content URL avoids
the problem entirely.

A Playwright-based fallback is included further down for the rare
case the plain-requests approach ever stops working, but it should
not be needed as the primary path.
"""

import re
import time
from dataclasses import dataclass
from typing import List, Optional

from datetime import date

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.pib.gov.in"
ALL_RELEASES_URL = f"{BASE_URL}/allRel.aspx"
DETAIL_URL = f"{BASE_URL}/PressReleaseDetail.aspx"      # wrapper page (JS-dependent, avoid)
CONTENT_URL = f"{BASE_URL}/PressReleasePage.aspx"        # actual article HTML (fetch this)
DEFAULT_TIMEOUT = 20

# Small delay between consecutive requests -- cheap insurance against
# looking like a bot, kept even though the real fix was the URL change.
REQUEST_DELAY_SECONDS = 1.5

_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
})

_warmed_up = False


def _warm_up_session() -> None:
    """Visits the homepage once to pick up cookies before hitting other pages."""
    global _warmed_up
    if _warmed_up:
        return
    try:
        _SESSION.get(BASE_URL, timeout=DEFAULT_TIMEOUT)
        _SESSION.headers["Referer"] = BASE_URL + "/"
        _warmed_up = True
        time.sleep(REQUEST_DELAY_SECONDS)
    except requests.exceptions.RequestException as exc:
        print(f"[_warm_up_session] Warm-up request failed (continuing anyway): {exc}")


def _polite_get(url: str, timeout: int = DEFAULT_TIMEOUT) -> requests.Response:
    """A requests.get() that warms up the session first and paces requests."""
    _warm_up_session()
    response = _SESSION.get(url, timeout=timeout)
    time.sleep(REQUEST_DELAY_SECONDS)
    return response


@dataclass
class ReleaseListing:
    """One entry in the browsable list of releases (no body text yet)."""
    prid: str
    title: str


@dataclass
class PressRelease:
    """Full result of successfully scraping a single press release."""
    prid: str
    title: str
    body: str
    word_count: int
    reg: str
    lang: str
    url: str


# ============================================================
# DISCOVERY: list currently-available releases
# ============================================================

def list_releases(
    reg: str = "48",
    lang: str = "1",
    selected_date: Optional[date] = None,
    timeout: int = DEFAULT_TIMEOUT
) -> List[ReleaseListing]:
    """
    Fetches PIB's "All Releases" page and returns every release
    currently listed there (title + PRID), in the order PIB shows
    them (newest first).

    Call this live, on demand -- when the user opens the app or
    clicks a refresh button. No background polling needed.
    """

    url = f"{ALL_RELEASES_URL}?reg={reg}&lang={lang}"

    try:
        # First GET: load the PIB page and ASP.NET hidden fields
        response = _polite_get(url, timeout=timeout)
        response.raise_for_status()

        # If no date was requested, keep the old behavior
        if selected_date is None:
            soup = BeautifulSoup(response.text, "lxml")

    # IMPORTANT: all of this must be INSIDE the for loop -- an earlier
    # version of this function had prid-extraction accidentally
    # de-indented to run only once, after the loop, using leftover
    # variables from the last link. That silently broke the whole list.

        else:
            soup = BeautifulSoup(response.text, "lxml")

            # Collect ASP.NET hidden form fields
            form_data = {}

            for hidden in soup.select("input[type='hidden']"):
                name = hidden.get("name")
                if name:
                    form_data[name] = hidden.get("value", "")

            # PIB's form values
            form_data.update({
                "ctl00$Bar1$ddlregion": reg,
                "ctl00$Bar1$ddlLang": lang,
                "ctl00$ContentPlaceHolder1$hydregionid": "3",
                "ctl00$ContentPlaceHolder1$hydLangid": lang,
                "ctl00$ContentPlaceHolder1$ddlMinistry": "0",

                "ctl00$ContentPlaceHolder1$ddlday":
                    str(selected_date.day),

                "ctl00$ContentPlaceHolder1$ddlMonth":
                    str(selected_date.month),

                "ctl00$ContentPlaceHolder1$ddlYear":
                    str(selected_date.year),

                "__EVENTTARGET":
                    "ctl00$ContentPlaceHolder1$ddlday",

                "__EVENTARGUMENT": "",
            })

            # Send the same type of postback that PIB uses
            response = _SESSION.post(
                url,
                data=form_data,
                timeout=timeout,
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

    except requests.exceptions.RequestException as exc:
        print(f"[list_releases] Failed to fetch release list: {exc}")
        return []

    listings: List[ReleaseListing] = []
    seen_prids = set()

    for link in soup.find_all("a"):
        href = link.get("href", "")
        onclick = link.get("onclick", "")
        title = link.get_text(" ", strip=True)

        prid = None

        match = re.search(
            r"PRID=(\d+)",
            href,
            re.IGNORECASE
        )

        if match:
            prid = match.group(1)

        if not prid:
            match = re.search(
                r"Bind_PressReleaseDetails\s*\(\s*(\d+)\s*\)",
                onclick,
                re.IGNORECASE,
            )

            if match:
                prid = match.group(1)

        if prid and title and prid not in seen_prids:
            seen_prids.add(prid)

            listings.append(
                ReleaseListing(
                    prid=prid,
                    title=title
                )
            )

    return listings

# ============================================================
# DETAIL: fetch and extract one release's full text
# ============================================================

def fetch_press_release(
    prid: str,
    reg: str = "48",
    lang: str = "1",
    timeout: int = DEFAULT_TIMEOUT,
    use_browser_fallback: bool = True,
) -> Optional[PressRelease]:
    """
    Fetch and parse a single PIB press release by PRID.

    Primary path: plain `requests` against PressReleasePage.aspx --
    the actual server-rendered content URL, not the JS wrapper.

    If that returns no body AND use_browser_fallback is True, falls
    back to a headless-browser render (see _fetch_rendered_html) as
    a safety net. This keeps the common case fast and dependency-light
    while still having a way out if PIB's behavior changes.
    """
    url = f"{CONTENT_URL}?PRID={prid}"

    try:
        response = _polite_get(url, timeout=timeout)
        response.raise_for_status()
        html = response.text
    except requests.exceptions.RequestException as exc:
        print(f"[fetch_press_release] Failed to fetch PRID {prid}: {exc}")
        return None

    result = _parse_release_html(html, prid, reg, lang, url)
    if result:
        return result

    if use_browser_fallback:
        print(f"[fetch_press_release] Plain fetch gave no body for PRID {prid}, "
              f"trying headless-browser fallback...")
        try:
            html = _fetch_rendered_html(f"{DETAIL_URL}?PRID={prid}&reg={reg}&lang={lang}",
                                         timeout_ms=timeout * 1000)
            return _parse_release_html(html, prid, reg, lang, url)
        except Exception as exc:
            print(f"[fetch_press_release] Browser fallback also failed for PRID {prid}: {exc}")
            return None

    print(f"[fetch_press_release] No body extracted for PRID {prid}.")
    return None


def _parse_release_html(html: str, prid: str, reg: str, lang: str, url: str) -> Optional[PressRelease]:
    soup = BeautifulSoup(html, "lxml")

    title = _extract_title(soup)
    if not title:
        return None

    body = _extract_body(soup)
    if not body:
        return None

    return PressRelease(
        prid=prid, title=title, body=body,
        word_count=len(body.split()), reg=reg, lang=lang, url=url,
    )


def get_latest_release(reg: str = "48", lang: str = "1", max_attempts: int = 5) -> Optional[PressRelease]:
    """
    Convenience wrapper: list releases, then fetch the newest one that
    actually works, skipping any that fail extraction.
    """
    listings = list_releases(reg=reg, lang=lang)
    if not listings:
        raise RuntimeError("No PIB release links were found.")

    for listing in listings[:max_attempts]:
        result = fetch_press_release(listing.prid, reg=reg, lang=lang)
        if result:
            return result
        print(f"[get_latest_release] Skipping PRID {listing.prid} "
              f"(\"{listing.title[:50]}...\") -- could not extract body.")

    print(f"[get_latest_release] None of the first {max_attempts} releases could be scraped.")
    return None


def _extract_title(soup: BeautifulSoup) -> str:
    """Title lives in the og:title meta tag -- cleaner than scraping <h1>."""
    title_tag = soup.find("meta", property="og:title")
    if title_tag and title_tag.get("content"):
        return title_tag["content"].strip()
    return ""


def _extract_body(soup: BeautifulSoup) -> str:
    """
    Walk backward from #ReleaseId collecting every <p> before it,
    then clean up separators/reference codes/duplicates.
    """
    release_id_element = soup.find(id="ReleaseId")
    if not release_id_element:
        return ""

    paragraphs = []
    for p in release_id_element.find_all_previous("p"):
        if p.find_parent(class_=re.compile(r"(twitter|x-post|social)", re.IGNORECASE)):
            continue
        text = p.get_text(" ", strip=True)
        if text:
            paragraphs.append(text)

    paragraphs.reverse()
    return _clean_paragraphs(paragraphs)


def _clean_paragraphs(paragraphs: List[str]) -> str:
    separator_pattern = re.compile(r"[*]+")
    reference_code_pattern = re.compile(r"[A-Z]{2,10}(?:/[A-Z]{2,10}){1,4}")

    clean_paragraphs: List[str] = []
    seen: set = set()

    for text in paragraphs:
        text = text.strip()
        if not text:
            continue
        if separator_pattern.fullmatch(text):
            continue
        if reference_code_pattern.fullmatch(text):
            continue

        normalized = re.sub(r"\s+", " ", text).strip()
        if normalized in seen:
            continue
        seen.add(normalized)
        clean_paragraphs.append(text)

    return "\n\n".join(clean_paragraphs)


# ============================================================
# FALLBACK ONLY: headless-browser render (Playwright)
# Not used unless the plain-requests path above fails.
# ============================================================

def _fetch_rendered_html(url: str, timeout_ms: int = 20000) -> str:
    from playwright.sync_api import sync_playwright

    match = re.search(r"PRID=(\d+)", url, re.IGNORECASE)
    if not match:
        raise ValueError(f"Could not find PRID in URL: {url}")
    prid = match.group(1)
    release_page_url = f"{CONTENT_URL}?PRID={prid}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=_SESSION.headers["User-Agent"])
        try:
            page.goto(release_page_url, timeout=timeout_ms, wait_until="domcontentloaded")
            page.wait_for_timeout(1500)
            html = page.content()
        finally:
            browser.close()
    return html


def debug_page_structure(prid: str) -> None:
    """Diagnostic helper: fetch via the plain-requests path and report what's found."""
    url = f"{CONTENT_URL}?PRID={prid}"
    response = _polite_get(url)
    print("URL fetched:", url)
    print("Status code:", response.status_code)
    print("Content length:", len(response.text))

    soup = BeautifulSoup(response.text, "lxml")
    release_id_element = soup.find(id="ReleaseId")
    print("\n#ReleaseId found:", release_id_element is not None)

    all_p_tags = soup.find_all("p")
    print("Total <p> tags on page:", len(all_p_tags))

    if release_id_element:
        p_before = release_id_element.find_all_previous("p")
        print("<p> tags found BEFORE #ReleaseId:", len(p_before))
        for i, p in enumerate(p_before[:5], start=1):
            print(f"  [{i}]", p.get_text(" ", strip=True)[:80])

    title_tag = soup.find("meta", property="og:title")
    print("\nog:title found:", title_tag.get("content") if title_tag else None)


if __name__ == "__main__":
    print("=" * 70)
    print("PIB RELEASE SCRAPER")
    print("=" * 70)

    listings = list_releases()
    print(f"\nFound {len(listings)} releases:\n")
    for i, listing in enumerate(listings[:10], start=1):
        print(f"{i}. {listing.title}\n   PRID: {listing.prid}")

    if listings:
        print("\n" + "=" * 70)
        print("FETCHING LATEST RELEASE")
        print("=" * 70)
        result = fetch_press_release(listings[0].prid)
        if result:
            print("\nTITLE:", result.title)
            print("WORD COUNT:", result.word_count)
            print("\nBODY:\n", result.body)
        else:
            print(f"Failed to fetch PRID {listings[0].prid}")