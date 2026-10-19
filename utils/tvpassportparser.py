from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup

def parse_schedule(html: str, time_zone: ZoneInfo) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    programs = []

    # Verify the selected timezone
    selector = soup.select_one("#timezone_selector")
    if selector:
        selected = selector.select_one("option[selected]")
        print("Selected timezone:", selected.get_text(strip=True) if selected else "Not marked")
    else:
        print("Timezone selector not found")

    for item in soup.select("div.list-group-item[data-st][data-showname]"):
        start_str = item.get("data-st")
        duration_str = item.get("data-duration")

        if not start_str or not duration_str:
            continue

        # TV Passport timestamps are Eastern local time
        local_start = datetime.strptime(
            start_str, "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=time_zone)

        duration = int(duration_str)
        local_end = local_start + timedelta(minutes=duration)

        # Convert to UTC for XMLTV
        start_utc = local_start.astimezone(timezone.utc)
        end_utc = local_end.astimezone(timezone.utc)

        programs.append({
            "title": item.get("data-showname", ""),
            "subtitle": item.get("data-episodetitle") or None,
            "episode_number": item.get("data-episodenumber") or None,
            "description": item.get("data-description") or None,
            "rating": item.get("data-rating") or None,
            "category": item.get("data-showtype") or None,
            "listing_id": item.get("data-listingid") or None,
            "start": start_utc,
            "stop": end_utc,
        })

    return sorted(programs, key=lambda p: p["start"])