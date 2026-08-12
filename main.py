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
    return response.json()["matches"]


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

    selected_matches = [
        match
        for match in matches
        if match["competition"]["code"] in COMPETITIONS
    ]

    if not selected_matches:
        print("No supported matches today.")
        return

    message = "⚽️ بازی‌های مهم امروز\n\n"

    message += "\n\n".join(
        format_match(match)
        for match in selected_matches
    )

    send_telegram(message)

    print(
        f"{len(selected_matches)} matches sent successfully."
    )


if __name__ == "__main__":
    main()
