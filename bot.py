import os
import logging
import random
import string
from datetime import datetime
import jdatetime
import pytz
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv
import sqlite3
from contextlib import contextmanager
import functools

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
    'description': '📝',
    'skip': '⏭️'
}

# Database initialization
def init_db():
    # Remove existing database to recreate with new schema
    if os.path.exists('accounting.db'):
        os.remove('accounting.db')
        
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  transaction_id TEXT UNIQUE NOT NULL,
                  type TEXT NOT NULL,
                  amount REAL NOT NULL,
                  description TEXT,
                  date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def get_tehran_time():
    """Get current time in Tehran timezone."""
    tehran_tz = pytz.timezone('Asia/Tehran')
    return datetime.now(tehran_tz)

@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect('accounting.db')
    try:
        yield conn
    finally:
        conn.close()

def format_amount(amount):
    """Format amount with thousand separators."""
    return f"{amount:,.0f}"

def format_date(date_str):
    """Format date to Persian style."""
    try:
        date = datetime.strptime(date_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
        persian_date = jdatetime.datetime.fromgregorian(datetime=date)
        return persian_date.strftime('%Y/%m/%d %H:%M')
    except Exception as e:
        logger.error(f"Error formatting date: {e}")
        return date_str

@functools.lru_cache(maxsize=128)
def get_persian_date():
    """Get current date in Persian calendar with caching."""
    tehran_time = get_tehran_time()
    return jdatetime.datetime.fromgregorian(datetime=tehran_time)

def generate_transaction_id():
    """Generate a unique transaction ID with format: letter + 3 digits."""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT transaction_id FROM transactions ORDER BY id DESC LIMIT 1')
            last_id = c.fetchone()
            
            if last_id:
                last_number = int(last_id[0][1:])
                new_number = last_number + 1
            else:
                new_number = 1
            
            letter = random.choice(string.ascii_lowercase)
            return f"{letter}{new_number:03d}"
    except sqlite3.OperationalError:
        init_db()
        return f"{random.choice(string.ascii_lowercase)}001"
    except Exception as e:
        logger.error(f"Error generating transaction ID: {e}")
        return f"{random.choice(string.ascii_lowercase)}{random.randint(1, 999):03d}"

def get_description_keyboard():
    """Get keyboard with skip button for description."""
    keyboard = [
        [KeyboardButton(f"{EMOJIS['skip']} رد کردن توضیحات"), KeyboardButton(f"{EMOJIS['back']} بازگشت به منو")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Main menu keyboard
def get_main_menu_keyboard():
    """Get main menu keyboard with aligned buttons."""
    keyboard = [
        [KeyboardButton(f"{EMOJIS['income']} ثبت درآمد"), KeyboardButton(f"{EMOJIS['expense']} ثبت هزینه")],
        [KeyboardButton(f"{EMOJIS['report']} گزارش تراکنش‌ها"), KeyboardButton(f"{EMOJIS['edit']} ویرایش تراکنش")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_report_keyboard():
    """Get report filtering keyboard."""
    keyboard = [
        [KeyboardButton("📅 امروز"), KeyboardButton("📅 هفته جاری")],
        [KeyboardButton("📅 ماه جاری"), KeyboardButton("📅 همه تراکنش‌ها")],
        [KeyboardButton(f"{EMOJIS['back']} بازگشت به منو")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

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
        await update.message.reply_text(
            "لطفاً بازه زمانی گزارش را انتخاب کنید:",
            reply_markup=get_report_keyboard()
        )
        context.user_data['waiting_for'] = 'report_period'
    
    elif text == f"{EMOJIS['edit']} ویرایش تراکنش":
        await show_edit_menu(update, context)
    
    elif text == f"{EMOJIS['skip']} رد کردن توضیحات":
        if 'amount' in context.user_data:
            amount = context.user_data['amount']
            transaction_type = 'income' if 'income' in context.user_data['waiting_for'] else 'expense'
            
            # Generate transaction ID
            transaction_id = generate_transaction_id()
            
            # Get current Tehran time
            tehran_time = get_tehran_time()
            
            # Save to database
            conn = sqlite3.connect('accounting.db')
            c = conn.cursor()
            c.execute('INSERT INTO transactions (transaction_id, type, amount, description, date) VALUES (?, ?, ?, ?, ?)',
                      (transaction_id, transaction_type, amount, None, tehran_time))
            conn.commit()
            conn.close()

            # Clear user data
            context.user_data.clear()

            type_emoji = EMOJIS['income'] if transaction_type == 'income' else EMOJIS['expense']
            type_text = "درآمد" if transaction_type == 'income' else "هزینه"
            
            # Get Persian date
            persian_date = get_persian_date()
            
            success_message = f"""
{EMOJIS['success']} تراکنش با موفقیت ثبت شد!

{type_emoji} نوع: {type_text}
{EMOJIS['money']} مبلغ: {format_amount(amount)} ریال
📝 شناسه تراکنش: {transaction_id}
{EMOJIS['calendar']} تاریخ: {persian_date.strftime('%Y/%m/%d %H:%M')}
"""
            await update.message.reply_text(
                success_message,
                reply_markup=get_main_menu_keyboard()
            )
    
    elif text == f"{EMOJIS['back']} بازگشت به منو":
        context.user_data.clear()
        await update.message.reply_text(
            "به منوی اصلی بازگشتید.",
            reply_markup=get_main_menu_keyboard()
        )
    
    elif 'waiting_for' in context.user_data:
        if context.user_data['waiting_for'] in ['edit_transaction_id', 'edit_action', 'edit_amount', 'edit_description']:
            await handle_edit_transaction(update, context)
        elif context.user_data['waiting_for'] == 'report_period':
            await show_filtered_report(update, context, text)
        elif 'amount' not in context.user_data:
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
                    f"{EMOJIS['warning']} توضیحات باید کوتاه و مختصر باشد",
                    reply_markup=get_description_keyboard()
                )
            
            except ValueError:
                await update.message.reply_text(
                    f"{EMOJIS['error']} لطفاً یک عدد معتبر وارد کنید."
                )
        
        else:
            description = text
            amount = context.user_data['amount']
            transaction_type = 'income' if 'income' in context.user_data['waiting_for'] else 'expense'

            # Generate transaction ID
            transaction_id = generate_transaction_id()
            
            # Get current Tehran time
            tehran_time = get_tehran_time()

            # Save to database
            conn = sqlite3.connect('accounting.db')
            c = conn.cursor()
            c.execute('INSERT INTO transactions (transaction_id, type, amount, description, date) VALUES (?, ?, ?, ?, ?)',
                      (transaction_id, transaction_type, amount, description, tehran_time))
            conn.commit()
            conn.close()

            # Clear user data
            context.user_data.clear()

            type_emoji = EMOJIS['income'] if transaction_type == 'income' else EMOJIS['expense']
            type_text = "درآمد" if transaction_type == 'income' else "هزینه"
            
            # Get Persian date
            persian_date = get_persian_date()
            
            success_message = f"""
{EMOJIS['success']} تراکنش با موفقیت ثبت شد!

{type_emoji} نوع: {type_text}
{EMOJIS['money']} مبلغ: {format_amount(amount)} ریال
{EMOJIS['description']} توضیحات: {description}
📝 شناسه تراکنش: {transaction_id}
{EMOJIS['calendar']} تاریخ: {persian_date.strftime('%Y/%m/%d %H:%M')}
"""
            await update.message.reply_text(
                success_message,
                reply_markup=get_main_menu_keyboard()
            )

async def show_filtered_report(update: Update, context: ContextTypes.DEFAULT_TYPE, period: str):
    """Show filtered transaction report based on selected period."""
    with get_db_connection() as conn:
        c = conn.cursor()
        
        # Get current Persian date
        now = get_persian_date()
        
        if period == "📅 امروز":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            period_title = "امروز"
        elif period == "📅 هفته جاری":
            start_date = now - jdatetime.timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            period_title = "هفته جاری"
        elif period == "📅 ماه جاری":
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            period_title = "ماه جاری"
        else:  # All transactions
            start_date = None
            end_date = None
            period_title = "همه تراکنش‌ها"
        
        if start_date and end_date:
            start_date_greg = start_date.togregorian()
            end_date_greg = end_date.togregorian()
            c.execute('''SELECT transaction_id, type, amount, description, date 
                        FROM transactions 
                        WHERE date BETWEEN ? AND ?
                        ORDER BY date DESC''', (start_date_greg, end_date_greg))
        else:
            c.execute('''SELECT transaction_id, type, amount, description, date 
                        FROM transactions 
                        ORDER BY date DESC''')
        
        transactions = c.fetchall()

    if not transactions:
        await update.message.reply_text(
            f"{EMOJIS['warning']} هیچ تراکنشی در بازه زمانی {period_title} یافت نشد.",
            reply_markup=get_main_menu_keyboard()
        )
        return

    # Calculate totals using list comprehension for better performance
    total_income = sum(t[2] for t in transactions if t[1] == 'income')
    total_expense = sum(t[2] for t in transactions if t[1] == 'expense')
    balance = total_income - total_expense

    # Create report using list comprehension and join for better performance
    separator = "┈" * 20
    report_parts = [
        f"{EMOJIS['report']} گزارش تراکنش‌های {period_title}",
        separator,
        f"{EMOJIS['money']} جمع درآمد: {format_amount(total_income)} ریال",
        f"{EMOJIS['money']} جمع هزینه: {format_amount(total_expense)} ریال",
        f"{EMOJIS['money']} موجودی: {format_amount(balance)} ریال",
        separator,
        f"{EMOJIS['income']} تراکنش‌های درآمدی:"
    ]

    # Process income transactions
    income_transactions = [t for t in transactions if t[1] == 'income']
    if income_transactions:
        for t in income_transactions:
            transaction_parts = [
                f"{EMOJIS['money']} مبلغ: {format_amount(t[2])} ریال",
                f"📝 شناسه تراکنش: {t[0]}"
            ]
            if t[3]:
                transaction_parts.append(f"{EMOJIS['description']} توضیحات: {t[3]}")
            transaction_parts.append(f"{EMOJIS['calendar']} تاریخ: {format_date(t[4])}")
            transaction_parts.append(separator)
            report_parts.extend(transaction_parts)
    else:
        report_parts.extend([f"هیچ تراکنش درآمدی ثبت نشده است.", separator])

    # Process expense transactions
    report_parts.extend([f"\n{EMOJIS['expense']} تراکنش‌های هزینه‌ای:"])
    expense_transactions = [t for t in transactions if t[1] == 'expense']
    if expense_transactions:
        for t in expense_transactions:
            transaction_parts = [
                f"{EMOJIS['money']} مبلغ: {format_amount(t[2])} ریال",
                f"📝 شناسه تراکنش: {t[0]}"
            ]
            if t[3]:
                transaction_parts.append(f"{EMOJIS['description']} توضیحات: {t[3]}")
            transaction_parts.append(f"{EMOJIS['calendar']} تاریخ: {format_date(t[4])}")
            transaction_parts.append(separator)
            report_parts.extend(transaction_parts)
    else:
        report_parts.extend([f"هیچ تراکنش هزینه‌ای ثبت نشده است.", separator])

    await update.message.reply_text(
        "\n".join(report_parts),
        reply_markup=get_main_menu_keyboard()
    )
    context.user_data.clear()

async def show_edit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show edit menu with options."""
    await update.message.reply_text(
        f"""
{EMOJIS['edit']} لطفاً شناسه تراکنش را وارد کنید:
{EMOJIS['warning']} شناسه تراکنش باید به صورت حرف و سه رقم باشد (مثال: a001)"""
    )
    context.user_data['waiting_for'] = 'edit_transaction_id'

def get_edit_keyboard():
    """Get edit menu keyboard."""
    keyboard = [
        [KeyboardButton("✏️ ویرایش با شناسه"), KeyboardButton("🗑️ حذف با شناسه")],
        [KeyboardButton(f"{EMOJIS['back']} بازگشت به منو")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_edit_transaction_keyboard():
    """Get keyboard for editing transaction details."""
    keyboard = [
        [KeyboardButton("✏️ ویرایش مبلغ"), KeyboardButton("✏️ ویرایش توضیحات")],
        [KeyboardButton(f"{EMOJIS['back']} بازگشت به منو")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def handle_edit_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle transaction editing process."""
    text = update.message.text

    if text == f"{EMOJIS['back']} بازگشت به منو":
        context.user_data.clear()
        await update.message.reply_text(
            "به منوی اصلی بازگشتید.",
            reply_markup=get_main_menu_keyboard()
        )
        return

    if 'waiting_for' not in context.user_data:
        await show_edit_menu(update, context)
        return

    if context.user_data['waiting_for'] == 'edit_transaction_id':
        try:
            transaction_id = text.strip().lower()
            
            if not (len(transaction_id) == 4 and 
                   transaction_id[0].isalpha() and 
                   transaction_id[0].islower() and 
                   transaction_id[1:].isdigit()):
                await update.message.reply_text(
                    f"{EMOJIS['error']} شناسه تراکنش نامعتبر است.\n"
                    f"لطفاً شناسه را به صورت حرف کوچک و سه رقم وارد کنید (مثال: a001)",
                    reply_markup=get_main_menu_keyboard()
                )
                return

            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute('''SELECT id, transaction_id, type, amount, description, date 
                            FROM transactions WHERE transaction_id = ?''', (transaction_id,))
                transaction = c.fetchone()

            if not transaction:
                await update.message.reply_text(
                    f"{EMOJIS['error']} تراکنش با شناسه {transaction_id} در سیستم وجود ندارد.\n"
                    f"لطفاً شناسه صحیح را وارد کنید یا به منوی اصلی بازگردید.",
                    reply_markup=get_main_menu_keyboard()
                )
                return

            context.user_data['editing_transaction'] = transaction
            type_emoji = EMOJIS['income'] if transaction[2] == 'income' else EMOJIS['expense']
            type_text = "درآمد" if transaction[2] == 'income' else "هزینه"
            
            keyboard = [
                [KeyboardButton("✏️ ویرایش مبلغ"), KeyboardButton("✏️ ویرایش توضیحات")],
                [KeyboardButton(f"{EMOJIS['back']} بازگشت به منو")]
            ]
            
            message_parts = [
                f"{EMOJIS['edit']} تراکنش انتخاب شده:",
                f"{type_emoji} نوع: {type_text}",
                f"{EMOJIS['money']} مبلغ: {format_amount(transaction[3])} ریال",
                f"📝 شناسه تراکنش: {transaction[1]}"
            ]
            
            if transaction[4]:
                message_parts.append(f"{EMOJIS['description']} توضیحات: {transaction[4]}")
            
            message_parts.extend([
                f"{EMOJIS['calendar']} تاریخ: {format_date(transaction[5])}",
                "لطفاً عملیات مورد نظر را انتخاب کنید:"
            ])
            
            await update.message.reply_text(
                "\n".join(message_parts),
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            context.user_data['waiting_for'] = 'edit_action'

        except Exception as e:
            logger.error(f"Error in edit transaction: {e}")
            await update.message.reply_text(
                f"{EMOJIS['error']} خطای غیرمنتظره رخ داد. لطفاً دوباره تلاش کنید.",
                reply_markup=get_main_menu_keyboard()
            )

    elif context.user_data['waiting_for'] == 'edit_action':
        if 'editing_transaction' not in context.user_data:
            await show_edit_menu(update, context)
            return

        if text == "✏️ ویرایش مبلغ":
            context.user_data['waiting_for'] = 'edit_amount'
            await update.message.reply_text(
                f"{EMOJIS['money']} مبلغ جدید را وارد کنید:\n"
                f"{EMOJIS['warning']} فقط عدد وارد کنید (مثال: 1000000)"
            )
        elif text == "✏️ ویرایش توضیحات":
            context.user_data['waiting_for'] = 'edit_description'
            await update.message.reply_text(
                f"{EMOJIS['description']} توضیحات جدید را وارد کنید:\n"
                f"{EMOJIS['warning']} توضیحات باید کوتاه و مختصر باشد"
            )

    elif context.user_data['waiting_for'] == 'edit_amount':
        if 'editing_transaction' not in context.user_data:
            await show_edit_menu(update, context)
            return

        try:
            new_amount = float(text.replace(',', ''))
            if new_amount <= 0:
                await update.message.reply_text(
                    f"{EMOJIS['error']} لطفاً یک مبلغ مثبت وارد کنید.",
                    reply_markup=get_edit_transaction_keyboard()
                )
                return

            transaction = context.user_data['editing_transaction']
            try:
                with get_db_connection() as conn:
                    c = conn.cursor()
                    c.execute('UPDATE transactions SET amount = ? WHERE id = ?',
                             (new_amount, transaction[0]))
                    conn.commit()

                await update.message.reply_text(
                    f"{EMOJIS['success']} مبلغ تراکنش با موفقیت ویرایش شد.\n\nآیا می‌خواهید توضیحات را هم ویرایش کنید؟",
                    reply_markup=get_edit_transaction_keyboard()
                )
                context.user_data['waiting_for'] = 'edit_action'
            except sqlite3.Error as e:
                logger.error(f"Database error while updating amount: {e}")
                await update.message.reply_text(
                    f"{EMOJIS['error']} خطا در ویرایش مبلغ. لطفاً دوباره تلاش کنید.",
                    reply_markup=get_edit_transaction_keyboard()
                )

        except ValueError:
            await update.message.reply_text(
                f"{EMOJIS['error']} لطفاً یک عدد معتبر وارد کنید.",
                reply_markup=get_edit_transaction_keyboard()
            )

    elif context.user_data['waiting_for'] == 'edit_description':
        if 'editing_transaction' not in context.user_data:
            await show_edit_menu(update, context)
            return

        new_description = text
        transaction = context.user_data['editing_transaction']
        
        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute('UPDATE transactions SET description = ? WHERE id = ?',
                         (new_description, transaction[0]))
                conn.commit()

            await update.message.reply_text(
                f"{EMOJIS['success']} توضیحات تراکنش با موفقیت ویرایش شد.\n\nآیا می‌خواهید مبلغ را هم ویرایش کنید؟",
                reply_markup=get_edit_transaction_keyboard()
            )
            context.user_data['waiting_for'] = 'edit_action'
        except sqlite3.Error as e:
            logger.error(f"Database error while updating description: {e}")
            await update.message.reply_text(
                f"{EMOJIS['error']} خطا در ویرایش توضیحات. لطفاً دوباره تلاش کنید.",
                reply_markup=get_edit_transaction_keyboard()
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