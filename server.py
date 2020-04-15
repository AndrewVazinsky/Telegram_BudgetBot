"""Telegram bot server launched directly"""
import logging
# import os

from aiogram import Bot, Dispatcher, executor, types

import exceptions
import expenses
from categories import Categories
from middlewares import AccessMiddleware
from config import TELEGRAM_API_TOKEN, TELEGRAM_ACCESS_ID

logging.basicConfig(level=logging.INFO)

# API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
# ACCESS_ID = os.getenv("TELEGRAM_ACCESS_ID")

bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(AccessMiddleware(TELEGRAM_ACCESS_ID))


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """Sends a welcome message and bot help"""
    await message.answer(
        "Bot for accounting expenses\n\n"
        "To add expense: 250 taxi\n"
        "Today's statistics: /today\n"
        "Current month's statistics: /month\n"
        "Previous month's statistics: /previous\n"
        "Last added expenses: /expenses\n"
        "Categories of expenditure: /categories")


@dp.message_handler(lambda message: message.text.startswith('/del'))
async def del_expense(message: types.Message):
    """Deletes one expense record by its identifier"""
    row_id = int(message.text[4:])
    expenses.delete_expense(row_id)
    answer_message = "Expense Deleted"
    await message.answer(answer_message)


@dp.message_handler(commands=['categories'])
async def categories_list(message: types.Message):
    """Sends a list of expense categories"""
    categories = Categories().get_all_categories()
    answer_message = "Expense categories:\n\n* " + \
                     ("\n* ".join([c.name + ' (' + ", ".join(c.aliases) + ')' for c in categories]))
    await message.answer(answer_message)


@dp.message_handler(commands=['today'])
async def today_statistics(message: types.Message):
    """Sends today's spend statistics"""
    answer_message = expenses.get_today_statistics()
    await message.answer(answer_message)


@dp.message_handler(commands=['month'])
async def month_statistics(message: types.Message):
    """Sends spending statistics for the current month"""
    answer_message = expenses.get_month_statistics()
    await message.answer(answer_message)


@dp.message_handler(commands=['previous'])
async def previous_month_statistics(message: types.Message):
    """Sends spending statistics for the previous month"""
    answer_message = expenses.get_previous_month_statistics()
    await message.answer(answer_message)


@dp.message_handler(commands=['expenses'])
async def list_expenses(message: types.Message):
    """Sends the last few expense entries"""
    last_expenses = expenses.last()
    if not last_expenses:
        await message.answer("Expenses have not been added yet")
        return

    last_expenses_rows = [
        f"{expense.amount} hrn. on {expense.category_name} - press "
        f"/del{expense.id} to delete"
        for expense in last_expenses]
    answer_message = "Last saved expenses:\n\n* " + "\n\n* ".join(last_expenses_rows)
    await message.answer(answer_message)


@dp.message_handler()
async def add_expense(message: types.Message):
    """Adding new expense"""
    try:
        expense = expenses.add_expense(message.text)
    except exceptions.NotCorrectMessage as e:
        await message.answer(str(e))
        return
    answer_message = (
        f"Added expenses {expense.amount} hrn on {expense.category_name}.\n\n"
        f"{expenses.get_today_statistics()}")
    await message.answer(answer_message)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
