from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton
import requests
from cachetools import TTLCache


api_id = 20003235
api_hash = "1b5375e7b6754e4a96c0055774fc4356"
bot_token = "6665304809:AAErb8QUvHkcFY4tB3G7LC0KVSpkl13UCpA"

cache = TTLCache(maxsize=1, ttl=300)



app = Client(
    "my_bot",
    api_id=api_id, api_hash=api_hash,
    bot_token=bot_token
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
        url = "http://212.86.115.174/api/available-products/"
        try:
            response = requests.get(url, auth=('call_helper', 'Hp13199113'))
            response.raise_for_status()
            products = response.json()
            product_list = "📦 **Доступные товары:**\n\n"
            for product in products:
                product_list += f"🔹 **Название:** {product['name']}\n💰 Цена: {product['price']}\n📊 Количество: {product['quantity']}\n\n"
            cache["products"] = product_list
        except requests.exceptions.RequestException:
            message.reply_text("Ошибка при получении данных, попробуйте позже")
            return

    message.reply_text(product_list)

if __name__ == "__main__":
    app.run()