#!/bin/bash
cd /Users/kevincolgan/code/imap_email_deleter
source venv/bin/activate
echo "[$(date '+%Y-%m-%d %H:%M:%S')]" >> cleanup.log
python cleanup_yahoo.py >> cleanup.log 2>&1
