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

# Emojis for better visual representation
EMOJIS = {
    'welcome': '👋',
    'income': '💰',
    'expense': '💸',
    'report': '📊',
    'edit': '✏️',
    'success': '✅',
    'error': '❌',
    'warning': '⚠️',
    'back': '🔙',
    'calendar': '📅',
    'money': '💵',
    'description': '📝'
}

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
        [KeyboardButton(f"{EMOJIS['income']} ثبت درآمد")],
        [KeyboardButton(f"{EMOJIS['expense']} ثبت هزینه")],
        [KeyboardButton(f"{EMOJIS['report']} گزارش تراکنش‌ها")],
        [KeyboardButton(f"{EMOJIS['edit']} ویرایش تراکنش")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def format_amount(amount):
    """Format amount with thousand separators."""
    return f"{amount:,.0f}"

def format_date(date_str):
    """Format date to Persian style."""
    date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    return date.strftime('%Y/%m/%d %H:%M')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message with the main menu when the command /start is issued."""
    welcome_message = f"""
{EMOJIS['welcome']} به ربات حسابداری شخصی خوش آمدید!

با استفاده از این ربات می‌توانید:
• درآمدها و هزینه‌های خود را ثبت کنید
• گزارش تراکنش‌ها را مشاهده کنید
• تراکنش‌های قبلی را ویرایش کنید

لطفاً یکی از گزینه‌های زیر را انتخاب کنید:
"""
    await update.message.reply_text(
        welcome_message,
        reply_markup=get_main_menu_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages."""
    text = update.message.text

    if text == f"{EMOJIS['income']} ثبت درآمد":
        context.user_data['waiting_for'] = 'income_amount'
        await update.message.reply_text(
            f"{EMOJIS['money']} لطفاً مبلغ درآمد را وارد کنید:\n"
            f"{EMOJIS['warning']} فقط عدد وارد کنید (مثال: 1000000)"
        )
    
    elif text == f"{EMOJIS['expense']} ثبت هزینه":
        context.user_data['waiting_for'] = 'expense_amount'
        await update.message.reply_text(
            f"{EMOJIS['money']} لطفاً مبلغ هزینه را وارد کنید:\n"
            f"{EMOJIS['warning']} فقط عدد وارد کنید (مثال: 1000000)"
        )
    
    elif text == f"{EMOJIS['report']} گزارش تراکنش‌ها":
        await show_report(update, context)
    
    elif text == f"{EMOJIS['edit']} ویرایش تراکنش":
        await show_edit_menu(update, context)
    
    elif 'waiting_for' in context.user_data:
        if 'amount' not in context.user_data:
            try:
                amount = float(text.replace(',', ''))
                if amount <= 0:
                    await update.message.reply_text(
                        f"{EMOJIS['error']} لطفاً یک مبلغ مثبت وارد کنید."
                    )
                    return

                transaction_type = 'income' if context.user_data['waiting_for'] == 'income_amount' else 'expense'
                
                # Store the amount and ask for description
                context.user_data['amount'] = amount
                context.user_data['waiting_for'] = f'{transaction_type}_description'
                
                await update.message.reply_text(
                    f"{EMOJIS['description']} لطفاً توضیحات این تراکنش را وارد کنید:\n"
                    f"{EMOJIS['warning']} توضیحات باید کوتاه و مختصر باشد"
                )
            
            except ValueError:
                await update.message.reply_text(
                    f"{EMOJIS['error']} لطفاً یک عدد معتبر وارد کنید."
                )
        
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

            type_emoji = EMOJIS['income'] if transaction_type == 'income' else EMOJIS['expense']
            type_text = "درآمد" if transaction_type == 'income' else "هزینه"
            
            success_message = f"""
{EMOJIS['success']} تراکنش با موفقیت ثبت شد!

{type_emoji} نوع: {type_text}
{EMOJIS['money']} مبلغ: {format_amount(amount)} ریال
{EMOJIS['description']} توضیحات: {description}
{EMOJIS['calendar']} تاریخ: {format_date(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}
"""
            await update.message.reply_text(
                success_message,
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
            f"{EMOJIS['warning']} هیچ تراکنشی یافت نشد.",
            reply_markup=get_main_menu_keyboard()
        )
        return

    # Calculate total income and expense
    total_income = sum(t[1] for t in transactions if t[0] == 'income')
    total_expense = sum(t[1] for t in transactions if t[0] == 'expense')
    balance = total_income - total_expense

    report = f"""
{EMOJIS['report']} گزارش ۱۰ تراکنش آخر:

{EMOJIS['money']} جمع درآمد: {format_amount(total_income)} ریال
{EMOJIS['money']} جمع هزینه: {format_amount(total_expense)} ریال
{EMOJIS['money']} موجودی: {format_amount(balance)} ریال

📋 جزئیات تراکنش‌ها:
"""
    for t in transactions:
        type_emoji = EMOJIS['income'] if t[0] == 'income' else EMOJIS['expense']
        type_text = "درآمد" if t[0] == 'income' else "هزینه"
        report += f"\n{type_emoji} {type_text}: {format_amount(t[1])} ریال"
        report += f"\n{EMOJIS['description']} توضیحات: {t[2]}"
        report += f"\n{EMOJIS['calendar']} تاریخ: {format_date(t[3])}\n"

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
            f"{EMOJIS['warning']} هیچ تراکنشی برای ویرایش وجود ندارد.",
            reply_markup=get_main_menu_keyboard()
        )
        return

    report = f"""
{EMOJIS['edit']} انتخاب تراکنش برای ویرایش:

"""
    for t in transactions:
        type_emoji = EMOJIS['income'] if t[1] == 'income' else EMOJIS['expense']
        type_text = "درآمد" if t[1] == 'income' else "هزینه"
        report += f"\n{t[0]}. {type_emoji} {type_text}: {format_amount(t[2])} ریال"
        report += f"\n   {EMOJIS['description']} توضیحات: {t[3]}"
        report += f"\n   {EMOJIS['calendar']} تاریخ: {format_date(t[4])}\n"

    report += f"\n{EMOJIS['warning']} برای ویرایش، شماره تراکنش را وارد کنید."

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