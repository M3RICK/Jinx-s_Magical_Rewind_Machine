from datetime import datetime


def detect_role(participant):
    role = (
        participant.get("teamPosition") or
        participant.get("individualPosition")
    )

    role_map = {
        "TOP": "TOP",
        "JUNGLE": "JUNGLE",
        "MIDDLE": "MIDDLE",
        "MID": "MIDDLE",
        "BOTTOM": "BOTTOM",
        "BOT": "BOTTOM",
        "UTILITY": "UTILITY",
        "SUPPORT": "UTILITY",
    }

    return role_map.get(role, "UNKNOWN")


def get_month_timestamps(year, month):
    start_date = datetime(year, month, 1)

    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())

    return start_timestamp, end_timestamp


def get_month_name(year, month):
    date = datetime(year, month, 1)
    return date.strftime("%B %Y")
