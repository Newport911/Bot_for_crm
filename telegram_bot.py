from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton
from cachetools import TTLCache
import os
from dotenv import load_dotenv
import httpx
from requests.auth import HTTPBasicAuth

import httpx
from requests.auth import HTTPBasicAuth

load_dotenv()

API_ID = os.getenv("api_id")
API_HASH = os.getenv("api_hash")
BOT_TOKEN = os.getenv("bot_token")
API_URL = os.getenv("API_URL")
USERNAME = os.getenv("PRODUCTS_API_USERNAME")
PASSWORD = os.getenv("PRODUCTS_API_PASSWORD")
API_URL_FOR_ORDER = os.getenv("API_URL_FOR_ORDER")

cache = TTLCache(maxsize=1, ttl=300)

TIMEOUT = 30.0
REQUEST_TIMEOUT = httpx.Timeout(TIMEOUT)

app = Client(
    "my_bot",
    api_id=API_ID, api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("Узнать статус заказа"), KeyboardButton("Нужна помощь")],
            [KeyboardButton("Наши соц сети"), KeyboardButton("Пленка в наличии")]
        ],
        resize_keyboard=True
    )
    await message.reply_text("Добро пожаловать! Выберите опцию:", reply_markup=keyboard)


user_data = {}


@app.on_message(filters.text & filters.private & filters.regex("^Узнать статус заказа$"))
async def status_order(client, message):
    await message.reply_text("Пожалуйста, введите номер телефона:")
    user_data[message.from_user.id] = {}

@app.on_message(filters.text & filters.private)
async def get_phone_number(client, message):
    if message.from_user.id in user_data and "phone_number" not in user_data[message.from_user.id]:
        user_data[message.from_user.id]["phone_number"] = message.text.strip()
        await message.reply_text("Теперь введите номер заказа:")
    elif message.from_user.id in user_data and "phone_number" in user_data[message.from_user.id]:
        order_number = message.text.strip()
        phone_number = user_data[message.from_user.id]["phone_number"]
        await check_order_status(client, message, phone_number, order_number)
        del user_data[message.from_user.id]

async def check_order_status(client, message, phone_number, order_number):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL_FOR_ORDER}{order_number}/", auth=HTTPBasicAuth(USERNAME, PASSWORD), timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            order_data = response.json()
            if order_data["client"]["phone_number"] == phone_number:
                await message.reply_text(f"Статус вашего заказа: {order_data['status']}")
            else:
                await message.reply_text("Ошибка: введенный номер телефона не соответствует номеру в заказе.")
    except httpx.RequestError as e:
        await message.reply_text(f"Ошибка при получении данных, попробуйте позже {e}")




@app.on_message(filters.text & filters.private & filters.regex("^Нужна помощь$"))
async def help_request(client, message):
    manager_username = "phsquat_chat"  # Замените на имя пользователя менеджера
    await message.reply_text(f"Вы можете связаться с нашим менеджером по этой ссылке: https://t.me/{manager_username}")

@app.on_message(filters.text & filters.private & filters.regex("^Наши соц сети$"))
async def social_media(client, message):
    await message.reply_text("Ссылка на наши соцсети")

@app.on_message(filters.text & filters.private & filters.regex("^Пленка в наличии$"))
async def available_products(client, message):
    if "products" in cache:
        product_list = cache["products"]
        print("Подняли с кэша")
    else:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(API_URL, auth=HTTPBasicAuth(USERNAME, PASSWORD), timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                products = response.json()
                product_list = "📦 **Доступные товары:**\n\n"
                for product in products:
                    quantity = product['quantity']
                    if quantity < 2:
                        quantity_text = "Осталась пара штук"
                    elif quantity < 10:
                        quantity_text = "Осталась последние 10"
                    elif quantity < 20:
                        quantity_text = "Много"
                    else:
                        quantity_text = "Целая гора"
                    product_list += f"🔹 **Название:** {product['name']}\n💰 Цена: {product['price']}\n📊 Количество: {quantity_text}\n\n"
                cache["products"] = product_list
        except httpx.RequestError as e:
            await message.reply_text(f"Ошибка при получении данных, попробуйте позже {e}")
            return

    await message.reply_text(product_list)

if __name__ == "__main__":
    app.run()