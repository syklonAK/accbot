#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

# Create temporary directory
TEMP_DIR="/tmp/accbot-install"
echo -e "${YELLOW}Creating temporary directory...${NC}"
rm -rf $TEMP_DIR
mkdir -p $TEMP_DIR
cd $TEMP_DIR

# Clone repository
echo -e "${YELLOW}Cloning repository...${NC}"
git clone https://github.com/syklonAK/accbot.git .

# Make accbot script executable
chmod +x accbot

# Move files to /opt/telegram-bot
echo -e "${YELLOW}Installing bot...${NC}"
mkdir -p /opt/telegram-bot
cp -r * /opt/telegram-bot/
cd /opt/telegram-bot

# Create symlink for accbot command
ln -sf /opt/telegram-bot/accbot /usr/local/bin/accbot

# Clean up
rm -rf $TEMP_DIR

echo -e "${GREEN}Installation completed!${NC}"
echo -e "${YELLOW}You can now use the following commands:${NC}"
echo -e "  - ${GREEN}accbot${NC} - Open bot management menu"
echo -e "  - ${GREEN}accbot --help${NC} - Show help message"
echo -e "\n${BLUE}Starting bot management menu...${NC}"
sleep 2
accbot 