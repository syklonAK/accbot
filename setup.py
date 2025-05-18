import os
import sys
import subprocess
import getpass

def check_python_version():
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required.")
        sys.exit(1)

def install_dependencies():
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def create_env_file():
    token = getpass.getpass("Enter your Telegram bot token: ")
    with open(".env", "w") as f:
        f.write(f"TELEGRAM_TOKEN={token}\n")
    print(".env file created successfully.")

def main():
    print("Welcome to the Telegram Bot Setup!")
    check_python_version()
    install_dependencies()
    create_env_file()
    print("Setup completed successfully. You can now run the bot using 'python bot.py'.")

if __name__ == "__main__":
    main() 