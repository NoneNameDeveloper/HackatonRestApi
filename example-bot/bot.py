import os
import re
import json
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup


import logging
from urllib.parse import quote
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters, CallbackContext

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

base_url = os.environ["TADA_API_BASE_URL"]
company_token = os.environ["TADA_API_COMPANY_TOKEN"]
token = os.environ['TELEGRAM_TOKEN']

async def bot_command(update, context):
    
    message = update.message
    text = message.text
    chat_id = message.chat_id

    sender_id = update.message.from_user.id
    
    response = requests.get(base_url + "/text_prompt?user_id=" + str(sender_id) + "&token=" + company_token + "&text=" + quote(text)).json()
    print(response)
    answer = None
    if response['status'] != "SUCCESS":
        answer = "Ошибка: " + response['STATUS']
    else:
        answer = response['result']

    # buttons = [
    #     [
    #         InlineKeyboardButton("Хороший ответ", callback_data="good"),
    #         InlineKeyboardButton("Плохой ответ", callback_data="bad"),
    #         InlineKeyboardButton("Ответить по-другому", callback_data="again")
    #     ]
    # ]

    # buttons = [[InlineKeyboardButton(variant, callback_data="again")] for variant in response['variants']]


    buttons = [[variant] for variant in response['variants']]
    reply_markup = ReplyKeyboardMarkup(buttons)

    n = 4000
    [await context.bot.send_message(chat_id=chat_id, text=s, reply_markup=reply_markup) for s in [answer[i:i+n] for i in range(0, len(answer), n)]]
    
    # await context.bot.edit_message_text(chat_id=chat_id, text=answer, reply_markup=reply_markup, message_id=response_message.message_id)




async def restart_command(update, context):
    sender_id = update.message.from_user.id
    response = requests.get(base_url + "/reset_state?user_id=" + str(sender_id) + "&token=" + company_token).json()
    print(response)

    reply_markup = ReplyKeyboardMarkup([['/reset']], resize_keyboard=True)
    await context.bot.send_message(chat_id=update.message.chat_id, text=str(response), reply_markup=reply_markup)

def main():
    app = ApplicationBuilder().token(token).build()
    app.add_handler(MessageHandler(~filters.COMMAND, bot_command))
    app.add_handler(CommandHandler("start", restart_command))
    app.add_handler(CommandHandler("restart", restart_command))
    app.add_handler(CommandHandler("reset", restart_command))
    app.run_polling()

if __name__ == '__main__':
    main()