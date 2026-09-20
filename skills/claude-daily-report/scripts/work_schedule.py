#!/usr/bin/env python3
"""Classify workdays for the current schedule.

Rules (Asia/Shanghai local dates):
- Regular week: Monday-Friday workdays, Saturday and Sunday rest (双休).
- First week of each month (the Monday-Sunday week that contains the 1st of a
  month): Saturday rest, Sunday is a workday. That Sunday's work is reported
  in the FOLLOWING Friday's weekly report (the Saturday-Friday cycle already
  guarantees this).
- Chinese statutory holidays override the base schedule: holiday dates are
  rest days, State Council makeup workdays (调休补班) are workdays even on
  weekends.

Holiday data must be updated once per year when the State Council notice
(国务院办公厅关于XXXX年部分节假日安排的通知) is published.
"""

import argparse
import json
from datetime import date, datetime, timedelta

# Source: 国办发明电〔2025〕7号, published 2025-11-04
# https://www.gov.cn/zhengce/content/202511/content_7047090.htm
HOLIDAYS = {
    2026: {
        "2026-01-01": "元旦", "2026-01-02": "元旦", "2026-01-03": "元旦",
        "2026-02-15": "春节", "2026-02-16": "春节", "2026-02-17": "春节",
        "2026-02-18": "春节", "2026-02-19": "春节", "2026-02-20": "春节",
        "2026-02-21": "春节", "2026-02-22": "春节", "2026-02-23": "春节",
        "2026-04-04": "清明节", "2026-04-05": "清明节", "2026-04-06": "清明节",
        "2026-05-01": "劳动节", "2026-05-02": "劳动节", "2026-05-03": "劳动节",
        "2026-05-04": "劳动节", "2026-05-05": "劳动节",
        "2026-06-19": "端午节", "2026-06-20": "端午节", "2026-06-21": "端午节",
        "2026-09-25": "中秋节", "2026-09-26": "中秋节", "2026-09-27": "中秋节",
        "2026-10-01": "国庆节", "2026-10-02": "国庆节", "2026-10-03": "国庆节",
        "2026-10-04": "国庆节", "2026-10-05": "国庆节", "2026-10-06": "国庆节",
        "2026-10-07": "国庆节",
    },
}

MAKEUP_WORKDAYS = {
    2026: {
        "2026-01-04": "元旦调休",
        "2026-02-14": "春节调休", "2026-02-28": "春节调休",
        "2026-05-09": "劳动节调休",
        "2026-09-20": "国庆节调休", "2026-10-10": "国庆节调休",
    },
}


def iso(day: date) -> str:
    return day.isoformat()


def week_monday(day: date) -> date:
    return day - timedelta(days=day.weekday())


def is_first_week(day: date) -> bool:
    monday = week_monday(day)
    return any((monday + timedelta(days=i)).day == 1 for i in range(7))


def holiday_name(day: date) -> str | None:
    return HOLIDAYS.get(day.year, {}).get(iso(day))


def makeup_name(day: date) -> str | None:
    return MAKEUP_WORKDAYS.get(day.year, {}).get(iso(day))


def is_workday(day: date) -> bool:
    if holiday_name(day):
        return False
    if makeup_name(day):
        return True
    if day.weekday() < 5:
        return True
    return day.weekday() == 6 and is_first_week(day)


def day_info(day: date) -> dict:
    return {
        "date": iso(day),
        "is_workday": is_workday(day),
        "week_type": "first_week" if is_first_week(day) else "regular",
        "holiday": holiday_name(day),
        "makeup_workday": makeup_name(day),
        "holiday_data_year_covered": day.year in HOLIDAYS,
    }


def schedule(day: date) -> dict:
    tomorrow = day + timedelta(days=1)
    month_week = (day.day - 1) // 7 + 1
    result = {
        **day_info(day),
        "week_monday": iso(week_monday(day)),
        "tomorrow": day_info(tomorrow),
        "friday_weekly_report_due": day.weekday() == 4,
        "reporting_year": day.year,
        "reporting_month": day.month,
        "month_week_number": month_week,
    }

    if day.weekday() == 4:
        period_start = day - timedelta(days=6)
        dates = [period_start + timedelta(days=offset) for offset in range(7)]
        result.update(
            {
                "weekly_period_start": iso(period_start),
                "weekly_period_end": iso(day),
                "weekly_period_end_exclusive": iso(day + timedelta(days=1)),
                "weekly_scheduled_workdays": [iso(d) for d in dates if is_workday(d)],
                "weekly_holidays": {iso(d): holiday_name(d) for d in dates if holiday_name(d)},
                "weekly_makeup_workdays": {iso(d): makeup_name(d) for d in dates if makeup_name(d)},
                "weekly_filename": f"month-{day.month:02d}-week-{month_week:02d}.md",
            }
        )

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Classify the double-rest schedule with first-week Sunday work and statutory holidays."
    )
    parser.add_argument("date", help="Local calendar date in YYYY-MM-DD format")
    args = parser.parse_args()
    day = datetime.strptime(args.date, "%Y-%m-%d").date()
    print(json.dumps(schedule(day), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
