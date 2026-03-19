#!/bin/bash

echo "Starting OpenCAL setup..."

sudo apt-get update

if [ -f "apt-requirements.txt" ]; then
  echo "Installing system dependencies from apt-requirements.txt..."
  grep -v '^#' apt-requirements.txt | xargs sudo apt-get install -y
else
  echo "apt-requirements.txt not found, skipping system packages."
fi

sudo apt-get install -y python3-venv python3-pip

# Hardware interface config
sudo raspi-config nonint do_i2c 0
echo "I2C Enabled"
sudo raspi-config nonint do_spi 0
echo "SPI Enabled"

sudo usermod -a -G i2c,spi opencal


VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating Python virtual environment"
  python3 -m venv --system-site-packages $VENV_DIR
fi

if [ -f "requirements.txt" ]; then 
  $VENV_DIR/bin/pip install --upgrade pip
  $VENV_DIR/bin/pip install -r requirements.txt
else
  echo "requirements.txt not found, skipping Python packages."
fi

echo "Setup complete"


