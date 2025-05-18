# Telegram Bot for Transaction and Debtor Management

A Telegram bot for managing transactions and debtors. The bot allows users to register income and expenses, generate reports, and manage debtors.

## Features

- **Transaction Management**:
  - Register income and expenses
  - Generate reports for today, current week, current month, or all transactions
  - Edit transaction details

- **Debtor Management**:
  - Register new debtors
  - View list of debtors
  - Edit debtor details
  - Automatically delete paid debtors after a specified time

- **Data Management**:
  - Clear all transaction reports
  - Clear debtor list
  - Test bot functionality

## Commands

- `/start` - Start the bot
- `/set_debtor` - Register a new debtor
- `/debtor_list` - View list of debtors
- `/edit_debtor` - Edit debtor details
- `/clear_data` - Clear all data
- `/clear_rep` - Clear transaction reports
- `/clear_debtor_list` - Clear debtor list
- `/test` - Test bot functionality

## Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up your Telegram bot token in the environment variables
4. Run the bot:
   ```
   python bot.py
   ```

## Dependencies

- python-telegram-bot
- pytz
- python-dotenv
- sqlite3

## License

This project is licensed under the MIT License. 