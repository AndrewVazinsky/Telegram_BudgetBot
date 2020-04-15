"""Work with expenses - adding, deleting, statistics"""

import datetime
import re
from typing import List, NamedTuple, Optional

import pytz

import db
import exceptions
from categories import Categories


class Message(NamedTuple):
    """Structure of a parsed message about a new expense"""
    amount: int
    category_text: str


class Expense(NamedTuple):
    """The structure of the new expense added to the database"""
    id: Optional[int]
    amount: int
    category_name: str


def add_expense(raw_message: str) -> Expense:
    """Adds a new message. Accepts a text message came in the boat."""
    parsed_message = _parse_message(raw_message)
    category = Categories().get_category(parsed_message.category_text)
    inserted_row_id = db.insert("expense",
                                {"amount": parsed_message.amount,
                                 "created": _get_now_formatted(),
                                 "category_codename": category.codename,
                                 "raw_text": raw_message}
                                )
    return Expense(id=None,
                   amount=parsed_message.amount,
                   category_name=category.name)


def get_today_statistics() -> str:
    """Returns a string of statistics on expenses for today"""
    cursor = db.get_cursor()
    cursor.execute("select sum(amount)"
                   "from expense where date(created)=date('now', 'localtime')")
    result = cursor.fetchone()
    if not result[0]:
        return "No expenses yet"
    all_today_expenses = result[0]
    cursor.execute("select sum(amount) from expense where date(created)=date('now', 'localtime') "
                   "and category_codename in (select codename from category where is_base_expense=true)")
    result = cursor.fetchone()
    base_today_expenses = result[0] if result[0] else 0
    return (f"Today's expenses:\n"
            f"total - {all_today_expenses} hrn.\n"
            f"base expenses - {base_today_expenses} hrn. out of {_get_budget_limit()} hrn.\n\n"
            f"For the current month: /month")


def get_previous_month_statistics() -> str:
    """Returns a string of statistics on expenses for the previous month"""
    now = _get_now_datetime()
    prev_last_day = now.replace(day=1) - datetime.timedelta(days=1)
    prev_first_day = prev_last_day.replace(day=1)
    first_day_of_previous_month = f'{prev_first_day.year:04d}-{prev_first_day.month:02d}-01'
    last_day_of_previous_month = f'{prev_last_day.year:04d}-{prev_last_day.month:02d}-{prev_last_day.day}'
    cursor = db.get_cursor()
    cursor.execute(f"select sum(amount) "
                   f"from expense where date(created) "
                   f"between '{first_day_of_previous_month}' and '{last_day_of_previous_month}'")
    result = cursor.fetchone()
    if not result[0]:
        return "There were no expenses in previous month"
    all_prev_month_expenses = result[0]
    cursor.execute(f"select sum(amount) "
                   f"from expense where date(created) >= '{first_day_of_previous_month}' "
                   f"and date(created) <= '{last_day_of_previous_month}' "
                   f"and category_codename in (select codename "
                   f"from category where is_base_expense=true)")
    result = cursor.fetchone()
    base_prev_month_expenses = result[0] if result[0] else 0
    return (f"Previous month expenses:\n"
            f"total - {all_prev_month_expenses} hrn.\n"
            f"base expenses - {base_prev_month_expenses} hrn. out of {prev_first_day.day * _get_budget_limit()} hrn.")


def get_month_statistics() -> str:
    """Returns a string of statistics on expenses for the current month"""
    now = _get_now_datetime()
    first_day_of_month = f'{now.year:04d}-{now.month:02d}-01'
    cursor = db.get_cursor()
    cursor.execute(f"select sum(amount) "
                   f" from expense where date(created) >= '{first_day_of_month}'")
    result = cursor.fetchone()
    if not result[0]:
        return "There are no expenses yet this month"
    all_today_expenses = result[0]
    cursor.execute(f"select sum(amount) "
                   f" from expense where date(created) >= '{first_day_of_month}'"
                   f"and category_codename in (select codename "
                   f"from category where is_base_expense=true)")
    result = cursor.fetchone()
    base_today_expenses = result[0] if result[0] else 0
    return (f"Current month expenses:\n"
            f"total - {all_today_expenses} hrn.\n"
            f"base expenses - {base_today_expenses} hrn. out of {now.day * _get_budget_limit()} hrn.")


def last() -> List[Expense]:
    """Returns the last few expenses"""
    cursor = db.get_cursor()
    cursor.execute(
        "select e.id, e.amount, c.name "
        "from expense e left join category c "
        "on c.codename=e.category_codename "
        "order by created desc limit 10")
    rows = cursor.fetchall()
    last_expenses = [Expense(id=row[0], amount=row[1], category_name=row[2]) for row in rows]
    return last_expenses


def delete_expense(row_id: int) -> None:
    """Deletes the message by its identifier"""
    db.delete("expense", row_id)


def _parse_message(raw_message: str) -> Message:
    """Parses the text of a message about a new expense"""
    regexp_result = re.match(r"([\d ]+) (.*)", raw_message)
    if not regexp_result or not regexp_result.group(0) \
            or not regexp_result.group(1) or not regexp_result.group(2):
        raise exceptions.NotCorrectMessage("I can not understand the message. Write a message in a format, "
                                           "e.g.:\n1000 cafe")

    amount = int(regexp_result.group(1).replace(" ", ""))
    category_text = regexp_result.group(2).strip().lower()
    return Message(amount=amount, category_text=category_text)


def _get_now_formatted() -> str:
    """Returns today's date as a string"""
    return _get_now_datetime().strftime("%Y-%m-%d %H:%M:%S")


def _get_now_datetime() -> datetime.datetime:
    """Returns today's datetime taking into account the time zone of Kiev time"""
    tz = pytz.timezone("Europe/Kiev")
    now = datetime.datetime.now(tz)
    return now


def _get_budget_limit() -> int:
    """Returns daily spending limit for basic base spending"""
    return db.fetchall("budget", ["daily_limit"])[0]["daily_limit"]
