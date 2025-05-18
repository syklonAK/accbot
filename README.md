# Telegram Accounting Bot

A Telegram bot for managing personal accounting with an intuitive button-based interface.

## Version 1.0.0

### Features
- Record income and expenses
- View transaction reports
- Edit existing transactions
- User-friendly button interface
- SQLite database for data persistence
- Persian language interface
- Beautiful emoji-enhanced UI
- 2x2 button layout for better organization

### Changelog
#### v1.0.0 (Initial Release)
- Basic accounting functionality
- Persian language support
- Emoji-enhanced interface
- Transaction recording and reporting
- SQLite database integration
- User-friendly error handling
- Formatted amount and date display

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the project root and add your Telegram bot token:
```
TELEGRAM_TOKEN=your_bot_token_here
```

3. Run the bot:
```bash
python bot.py
```

## Usage

1. Start the bot by sending `/start` command
2. Use the buttons to:
   - Record Income: Add new income entries
   - Record Expense: Add new expense entries
   - View Report: See your recent transactions
   - Edit Transaction: Modify existing transactions

## Commands

- `/start` - Start the bot and show the main menu
- `/in` - Quick command to record income
- `/out` - Quick command to record expenses
- `/report` - Quick command to view transaction report

## Database

The bot uses SQLite to store transactions in a local database file (`accounting.db`). The database is automatically created when you first run the bot.

## Future Plans
- Transaction editing and deletion
- Export reports to PDF/Excel
- Category management
- Date-based filtering
- Multi-user support
- Backup/restore functionality 