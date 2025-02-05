from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton
import requests

api_id = 20003235
api_hash = "1b5375e7b6754e4a96c0055774fc4356"
bot_token = "6665304809:AAErb8QUvHkcFY4tB3G7LC0KVSpkl13UCpA"

app = Client(
    "my_bot",
    api_id=api_id, api_hash=api_hash,
    bot_token=bot_token
)

@app.on_message(filters.command("start") & filters.private)
def start(client, message):
    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("Кнопка 1"), KeyboardButton("Кнопка 2")],
            [KeyboardButton("Кнопка 3"), KeyboardButton("Пленка в наличии")]
        ],
        resize_keyboard=True
    )
    message.reply_text("Добро пожаловать! Выберите опцию:", reply_markup=keyboard)

@app.on_message(filters.text & filters.private)
def available_products(client, message):
    if message.text == "Пленка в наличии":
        url = "http://212.86.115.174/api/available-products/"
        try:
            response = requests.get(url, auth=('call_helper', 'Hp13199113'))
            response.raise_for_status()
            products = response.json()
            product_list = "📦 **Доступные товары:**\n\n"
            for product in products:
                product_list += f"🔹 **Название:** {product['name']}\n💰 Цена: {product['price']}\n📊 Количество: {product['quantity']}\n\n"
            message.reply_text(product_list)
        except requests.exceptions.RequestException as e:
            message.reply_text(f"Ошибка при получении данных: {e}")
    else:
        message.reply_text("Выберите опцию с клавиатуры.")

if __name__ == "__main__":
    app.run()