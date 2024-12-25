import logging
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import os

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

async def start(update: Update, context: CallbackContext) -> None:
    # Создаем клавиатуру с кнопками
    keyboard = [
        ["Проверить статус заказа"],
        ["Помощь", "Контакты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    # Отправляем сообщение с клавиатурой
    await update.message.reply_text(
        'Здравствуйте! Введите номер заказа и номер телефона через пробел.',
        reply_markup=reply_markup
    )

async def check_order_status(update: Update, context: CallbackContext) -> None:
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

async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Это бот для проверки статуса заказа. Введите номер заказа и номер телефона через пробел.")

async def contact_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Контакты: support@example.com, Телефон: +123456789")

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    # on noncommand i.e message - check order status
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_order_status))

    # Add handlers for button presses
    application.add_handler(MessageHandler(filters.Regex('^Проверить статус заказа$'), check_order_status))
    application.add_handler(MessageHandler(filters.Regex('^Помощь$'), help_command))
    application.add_handler(MessageHandler(filters.Regex('^Контакты$'), contact_command))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()