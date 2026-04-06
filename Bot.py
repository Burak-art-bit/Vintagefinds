import requests
import time
import random
from datetime import datetime

# ============================================================
# KONFIGURATION – nur hier anpassen!
# ============================================================
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1490761422093680801/tewkTldlSW8vd2wU_CmPf3011rp3p_5eqwFmp4kBCKCqAe9pH1Nj-W--a_69hl968sY_"  # <-- einfügen
VINTED_DOMAIN = "https://www.vinted.de"
CHECK_EVERY_SECONDS = 360  # 6 Minuten = ~10 Produkte/Stunde
# ============================================================

BRANDS = [
    "chanel", "prada", "gucci", "dior", "louis vuitton",
    "nike", "ralph lauren", "evisu", "levi's", "true religion"
]

BRAND_COLORS = {
    "chanel": 0x000000,
    "prada": 0x000000,
    "gucci": 0x00703C,
    "dior": 0x002D72,
    "louis vuitton": 0xA67C52,
    "nike": 0xFF6600,
    "ralph lauren": 0x002868,
    "evisu": 0x1C3F94,
    "levi's": 0xE31937,
    "true religion": 0x1C3F94,
}

seen_ids = set()


def get_session():
    """Erstellt eine neue Vinted-Session mit Cookie."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
        "Referer": VINTED_DOMAIN,
    })
    try:
        session.get(VINTED_DOMAIN, timeout=10)
    except Exception as e:
        print(f"Session-Fehler: {e}")
    return session


def search_vinted(session, brand):
    """Sucht nach neuen Artikeln für eine Brand."""
    url = f"{VINTED_DOMAIN}/api/v2/catalog/items"
    params = {
        "search_text": brand,
        "order": "newest_first",
        "per_page": 5,
    }
    try:
        resp = session.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            return resp.json().get("items", [])
        elif resp.status_code == 401:
            print(f"Session abgelaufen, wird erneuert...")
            return None  # Signal für Session-Erneuerung
    except Exception as e:
        print(f"Fehler bei [{brand}]: {e}")
    return []


def send_to_discord(item, brand):
    """Sendet ein Produkt als Discord Embed mit Link-Button."""
    try:
        photo = item.get("photo", {})
        image_url = photo.get("url", photo.get("full_size_url", ""))
        
        price_val = item.get("price", "?")
        currency = item.get("currency", "EUR")
        price_str = f"{price_val} {currency}"
        
        size = item.get("size_title", "Keine Angabe")
        title = item.get("title", "Unbekannt")
        item_id = item.get("id")
        item_url = f"{VINTED_DOMAIN}/items/{item_id}"
        condition = item.get("status", "")
        
        color = BRAND_COLORS.get(brand.lower(), 0xFF6B00)
        
        embed = {
            "title": f"🛍️ {title}",
            "url": item_url,  # Titel wird klickbarer Link!
            "description": f"[➡️ **Direkt zum Produkt auf Vinted klicken**]({item_url})",
            "color": color,
            "fields": [
                {"name": "💶 Preis", "value": f"**{price_str}**", "inline": True},
                {"name": "📏 Größe", "value": size, "inline": True},
                {"name": "🏷️ Marke", "value": brand.title(), "inline": True},
                {"name": "✅ Zustand", "value": condition if condition else "k.A.", "inline": True},
            ],
            "thumbnail": {"url": image_url},
            "footer": {
                "text": f"Vinted Sniper • {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr"
            }
        }
        
        payload = {"embeds": [embed]}
        resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        
        if resp.status_code == 204:
            print(f"  ✅ Gesendet: {title[:40]}... | {price_str}")
        else:
            print(f"  ⚠️ Discord Fehler: {resp.status_code}")
            
    except Exception as e:
        print(f"Discord-Fehler: {e}")


def run():
    print("=" * 50)
    print("🚀 VINTED SNIPER GESTARTET")
    print(f"🏷️  Brands: {', '.join(b.title() for b in BRANDS)}")
    print(f"⏱️  Intervall: ~{CHECK_EVERY_SECONDS}s")
    print("=" * 50)

    session = get_session()
    cycle = 0

    while True:
        cycle += 1
        print(f"\n🔍 Suchdurchlauf #{cycle} — {datetime.now().strftime('%H:%M:%S')}")
        items_found = 0

        # Session alle 20 Zyklen erneuern
        if cycle % 20 == 0:
            print("🔄 Session wird erneuert...")
            session = get_session()

        for brand in BRANDS:
            result = search_vinted(session, brand)
            
            if result is None:  # Session abgelaufen
                session = get_session()
                result = search_vinted(session, brand) or []

            for item in result:
                item_id = item.get("id")
                if item_id and item_id not in seen_ids:
                    seen_ids.add(item_id)
                    send_to_discord(item, brand)
                    items_found += 1
                    time.sleep(random.uniform(3, 6))  # Anti-Spam

            # Pause zwischen Brands
            time.sleep(random.uniform(20, 35))

        print(f"📦 {items_found} neue Artikel gefunden")
        print(f"💤 Warte {CHECK_EVERY_SECONDS}s bis zum nächsten Durchlauf...")
        time.sleep(CHECK_EVERY_SECONDS)


if __name__ == "__main__":
    run()
