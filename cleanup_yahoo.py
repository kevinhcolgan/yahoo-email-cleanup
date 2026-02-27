from imap_tools import MailBox, AND
import csv
import os
import socket
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Configuration
IMAP_SERVER = 'imap.mail.yahoo.com'
EMAIL = 'kcolgan@yahoo.com'
APP_PASSWORD = os.getenv('YAHOO_APP_PASSWORD')
CSV_FILE = 'senders_to_delete.csv'
DRY_RUN = False  # Set to False to actually delete
BATCH_SIZE = 100  # Process in chunks of this many emails
LIMIT_PER_SENDER = None  # Set to a number to limit emails per sender (e.g., 1000), or None for all
DAYS_BETWEEN_RUNS = 7  # Run cleanup only if N days have passed since last run
LAST_RUN_FILE = '.last_cleanup_run'  # Track last successful run

# Set socket timeout to avoid hanging
socket.setdefaulttimeout(30)

def should_run_cleanup():
    """Check if enough time has passed since last cleanup run"""
    last_run_path = Path(LAST_RUN_FILE)
    
    if not last_run_path.exists():
        return True  # Never ran before, so run now
    
    last_run_time = last_run_path.stat().st_mtime
    current_time = time.time()
    days_since_run = (current_time - last_run_time) / (86400)  # 86400 seconds in a day
    
    if days_since_run >= DAYS_BETWEEN_RUNS:
        return True
    
    return False

def mark_cleanup_run():
    """Update timestamp of last successful cleanup"""
    Path(LAST_RUN_FILE).touch()

def main():
    print("Yahoo Mail Cleanup Script")
    print("="*50)
    
    # Check if we should run
    if not should_run_cleanup():
        print("⏭️  Skipping - last cleanup was less than 7 days ago")
        return
    
    if DRY_RUN:
        print("⚠️  DRY RUN MODE - No emails will be deleted")
    else:
        print("🔴 LIVE MODE - Emails WILL be deleted")
    
    if not APP_PASSWORD:
        print("❌ Error: YAHOO_APP_PASSWORD not found in .env file")
        return
    
    with MailBox(IMAP_SERVER).login(EMAIL, APP_PASSWORD) as mailbox:
        print(f"✓ Connected to {EMAIL}\n")
        
        # Read senders from CSV
        with open(CSV_FILE) as f:
            senders = [row['email'] for row in csv.DictReader(f)]
        
        print(f"Processing {len(senders)} senders...\n")
        total_deleted = 0
        
        # Process each sender
        for idx, sender in enumerate(senders, 1):
            print(f"[{idx}/{len(senders)}] {sender}")
            
            try:
                # Find emails from this sender - just get count first
                print(f"  Searching mailbox...")
                uids = mailbox.uids(AND(from_=sender))
                
                if LIMIT_PER_SENDER and len(uids) > LIMIT_PER_SENDER:
                    uids = uids[:LIMIT_PER_SENDER]
                    print(f"  Limited to {LIMIT_PER_SENDER} emails")
                
                count = len(uids)
                
                if count > 0:
                    if not DRY_RUN:
                        # Delete in batches
                        for i in range(0, len(uids), BATCH_SIZE):
                            batch = uids[i:i+BATCH_SIZE]
                            mailbox.delete(batch)
                            print(f"  ✓ Deleted batch {i//BATCH_SIZE + 1}/{(len(uids) + BATCH_SIZE - 1)//BATCH_SIZE}")
                        print(f"  ✓ Total: {count} emails deleted")
                    else:
                        print(f"  ℹ Would delete {count} emails in {(count + BATCH_SIZE - 1)//BATCH_SIZE} batch(es)")
                    total_deleted += count
                else:
                    print(f"  ℹ No matching emails found")
                
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                continue
        
        print(f"\n{'='*50}")
        action = "Would delete" if DRY_RUN else "Deleted"
        print(f"{action}: {total_deleted} emails")
        print(f"{'='*50}")
        
        # Mark successful run
        mark_cleanup_run()

if __name__ == "__main__":
    main()
