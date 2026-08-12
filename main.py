import os
import requests
from datetime import datetime

FOOTBALL_DATA_TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = "@hcaza"

COMPETITIONS = {
    "PL": "🇬🇧 لیگ برتر انگلیس",
    "PD": "🇪🇸 لالیگا",
    "BL1": "🇩🇪 بوندس‌لیگا",
    "SA": "🇮🇹 سری آ",
    "FL1": "🇫🇷 لیگ ۱ فرانسه",
    "CL": "🇪🇺 لیگ قهرمانان اروپا",
}

def get_matches():
    headers = {
        "X-Auth-Token": FOOTBALL_DATA_TOKEN
    }

    response = requests.get(
        "https://api.football-data.org/v4/matches",
        headers=headers,
        timeout=20
    )

    response.raise_for_status()
    return response.json().get("matches", [])

def get_extra_matches():
    today = datetime.utcnow().strftime("%Y-%m-%d")

    response = requests.get(
        "https://www.thesportsdb.com/api/v1/json/123/eventsday.php",
        params={
            "d": today,
            "s": "Soccer"
        },
        timeout=20
    )

    response.raise_for_status()
    data = response.json()

    return data.get("events") or []

def is_relevant_extra_match(event):
    league = (event.get("strLeague") or "").lower()

    wanted_competitions = [
        "fa cup",
        "league cup",
        "efl cup",
        "community shield",
        "copa del rey",
        "supercopa",
        "dfb-pokal",
        "dfb pokal",
        "coppa italia",
        "supercoppa",
        "coupe de france",
        "trophee des champions",
        "trophée des champions",
        "club friendlies",
        "club friendly",
    ]

    return any(
        competition in league
        for competition in wanted_competitions
    )

def format_match(match):
    competition_code = match["competition"]["code"]
    competition = COMPETITIONS.get(
        competition_code,
        match["competition"]["name"]
    )

    home = match["homeTeam"]["name"]
    away = match["awayTeam"]["name"]
    status = match["status"]

    score = match["score"]["fullTime"]
    home_score = score["home"]
    away_score = score["away"]

    if home_score is not None and away_score is not None:
        match_info = f"{home}  {home_score} - {away_score}  {away}"
    else:
        utc_date = match["utcDate"]

        dt = datetime.fromisoformat(
            utc_date.replace("Z", "+00:00")
        )

        match_info = (
            f"{home} - {away}\n"
            f"🕒 {dt.strftime('%H:%M')} UTC"
        )

    status_fa = {
        "FINISHED": "🏁 پایان بازی",
        "IN_PLAY": "🔴 در حال برگزاری",
        "PAUSED": "⏸ پایان نیمه اول",
        "TIMED": "⏳ برگزار نشده",
        "SCHEDULED": "⏳ برگزار نشده",
    }.get(status, status)

    return (
        f"{competition}\n"
        f"⚽️ {match_info}\n"
        f"{status_fa}"
    )

def format_extra_match(event):
    competition = event.get("strLeague") or "مسابقه فوتبال"
    home = event.get("strHomeTeam") or "تیم میزبان"
    away = event.get("strAwayTeam") or "تیم مهمان"

    home_score = event.get("intHomeScore")
    away_score = event.get("intAwayScore")

    event_time = event.get("strTime") or ""
    event_status = event.get("strStatus") or ""

    if home_score is not None and away_score is not None:
        match_info = f"{home}  {home_score} - {away_score}  {away}"
    else:
        match_info = f"{home} - {away}"

        if event_time:
            match_info += f"\n🕒 {event_time}"

    status_fa = {
        "Match Finished": "🏁 پایان بازی",
        "Finished": "🏁 پایان بازی",
        "In Progress": "🔴 در حال برگزاری",
        "Not Started": "⏳ برگزار نشده",
    }.get(event_status, "⏳ زمان‌بندی شده")

    return (
        f"🏆 {competition}\n"
        f"⚽️ {match_info}\n"
        f"{status_fa}"
    )

def send_telegram(text):
    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    response = requests.post(
        url,
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "disable_web_page_preview": True,
        },
        timeout=20
    )

    response.raise_for_status()


def main():
    matches = get_matches()
    extra_matches = get_extra_matches()
    print(f"Extra source returned {len(extra_matches)} events.")
    relevant_extra_matches = [
        event
        for event in extra_matches
        if is_relevant_extra_match(event)
    ]

    print(
        f"Relevant extra matches: {len(relevant_extra_matches)}"
    )
    selected_matches = [
        match
        for match in matches
        if match["competition"]["code"] in COMPETITIONS
    ]

    if not selected_matches and not relevant_extra_matches:
        send_telegram(
            "✅ اتصال کامل شد\n\n"
            "بات فوتبال HCaza با موفقیت به GitHub Actions و تلگرام متصل شد.\n\n"
            "⚽️ امروز از رقابت‌های انتخاب‌شده بازی‌ای برای انتشار پیدا نشد."
        )
        print("Test message sent successfully.")
        return

    message = "⚽️ بازی‌های مهم امروز\n\n"

    message += "\n\n".join(
        format_match(match)
        for match in selected_matches
    )

    if relevant_extra_matches:
        message += "\n\n🏆 جام‌ها و بازی‌های دوستانه\n\n"
        message += "\n\n".join(
            format_extra_match(event)
            for event in relevant_extra_matches
        )
    send_telegram(message)

    print(
        f"{len(selected_matches)} matches sent successfully."
    )


if __name__ == "__main__":
    main()
