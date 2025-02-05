from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton


from cachetools import TTLCache

import os
from dotenv import load_dotenv


import requests
import httpx
from requests.auth import HTTPBasicAuth


load_dotenv()


API_ID = os.getenv("api_id")
API_HASH = os.getenv("api_hash")
BOT_TOKEN = os.getenv("bot_token")
API_URL = os.getenv("API_URL")
USERNAME = os.getenv("PRODUCTS_API_USERNAME")
PASSWORD = os.getenv("PRODUCTS_API_PASSWORD")

cache = TTLCache(maxsize=1, ttl=300)

TIMEOUT = 30.0
REQUEST_TIMEOUT = httpx.Timeout(TIMEOUT)


app = Client(
    "my_bot",
    api_id=API_ID, api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("start") & filters.private)
def start(client, message):
    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("Узнать статус заказа"), KeyboardButton("Нужна помощь")],
            [KeyboardButton("Наши соц сети"), KeyboardButton("Пленка в наличии")]
        ],
        resize_keyboard=True
    )
    message.reply_text("Добро пожаловать! Выберите опцию:", reply_markup=keyboard)

@app.on_message(filters.text & filters.private & filters.regex("^Узнать статус заказа$"))
def status_order(client, message):
    message.reply_text("Узнайте статус заказа")

@app.on_message(filters.text & filters.private & filters.regex("^Нужна помощь$"))
def help_request(client, message):
    message.reply_text("Наш менеджер поможет вам с заказом.")

@app.on_message(filters.text & filters.private & filters.regex("^Наши соц сети$"))
def social_media(client, message):
    message.reply_text("Ссылка на наши соцсети")

@app.on_message(filters.text & filters.private & filters.regex("^Пленка в наличии$"))
def available_products(client, message):
    if "products" in cache:
        product_list = cache["products"]
        print("Подняли с кэша")
    else:
        try:
            url = API_URL
            response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD), timeout=TIMEOUT)
            response.raise_for_status()
            products = response.json()
            product_list = "📦 **Доступные товары:**\n\n"
            for product in products:
                product_list += f"🔹 **Название:** {product['name']}\n💰 Цена: {product['price']}\n📊 Количество: {product['quantity']}\n\n"
            cache["products"] = product_list
        except requests.exceptions.RequestException as e:
            message.reply_text(f"Ошибка при получении данных, попробуйте позже {e}")
            return

    message.reply_text(product_list)

if __name__ == "__main__":
    app.run()