import os
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv
import sqlite3

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database initialization
def init_db():
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  type TEXT NOT NULL,
                  amount REAL NOT NULL,
                  description TEXT,
                  date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# Main menu keyboard
def get_main_menu_keyboard():
    keyboard = [
        [KeyboardButton("ثبت درآمد")],
        [KeyboardButton("ثبت هزینه")],
        [KeyboardButton("گزارش تراکنش‌ها")],
        [KeyboardButton("ویرایش تراکنش")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message with the main menu when the command /start is issued."""
    await update.message.reply_text(
        'به ربات حسابداری خوش آمدید! لطفاً یک گزینه را انتخاب کنید:',
        reply_markup=get_main_menu_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages."""
    text = update.message.text

    if text == "ثبت درآمد":
        context.user_data['waiting_for'] = 'income_amount'
        await update.message.reply_text('لطفاً مبلغ درآمد را وارد کنید:')
    
    elif text == "ثبت هزینه":
        context.user_data['waiting_for'] = 'expense_amount'
        await update.message.reply_text('لطفاً مبلغ هزینه را وارد کنید:')
    
    elif text == "گزارش تراکنش‌ها":
        await show_report(update, context)
    
    elif text == "ویرایش تراکنش":
        await show_edit_menu(update, context)
    
    elif 'waiting_for' in context.user_data:
        if 'amount' not in context.user_data:
            try:
                amount = float(text)
                if amount <= 0:
                    await update.message.reply_text('لطفاً یک مبلغ مثبت وارد کنید.')
                    return

                transaction_type = 'income' if context.user_data['waiting_for'] == 'income_amount' else 'expense'
                
                # Store the amount and ask for description
                context.user_data['amount'] = amount
                context.user_data['waiting_for'] = f'{transaction_type}_description'
                
                await update.message.reply_text('لطفاً توضیحات این تراکنش را وارد کنید:')
            
            except ValueError:
                await update.message.reply_text('لطفاً یک عدد معتبر وارد کنید.')
        
        else:
            description = text
            amount = context.user_data['amount']
            transaction_type = 'income' if 'income' in context.user_data['waiting_for'] else 'expense'

            # Save to database
            conn = sqlite3.connect('accounting.db')
            c = conn.cursor()
            c.execute('INSERT INTO transactions (type, amount, description) VALUES (?, ?, ?)',
                      (transaction_type, amount, description))
            conn.commit()
            conn.close()

            # Clear user data
            context.user_data.clear()

            await update.message.reply_text(
                f'تراکنش {transaction_type} به مبلغ {amount} با موفقیت ثبت شد!',
                reply_markup=get_main_menu_keyboard()
            )

async def show_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show transaction report."""
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute('SELECT type, amount, description, date FROM transactions ORDER BY date DESC LIMIT 10')
    transactions = c.fetchall()
    conn.close()

    if not transactions:
        await update.message.reply_text(
            'هیچ تراکنشی یافت نشد.',
            reply_markup=get_main_menu_keyboard()
        )
        return

    report = "۱۰ تراکنش آخر:\n\n"
    for t in transactions:
        type_text = "درآمد" if t[0] == "income" else "هزینه"
        report += f"{type_text}: {t[1]} - {t[2]} ({t[3]})\n"

    await update.message.reply_text(
        report,
        reply_markup=get_main_menu_keyboard()
    )

async def show_edit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show edit menu with recent transactions."""
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute('SELECT id, type, amount, description, date FROM transactions ORDER BY date DESC LIMIT 5')
    transactions = c.fetchall()
    conn.close()

    if not transactions:
        await update.message.reply_text(
            'هیچ تراکنشی برای ویرایش وجود ندارد.',
            reply_markup=get_main_menu_keyboard()
        )
        return

    report = "انتخاب تراکنش برای ویرایش:\n\n"
    for t in transactions:
        type_text = "درآمد" if t[1] == "income" else "هزینه"
        report += f"{t[0]}. {type_text}: {t[2]} - {t[3]}\n"

    await update.message.reply_text(
        report,
        reply_markup=get_main_menu_keyboard()
    )

def main():
    """Start the bot."""
    # Initialize database
    init_db()

    # Create the Application
    application = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 