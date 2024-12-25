import logging
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Your Django API endpoint and credentials
API_URL = os.getenv("API_URL")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# Dictionary for status translation
STATUS_CHOICES = {
    # Add your status choices here
}

# Dictionary to track the last request time for each user
user_last_request_time = {}

# Minimum interval between requests (e.g., 5 seconds)
MIN_REQUEST_INTERVAL = timedelta(seconds=5)

async def check_rate_limit(user_id):
    now = datetime.now()
    if user_id in user_last_request_time:
        last_request_time = user_last_request_time[user_id]
        time_since_last_request = now - last_request_time
        if time_since_last_request < MIN_REQUEST_INTERVAL:
            remaining_time = MIN_REQUEST_INTERVAL - time_since_last_request
            return False, remaining_time
    user_last_request_time[user_id] = now
    return True, None

async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    allowed, remaining_time = await check_rate_limit(user_id)
    if not allowed:
        seconds_left = int(remaining_time.total_seconds())
        await update.message.reply_text(
            f"Слишком много запросов. Пожалуйста, подождите еще {seconds_left} секунд."
        )
        return

    # Создаем клавиатуру с кнопками
    keyboard = [
        ["Проверить статус заказа"],
        ["Помощь", "Контакты"],
        ["Пленка в наличии"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    # Отправляем сообщение с клавиатурой
    await update.message.reply_text(
        'Здравствуйте! Введите номер заказа и номер телефона через пробел.',
        reply_markup=reply_markup
    )

async def check_order_status(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    allowed, remaining_time = await check_rate_limit(user_id)
    if not allowed:
        seconds_left = int(remaining_time.total_seconds())
        await update.message.reply_text(
            f"Слишком много запросов. Пожалуйста, подождите еще {seconds_left} секунд."
        )
        return

    try:
        # Разделяем сообщение на номер заказа и номер телефона
        parts = update.message.text.split()
        if len(parts) != 2:
            await update.message.reply_text("Пожалуйста, введите номер заказа и номер телефона через пробел.")
            return

        order_number, phone_number = parts

        # Убираем '+' в начале номера телефона, если он есть
        if phone_number.startswith('+'):
            phone_number = phone_number[1:]

        # Формируем URL для API
        url = f"{API_URL}{order_number}/"

        # Выполняем запрос с базовой аутентификацией
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD))

        # Логируем ответ для отладки
        logger.info(f"API response: {response.status_code} {response.text}")

        if response.status_code == 200:
            order_data = response.json()
            if order_data['client']['phone_number'] == phone_number:
                # Получаем описание статуса из STATUS_CHOICES
                status_description = STATUS_CHOICES.get(order_data['status'], 'Неизвестный статус')

                # Форматируем сообщение ответа
                message = (
                    f"{status_description}\n"
                )
                await update.message.reply_text(message)
            else:
                await update.message.reply_text("Номер телефона не совпадает с номером телефона клиента в заказе.")
        else:
            await update.message.reply_text("Заказ не найден. Проверьте номер заказа и попробуйте снова.")
    except Exception as e:
        logger.error(f"Error checking order status: {e}")
        await update.message.reply_text("Произошла ошибка при проверке заказа. Пожалуйста, повторите попытку позже.")

async def available_products_command(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    allowed, remaining_time = await check_rate_limit(user_id)
    if not allowed:
        seconds_left = int(remaining_time.total_seconds())
        await update.message.reply_text(
            f"Слишком много запросов. Пожалуйста, подождите еще {seconds_left} секунд."
        )
        return

    try:
        # Получаем URL и учетные данные из переменных окружения
        products_url = os.getenv("PRODUCTS_API_URL")
        username = os.getenv("PRODUCTS_API_USERNAME")
        password = os.getenv("PRODUCTS_API_PASSWORD")

        # Выполняем запрос к API
        response = requests.get(products_url, auth=HTTPBasicAuth(username, password))

        if response.status_code == 200:
            products = response.json()
            message = "📦 *Доступные товары:*\n\n"
            for product in products:
                price = float(product['price'])
                discount = float(product['discount'])
                final_price = price - discount if discount > 0 else price

                # Определяем текст для количества
                quantity = product['quantity']
                if quantity < 2:
                    quantity_text = "Осталась пара штук"
                elif quantity < 10:
                    quantity_text = "Осталась последние 10"
                elif quantity < 20:
                    quantity_text = "Много"
                else:
                    quantity_text = "Целая гора"

                message += (
                    f"🔹 *Название:* {product['name']}\n"
                    f"💰 *Цена:* {final_price:.2f} {'(Скидка: ' + str(discount) + ')' if discount > 0 else ''}\n"
                    f"📊 *Количество:* {quantity_text}\n\n"
                )
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text("Не удалось получить список товаров. Попробуйте позже.")
    except Exception as e:
        logger.error(f"Error fetching available products: {e}")
        await update.message.reply_text("Произошла ошибка при получении списка товаров. Пожалуйста, повторите попытку позже.")

async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Это бот для проверки статуса заказа. Введите номер заказа и номер телефона через пробел.")

async def contact_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Контакты: support@example.com, Телефон: +123456789")

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    # Add handlers for button presses
    application.add_handler(MessageHandler(filters.Regex('^Пленка в наличии$'), available_products_command))
    application.add_handler(MessageHandler(filters.Regex('^Проверить статус заказа$'), check_order_status))
    application.add_handler(MessageHandler(filters.Regex('^Помощь$'), help_command))
    application.add_handler(MessageHandler(filters.Regex('^Контакты$'), contact_command))

    # on noncommand i.e message - check order status
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_order_status))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()