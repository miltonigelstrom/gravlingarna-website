#!/usr/bin/env python3
"""
Grävlingarna — Google Reviews Updater
Hämtar omdömen från Google Places API och uppdaterar index.html.

Kör manuellt:  python3 update_reviews.py
Körs automatiskt varje måndag kl 09:00 via launchd.
"""

import json
import sys
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from html import escape

# ── Sökvägar ────────────────────────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "reviews-config.json"
INDEX_HTML  = SCRIPT_DIR / "index.html"
LOG_FILE    = SCRIPT_DIR / "reviews-update.log"

# ── Google Places API (New) ──────────────────────────────────────────────────
# languageCode=sv → tidsstämplar på svenska ("2 månader sedan")
PLACES_URL  = "https://places.googleapis.com/v1/places/{place_id}?languageCode=sv"
# originalText = recensionen på det språk kunden faktiskt skrev (ej maskinöversatt)
FIELD_MASK  = "displayName,rating,userRatingCount,reviews.authorAttribution,reviews.rating,reviews.relativePublishTimeDescription,reviews.text,reviews.originalText"


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        print(f"FEL: Konfigfilen saknas: {CONFIG_FILE}")
        print("Skapa reviews-config.json med dina uppgifter. Se reviews-config.example.json.")
        sys.exit(1)
    with open(CONFIG_FILE, encoding="utf-8") as f:
        cfg = json.load(f)
    if not cfg.get("api_key") or cfg["api_key"].startswith("DIN_"):
        print("FEL: api_key är inte satt i reviews-config.json")
        sys.exit(1)
    if not cfg.get("place_id") or cfg["place_id"].startswith("DIN_"):
        print("FEL: place_id är inte satt i reviews-config.json")
        sys.exit(1)
    return cfg


def fetch_place(api_key: str, place_id: str) -> dict:
    url = PLACES_URL.format(place_id=place_id)
    req = urllib.request.Request(url)
    req.add_header("X-Goog-Api-Key", api_key)
    req.add_header("X-Goog-FieldMask", FIELD_MASK)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"HTTP-fel {e.code}: {body}")
        sys.exit(1)
    except Exception as e:
        print(f"Nätverksfel: {e}")
        sys.exit(1)


def stars(rating: float) -> str:
    full = int(round(rating))
    return "★" * full + "☆" * (5 - full)


def build_review_card(review: dict) -> str:
    attr      = review.get("authorAttribution", {})
    author    = escape(attr.get("displayName", "Anonym"))
    photo_uri = attr.get("photoUri", "")
    rating    = review.get("rating", 5)
    # Föredra originalText (det språk kunden skrev på), fallback till text
    original  = review.get("originalText", {}).get("text", "").strip()
    fallback  = review.get("text", {}).get("text", "").strip()
    text_raw  = original if original else fallback
    when      = escape(review.get("relativePublishTimeDescription", ""))
    initial   = author[0].upper() if author else "?"

    # Förkorta extremt långa recensioner (CSS hanterar visuell trunkering)
    if len(text_raw) > 450:
        text_raw = text_raw[:447] + "…"
    text = escape(text_raw)

    # Avatar: profilbild om tillgänglig, annars initial-bokstav
    if photo_uri:
        avatar_html = (
            f'<img class="review-avatar" src="{escape(photo_uri)}" alt="{author}" '
            f"onerror=\"this.style.display='none';this.nextElementSibling.style.display='flex'\">"
            f'<div class="review-avatar-fb" style="display:none">{initial}</div>'
        )
    else:
        avatar_html = f'<div class="review-avatar-fb">{initial}</div>'

    # "Läs mer"-knapp för längre omdömen
    readmore = ""
    if len(text_raw) > 160:
        readmore = (
            '\n              <button class="review-readmore" '
            "onclick=\"this.previousElementSibling.classList.add('expanded');this.remove()\">"
            "Läs mer</button>"
        )

    return (
        f'            <div class="review">\n'
        f'              <div class="review-header">\n'
        f'                {avatar_html}\n'
        f'                <div class="review-name-wrap">\n'
        f'                  <span class="review-author">{author}</span>\n'
        f'                  <span class="review-when">{when}</span>\n'
        f'                </div>\n'
        f'                <span class="review-g">G</span>\n'
        f'              </div>\n'
        f'              <span class="review-stars">{stars(rating)}</span>\n'
        f'              <p class="review-body">"{text}"</p>{readmore}\n'
        f'            </div>'
    )


def build_reviews_block(place_data: dict) -> str:
    reviews       = place_data.get("reviews", [])
    total_ratings = place_data.get("userRatingCount", 0)
    avg_rating    = place_data.get("rating", 0)
    updated       = datetime.now().strftime("%Y-%m-%d")

    if not reviews:
        return (
            '      <p class="placeholder-note reveal">'
            "Inga omdömen hittades på Google.</p>"
        )

    star_count = int(round(avg_rating))
    big_stars  = "★" * star_count + "☆" * (5 - star_count)

    cards_html = "\n".join(build_review_card(r) for r in reviews)

    note = (
        f'      <p class="placeholder-note reveal">'
        f"Hämtade från Google · {total_ratings} omdömen totalt · Uppdaterat {updated}</p>"
    )

    google_logo = (
        '<span class="g-blue">G</span>'
        '<span class="g-red">o</span>'
        '<span class="g-yellow">o</span>'
        '<span class="g-blue">g</span>'
        '<span class="g-green">l</span>'
        '<span class="g-red">e</span>'
    )

    return (
        f'      <div class="reviews-outer reveal">\n'
        f'        <div class="reviews-sidebar">\n'
        f'          <div class="rs-label">Utmärkt</div>\n'
        f'          <div class="rs-stars">{big_stars}</div>\n'
        f'          <div class="rs-count">Baserat på {total_ratings} recensioner</div>\n'
        f'          <div class="rs-google">{google_logo}</div>\n'
        f'        </div>\n'
        f'        <div class="cr-outer">\n'
        f'          <div class="cr-wrap">\n'
        f'            <button class="cr-btn cr-prev" aria-label="Föregående" onclick="reviewsNav(-1)">&#8249;</button>\n'
        f'            <div class="cr-viewport">\n'
        f'              <div class="cr-track" id="reviewsTrack">\n'
        f'{cards_html}\n'
        f'              </div>\n'
        f'            </div>\n'
        f'            <button class="cr-btn cr-next" aria-label="Nästa" onclick="reviewsNav(1)">&#8250;</button>\n'
        f'          </div>\n'
        f'          <div class="cr-dots" id="reviewsDots"></div>\n'
        f'        </div>\n'
        f'      </div>\n'
        f'{note}'
    )


def update_index_html(block: str) -> bool:
    html = INDEX_HTML.read_text(encoding="utf-8")

    start_marker = "<!-- REVIEWS-START -->"
    end_marker   = "<!-- REVIEWS-END -->"

    start = html.find(start_marker)
    end   = html.find(end_marker)

    if start == -1 or end == -1:
        print("FEL: Hittade inte <!-- REVIEWS-START --> / <!-- REVIEWS-END --> i index.html")
        return False

    new_html = (
        html[: start + len(start_marker)]
        + "\n"
        + block
        + "\n      "
        + html[end:]
    )

    INDEX_HTML.write_text(new_html, encoding="utf-8")
    return True


def find_place_id(api_key: str, query: str):
    """Sök efter ett Place ID med ett företagsnamn (kör med --find-place)."""
    url  = "https://places.googleapis.com/v1/places:searchText"
    body = json.dumps({"textQuery": query}).encode()
    req  = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type",      "application/json")
    req.add_header("X-Goog-Api-Key",    api_key)
    req.add_header("X-Goog-FieldMask",  "places.id,places.displayName,places.formattedAddress")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP-fel {e.code}: {e.read().decode()}")
        sys.exit(1)

    places = data.get("places", [])
    if not places:
        print("Hittade inga platser. Prova ett mer exakt sökord.")
        return

    print(f"\nHittade {len(places)} resultat:\n")
    for p in places:
        pid  = p.get("id", "?")
        name = p.get("displayName", {}).get("text", "?")
        addr = p.get("formattedAddress", "")
        print(f"  Namn:     {name}")
        print(f"  Adress:   {addr}")
        print(f"  Place ID: {pid}")
        print()

    if len(places) == 1:
        pid = places[0]["id"]
        print(f'Lägg till detta i reviews-config.json:\n  "place_id": "{pid}"')


def main():
    # ── Läge: hitta Place ID ────────────────────────────────────────────────
    if "--find-place" in sys.argv:
        cfg = load_config()
        query = " ".join(sys.argv[sys.argv.index("--find-place") + 1:]) or \
                "Grävlingarna Trädgårdsentreprenad"
        print(f'Söker efter: "{query}"')
        find_place_id(cfg["api_key"], query)
        return

    # ── Normalläge: hämta recensioner och uppdatera index.html ─────────────
    print("=" * 50)
    print("Grävlingarna — Reviews Updater")
    print("=" * 50)

    cfg      = load_config()
    api_key  = cfg["api_key"]
    place_id = cfg["place_id"]

    log(f"Hämtar recensioner för place_id: {place_id}")
    place_data = fetch_place(api_key, place_id)

    reviews = place_data.get("reviews", [])
    log(f"Hittade {len(reviews)} recensioner (Google returnerar max 5)")

    block = build_reviews_block(place_data)

    if update_index_html(block):
        log("✓ index.html uppdaterad")
    else:
        log("✗ Misslyckades att uppdatera index.html")
        sys.exit(1)


if __name__ == "__main__":
    main()
