import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
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
        [InlineKeyboardButton("Record Income", callback_data='income')],
        [InlineKeyboardButton("Record Expense", callback_data='expense')],
        [InlineKeyboardButton("View Report", callback_data='report')],
        [InlineKeyboardButton("Edit Transaction", callback_data='edit')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message with the main menu when the command /start is issued."""
    await update.message.reply_text(
        'Welcome to your Accounting Bot! Please choose an option:',
        reply_markup=get_main_menu_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses."""
    query = update.callback_query
    await query.answer()

    if query.data == 'income':
        context.user_data['waiting_for'] = 'income_amount'
        await query.message.reply_text('Please enter the income amount:')
    
    elif query.data == 'expense':
        context.user_data['waiting_for'] = 'expense_amount'
        await query.message.reply_text('Please enter the expense amount:')
    
    elif query.data == 'report':
        await show_report(update, context)
    
    elif query.data == 'edit':
        await show_edit_menu(update, context)

async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle amount input for income/expense."""
    if 'waiting_for' not in context.user_data:
        return

    try:
        amount = float(update.message.text)
        if amount <= 0:
            await update.message.reply_text('Please enter a positive amount.')
            return

        transaction_type = 'income' if context.user_data['waiting_for'] == 'income_amount' else 'expense'
        
        # Store the amount and ask for description
        context.user_data['amount'] = amount
        context.user_data['waiting_for'] = f'{transaction_type}_description'
        
        await update.message.reply_text('Please enter a description for this transaction:')
    
    except ValueError:
        await update.message.reply_text('Please enter a valid number.')

async def handle_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle description input and save the transaction."""
    if 'waiting_for' not in context.user_data or 'amount' not in context.user_data:
        return

    description = update.message.text
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
        f'{transaction_type.capitalize()} of {amount} recorded successfully!',
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
        await update.callback_query.message.reply_text(
            'No transactions found.',
            reply_markup=get_main_menu_keyboard()
        )
        return

    report = "Last 10 transactions:\n\n"
    for t in transactions:
        report += f"{t[0].capitalize()}: {t[1]} - {t[2]} ({t[3]})\n"

    await update.callback_query.message.reply_text(
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
        await update.callback_query.message.reply_text(
            'No transactions to edit.',
            reply_markup=get_main_menu_keyboard()
        )
        return

    keyboard = []
    for t in transactions:
        keyboard.append([InlineKeyboardButton(
            f"{t[1].capitalize()}: {t[2]} - {t[3]}",
            callback_data=f'edit_{t[0]}'
        )])

    keyboard.append([InlineKeyboardButton("Back to Main Menu", callback_data='main_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.reply_text(
        'Select a transaction to edit:',
        reply_markup=reply_markup
    )

def main():
    """Start the bot."""
    # Initialize database
    init_db()

    # Create the Application
    application = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_description))

    # Start the Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 