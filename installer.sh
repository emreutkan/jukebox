#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'
REPO_URL="https://github.com/emreutkan/jukebox.git"
INSTALL_DIR="$HOME"

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (sudo ./installer.sh)${NC}"
    exit
fi

cd $INSTALL_DIR
echo -e "${GREEN}Cloning the jukebox repository to the root directory.${NC}"
git clone "$REPO_URL"
cd jukebox || exit

if command -v pacman &> /dev/null; then
    PACKAGE_MANAGER_INSTALL="sudo pacman -S --noconfirm"
    PACKAGE_MANAGER_UPDATE="sudo pacman -Syu"
    echo -e "${GREEN}Arch Based Distro detected.${NC}"
elif command -v apt-get &> /dev/null; then
    PACKAGE_MANAGER_INSTALL="sudo apt-get install -y"
    PACKAGE_MANAGER_UPDATE="sudo apt-get update"
    echo -e "${GREEN}Debian Based Distro detected.${NC}"
else
    echo -e "${RED}Supported package manager not found. Install packages manually.${NC}"
    exit 1
fi

echo -e "${GREEN}Updating package manager${NC}"
$PACKAGE_MANAGER_UPDATE

DEPENDENCIES="aircrack-ng airgraph-ng net-tools python3 python3-pip git"
for dep in $DEPENDENCIES; do
    if ! command -v $dep &> /dev/null; then
        echo -e "${GREEN}Installing $dep${NC}"
        $PACKAGE_MANAGER_INSTALL $dep
    else
        echo -e "${GREEN}$dep already installed.${NC}"
    fi
done

if [ ! -d "venv" ]; then
    echo -e "${GREEN}Creating a virtual environment${NC}"
    python3 -m venv venv
fi

echo -e "${GREEN}Activating the virtual environment and installing Python dependencies${NC}"
source venv/bin/activate
pip install -r requirements.txt

echo -e "${GREEN}Creating a jukebox command...${NC}"
echo "#!/bin/bash
if [ \"\$EUID\" -ne 0 ]; then
    echo 'Please run as root (sudo jukebox)'
    exit
fi
cd $INSTALL_DIR/jukebox
source venv/bin/activate
python jukebox.py" > jukebox

chmod +x jukebox
sudo mv jukebox /usr/local/bin/jukebox

echo -e "${GREEN}Installation complete. You can now run by typing 'sudo jukebox' in the terminal.${NC}"
