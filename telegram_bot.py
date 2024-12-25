import logging
import requests
import httpx
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

# Constants
TIMEOUT = 30.0
REQUEST_TIMEOUT = httpx.Timeout(TIMEOUT)

# Your Django API endpoint and credentials
API_URL = os.getenv("API_URL")
USERNAME = os.getenv("PRODUCTS_API_USERNAME")
PASSWORD = os.getenv("PRODUCTS_API_PASSWORD")

# Dictionary for status translation
STATUS_CHOICES = {
    'opl_na_proyavku': 'Статус твоего заказа: оплачен, в очереди на проявку! 🎞',
    'opl_na_skan': 'Статус твоего заказа: оплачен, в очереди на сканирование! 🎞',
    'opl_na_otpravku': 'Статус твоего заказа: оплачен, скоро будет отправлен на почту!',
    'opl_na_pechat': 'Статус твоего заказа: оплачен, в очереди на печать! 🌠',
    'opl_gotov': 'Статус твоего заказа: оплачен и готов 💫 Можно забирать!',
    'opl_gotov_otpr': 'Статус твоего заказа: оплачен, готов и отправлен на e-mail 📩',
    'opl_gotov_otpr_otdan': 'Статус твоего заказа: оплачен, готов, отправлен на e-mail и отдан тебе 🙂',
    'opl_gotov_otdan': 'Статус твоего заказа: оплачен, готов и отдан тебе 🙂',
    'no_gotov': 'Статус твоего заказа: не оплачен, готов',
    'srchno_opl_na_proyavku': 'Статус твоего заказа: ⚡️срочный заказ⚡️, оплачен, в очереди на проявку!',
    'srchno_opl_na_skan': 'Статус твоего заказа:⚡️срочный заказ⚡️, оплачен, в очереди на сканирование!',
}

# Dictionary to track the last request time for each user
user_last_request_time = {}

# Minimum interval between requests
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
    if not update.message:
        logger.error("Received update without message")
        return

    user_id = update.message.from_user.id
    allowed, remaining_time = await check_rate_limit(user_id)
    if not allowed:
        seconds_left = int(remaining_time.total_seconds())
        await update.message.reply_text(
            f"Слишком много запросов. Пожалуйста, подождите еще {seconds_left} секунд."
        )
        return

    keyboard = [
        ["Проверить статус заказа"],
        ["Помощь", "Контакты"],
        ["Пленка в наличии"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        'Здравствуйте! Введите номер заказа и номер телефона через пробел.',
        reply_markup=reply_markup
    )


async def check_order_status(update: Update, context: CallbackContext) -> None:
    if not update.message:
        logger.error("Received update without message")
        return

    user_id = update.message.from_user.id
    allowed, remaining_time = await check_rate_limit(user_id)
    if not allowed:
        seconds_left = int(remaining_time.total_seconds())
        await update.message.reply_text(
            f"Слишком много запросов. Пожалуйста, подождите еще {seconds_left} секунд."
        )
        return

    try:
        parts = update.message.text.split()
        if len(parts) != 2:
            await update.message.reply_text("Пожалуйста, введите номер заказа и номер телефона через пробел.")
            return

        order_number, phone_number = parts
        if phone_number.startswith('+'):
            phone_number = phone_number[1:]

        url = f"{API_URL}{order_number}/"
        logger.info(f"Trying to connect to API: {url}")

        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD), timeout=TIMEOUT)
        logger.info(f"API response: {response.status_code} {response.text}")

        if response.status_code == 200:
            order_data = response.json()
            if order_data['client']['phone_number'] == phone_number:
                status_description = STATUS_CHOICES.get(order_data['status'], 'Неизвестный статус')
                message = f"{status_description}\n"
                await update.message.reply_text(message)
            else:
                await update.message.reply_text("Номер телефона не совпадает с номером телефона клиента в заказе.")
        else:
            await update.message.reply_text("Заказ не найден. Проверьте номер заказа и попробуйте снова.")
    except requests.Timeout:
        logger.error("Request timed out")
        await update.message.reply_text("Превышено время ожидания ответа. Пожалуйста, повторите попытку позже.")
    except Exception as e:
        logger.error(f"Error checking order status: {e}")
        await update.message.reply_text("Произошла ошибка при проверке заказа. Пожалуйста, повторите попытку позже.")


async def available_products_command(update: Update, context: CallbackContext) -> None:
    if not update.message:
        logger.error("Received update without message")
        return

    user_id = update.message.from_user.id
    allowed, remaining_time = await check_rate_limit(user_id)
    if not allowed:
        seconds_left = int(remaining_time.total_seconds())
        await update.message.reply_text(
            f"Слишком много запросов. Пожалуйста, подождите еще {seconds_left} секунд."
        )
        return

    try:
        products_url = os.getenv("PRODUCTS_API_URL")
        username = os.getenv("PRODUCTS_API_USERNAME")
        password = os.getenv("PRODUCTS_API_PASSWORD")

        logger.info(f"Trying to connect to API: {products_url}")
        response = requests.get(products_url, auth=HTTPBasicAuth(username, password), timeout=TIMEOUT)

        if response.status_code == 200:
            products = response.json()
            messages = ["📦 *Доступные товары:*\n\n"]
            current_message = messages[0]

            for product in products:
                price = float(product['price'])
                discount = float(product['discount'])
                final_price = price - discount if discount > 0 else price

                quantity = product['quantity']
                if quantity < 2:
                    quantity_text = "Осталась пара штук"
                elif quantity < 10:
                    quantity_text = "Осталась последние 10"
                elif quantity < 20:
                    quantity_text = "Много"
                else:
                    quantity_text = "Целая гора"

                product_text = (
                    f"🔹 *Название:* {product['name']}\n"
                    f"💰 *Цена:* {final_price:.2f} {'(Скидка: ' + str(discount) + ')' if discount > 0 else ''}\n"
                    f"📊 *Количество:* {quantity_text}\n\n"
                )

                # Проверяем, не превысит ли добавление нового товара лимит
                if len(current_message + product_text) > 4000:  # Оставляем небольшой запас
                    messages.append(product_text)
                    current_message = product_text
                else:
                    current_message += product_text
                    messages[-1] = current_message

            # Отправляем все сообщения
            for message in messages:
                await update.message.reply_text(message, parse_mode='Markdown')

        else:
            await update.message.reply_text("Не удалось получить список товаров. Попробуйте позже.")
    except requests.Timeout:
        logger.error("Request timed out")
        await update.message.reply_text("Превышено время ожидания ответа. Пожалуйста, повторите попытку позже.")
    except Exception as e:
        logger.error(f"Error fetching available products: {e}")
        await update.message.reply_text(
            "Произошла ошибка при получении списка товаров. Пожалуйста, повторите попытку позже.")

async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Это бот для проверки статуса заказа. Введите номер заказа и номер телефона через пробел.")


async def contact_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Контакты: support@example.com, Телефон: +123456789")


def main() -> None:
    application = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex('^Пленка в наличии$'), available_products_command))
    application.add_handler(MessageHandler(filters.Regex('^Проверить статус заказа$'), check_order_status))
    application.add_handler(MessageHandler(filters.Regex('^Помощь$'), help_command))
    application.add_handler(MessageHandler(filters.Regex('^Контакты$'), contact_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_order_status))

    application.run_polling()


if __name__ == '__main__':
    main()