#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Starting Telegram Bot Installation...${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

# Update system
echo -e "${YELLOW}Updating system packages...${NC}"
apt update && apt upgrade -y

# Install required system packages
echo -e "${YELLOW}Installing system dependencies...${NC}"
apt install -y python3 python3-pip python3-venv git screen

# Create bot directory
echo -e "${YELLOW}Setting up bot directory...${NC}"
mkdir -p /opt/telegram-bot
cd /opt/telegram-bot

# Clone repository (replace with your repository URL)
echo -e "${YELLOW}Cloning repository...${NC}"
git clone https://github.com/yourusername/accbot.git .

# Create virtual environment
echo -e "${YELLOW}Creating Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Create systemd service
echo -e "${YELLOW}Creating systemd service...${NC}"
cat > /etc/systemd/system/telegram-bot.service << EOL
[Unit]
Description=Telegram Bot Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/telegram-bot
Environment=PATH=/opt/telegram-bot/venv/bin
ExecStart=/opt/telegram-bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

# Get bot token
echo -e "${YELLOW}Please enter your Telegram bot token:${NC}"
read -sp "Token: " token
echo "TELEGRAM_TOKEN=$token" > .env

# Set permissions
chown -R root:root /opt/telegram-bot
chmod -R 755 /opt/telegram-bot

# Enable and start service
echo -e "${YELLOW}Enabling and starting bot service...${NC}"
systemctl daemon-reload
systemctl enable telegram-bot
systemctl start telegram-bot

# Check service status
echo -e "${YELLOW}Checking service status...${NC}"
systemctl status telegram-bot

echo -e "${GREEN}Installation completed!${NC}"
echo -e "${GREEN}Bot is now running as a system service.${NC}"
echo -e "${YELLOW}Useful commands:${NC}"
echo -e "  - Check status: ${GREEN}systemctl status telegram-bot${NC}"
echo -e "  - View logs: ${GREEN}journalctl -u telegram-bot -f${NC}"
echo -e "  - Stop bot: ${GREEN}systemctl stop telegram-bot${NC}"
echo -e "  - Start bot: ${GREEN}systemctl start telegram-bot${NC}"
echo -e "  - Restart bot: ${GREEN}systemctl restart telegram-bot${NC}" 