# Bitmex Risk Manager

## What It Is

Bitmex position/order managaement and position sizer with Telegram Bot integration

### One-Liner 1st Time VPS Setup

sudo apt update && sudo apt upgrade -y && sudo apt install python3.7 -y && sudo apt-get install python3-pip -y && sudo apt-get install python3-venv -y && git clone https://github.com/zalzibab/risk_managers.git && cd risk_managers

### How To Use

On initial VPS setup, run one-liner above.

Create a new screen session > screen -S risk_managers

Run the following one-liner

python3 -m venv env && source env/bin/activate && python -m pip install -r requirements.txt && python rm_bitmex.py

When your session is complete, detach from the screen session with keyboard input > Ctrl+a d

When you come back > screen -r risk_managers will reattach your screen session, already in your python virtual environment

#### To Get Updated Repo

screen -r risk_managers && git pull && python -m pip install -r requirements.txt






