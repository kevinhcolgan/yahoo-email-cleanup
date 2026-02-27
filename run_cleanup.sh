#!/bin/bash
cd /Users/kevincolgan/code/imap_email_deleter
source venv/bin/activate
python cleanup_yahoo.py >> cleanup.log 2>&1
