import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from requests.auth import HTTPBasicAuth

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Your Django API endpoint and credentials
API_URL = "http://127.0.0.1:8000/myapp/api/orders/number/"
USERNAME = "admin"  # Замените на ваш реальный логин
PASSWORD = "hp13199113"  # Замените на ваш реальный пароль

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
    'no_na_proyavku': 'Статус твоего заказа: не оплачен, в очереди на проявку.',
}

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Здравствуйте! Введите номер заказа и номер телефона через пробел.')

async def check_order_status(update: Update, context: CallbackContext) -> None:
    try:
        # Split the message into order number and phone number
        parts = update.message.text.split()
        if len(parts) != 2:
            await update.message.reply_text("Пожалуйста, введите номер заказа и номер телефона через пробел.")
            return

        order_number, phone_number = parts

        # Construct the API URL
        url = f"{API_URL}{order_number}/"

        # Make the request with Basic Authentication
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD))

        # Log the response for debugging
        logger.info(f"API response: {response.status_code} {response.text}")

        if response.status_code == 200:
            order_data = response.json()
            if order_data['client']['phone_number'] == phone_number:
                # Get status description from STATUS_CHOICES
                status_description = STATUS_CHOICES.get(order_data['status'], 'Неизвестный статус')

                # Format response message
                message = (
                    # f"Order Number: {order_data['order_number']}\n"
                    # f"Client Name: {order_data['client']['first_name']} {order_data['client']['last_name']}\n"
                    # f"Phone Number: {order_data['client']['phone_number']}\n"
                    # f"Email: {order_data['client']['email']}\n"
                    # f"Total Spent: {order_data['client']['total_spent']}\n"
                    # f"Student ID: {order_data['client']['student_id']}\n"
                    # f"Student ID Expiry Date: {order_data['client']['student_id_expiry_date']}\n"
                    # f"Created At: {order_data['created_at']}\n"
                    f"{status_description}\n"
                    # f"Processed By: {order_data['processed_by']}\n"
                    # f"Scanned By: {order_data['scanned_by']}\n"
                    # f"Shipped By: {order_data['shipped_by']}\n"
                    # f"Printed By: {order_data['printed_by']}"
                )
                await update.message.reply_text(message)
            else:
                await update.message.reply_text("Номер телефона не совпадает с номером телефона клиента в заказе.")
        else:
            await update.message.reply_text("Заказ не найден. Проверьте номер заказа и попробуйте снова.")
    except Exception as e:
        logger.error(f"Error checking order status: {e}")
        await update.message.reply_text("Произошла ошибка при проверке заказа. Пожалуйста, повторите попытку позже.")

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("6712054238:AAHM5RJtgmCF29hTDTL_HYPomJezbALO9_8").build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    # on noncommand i.e message - check order status
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_order_status))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
