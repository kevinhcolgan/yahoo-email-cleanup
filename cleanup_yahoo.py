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

# Retry configuration
MAX_RETRIES = 3  # Number of retries for failed operations
RETRY_DELAY = 5  # Seconds to wait between retries
CONNECTION_TIMEOUT = 60  # Increased timeout for IMAP operations
OPERATION_TIMEOUT = 45  # Timeout for individual operations

# Set socket timeout to avoid hanging
socket.setdefaulttimeout(CONNECTION_TIMEOUT)

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

def retry_with_backoff(func, max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    """Retry a function with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return func()
        except (TimeoutError, socket.timeout, OSError) as e:
            if attempt < max_retries - 1:
                wait_time = delay * (2 ** attempt)  # Exponential backoff
                print(f"  ⚠️  Timeout on attempt {attempt + 1}/{max_retries}, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise Exception(f"Failed after {max_retries} attempts: {str(e)}")
        except Exception as e:
            # For non-timeout errors, don't retry
            raise e

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
    
    # Connect with retry logic
    mailbox = None
    try:
        def connect():
            return MailBox(IMAP_SERVER).login(EMAIL, APP_PASSWORD)

        mailbox = retry_with_backoff(connect)
        print(f"✓ Connected to {EMAIL}\n")

        # Read senders from CSV
        with open(CSV_FILE) as f:
            senders = [row['email'] for row in csv.DictReader(f)]

        print(f"Processing {len(senders)} senders...\n")
        total_deleted = 0
        failed_senders = []

        # Process each sender
        for idx, sender in enumerate(senders, 1):
            print(f"[{idx}/{len(senders)}] {sender}")

            try:
                # Find emails from this sender with retry logic
                print(f"  Searching mailbox...")

                def search_operation():
                    return mailbox.uids(AND(from_=sender))

                uids = retry_with_backoff(search_operation)

                if LIMIT_PER_SENDER and len(uids) > LIMIT_PER_SENDER:
                    uids = uids[:LIMIT_PER_SENDER]
                    print(f"  Limited to {LIMIT_PER_SENDER} emails")

                count = len(uids)

                if count > 0:
                    if not DRY_RUN:
                        # Delete in batches with retry logic
                        for i in range(0, len(uids), BATCH_SIZE):
                            batch = uids[i:i+BATCH_SIZE]

                            def delete_operation():
                                return mailbox.delete(batch)

                            retry_with_backoff(delete_operation)
                            print(f"  ✓ Deleted batch {i//BATCH_SIZE + 1}/{(len(uids) + BATCH_SIZE - 1)//BATCH_SIZE}")
                        print(f"  ✓ Total: {count} emails deleted")
                    else:
                        print(f"  ℹ Would delete {count} emails in {(count + BATCH_SIZE - 1)//BATCH_SIZE} batch(es)")
                    total_deleted += count
                else:
                    print(f"  ℹ No matching emails found")

            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                failed_senders.append(sender)
                continue

        print(f"\n{'='*50}")
        action = "Would delete" if DRY_RUN else "Deleted"
        print(f"{action}: {total_deleted} emails")
        if failed_senders:
            print(f"Failed senders ({len(failed_senders)}): {', '.join(failed_senders[:5])}")
            if len(failed_senders) > 5:
                print(f"  ... and {len(failed_senders) - 5} more")
        print(f"{'='*50}")

        # Mark successful run
        mark_cleanup_run()

    finally:
        # Safely close connection with retry logic
        if mailbox:
            try:
                def logout_operation():
                    return mailbox.logout()

                retry_with_backoff(logout_operation)
                print("✓ Disconnected successfully")
            except Exception as e:
                print(f"⚠️  Warning: Error during logout: {str(e)}")
                # Try to force close the connection
                try:
                    if hasattr(mailbox, 'client'):
                        mailbox.client.shutdown()
                except:
                    pass

if __name__ == "__main__":
    main()
