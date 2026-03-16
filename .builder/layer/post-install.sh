#!/bin/bash

REPO_PATH="/home/opencal/OpeCAL"


git clone https://github.com/computed-axial-lithography/OpenCAL.git $REPO_PATH

cd $REPO_PATH
chmod +x setup.sh
sudo -u opencal ./setup.sh

# System Settings


# Startup Script
cat <<EOF > /etc/systemd/system/opencal-startup.service
[Unit]
Description=Opencal Startup Script
After=network.target

[Service]
ExecStart=.venv/bin/python3 -m opencal
WorkingDirectory=/home/opencal/OpenCAL
StandardOutput=inherit
StandardError=inherit
Restart=always
User=opencal

[Install]
WantedBy=multi-user.target
EOF

systemctl enable opencal-startup.service


