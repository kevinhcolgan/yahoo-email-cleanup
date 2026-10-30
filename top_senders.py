from imap_tools import MailBox
import csv
import os
from collections import defaultdict
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Configuration
IMAP_SERVER = 'imap.mail.yahoo.com'
EMAIL = os.getenv('YAHOO_MAIL_ACCOUNT')
APP_PASSWORD = os.getenv('YAHOO_APP_PASSWORD')
OUTPUT_FILE = 'top_senders.csv'

def main():
    print("Top Senders Scanner")
    print("="*50)
    
    if not APP_PASSWORD:
        print("❌ Error: YAHOO_APP_PASSWORD not found in .env file")
        return
    
    sender_counts = defaultdict(int)
    
    with MailBox(IMAP_SERVER).login(EMAIL, APP_PASSWORD) as mailbox:
        print(f"✓ Connected to {EMAIL}\n")
        print("Scanning senders (this may take a minute)...")
        
        email_count = 0
        try:
            for msg in mailbox.fetch():
                email_count += 1
                if email_count % 1000 == 0:
                    print(f"  Processed {email_count} emails...")
                
                sender = msg.from_
                if sender:
                    sender_counts[sender] += 1
        
        except KeyboardInterrupt:
            print(f"\n⚠️  Stopped at {email_count} emails")
    
    # Sort by count (highest first)
    sorted_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\nFound {len(sorted_senders)} unique senders across {email_count} emails")
    
    # Write to CSV
    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['email', 'count'])
        for sender, count in sorted_senders:
            writer.writerow([sender, count])
    
    print(f"\n✓ Saved to {OUTPUT_FILE}")
    print(f"\nTop 30 senders by volume:")
    print("-" * 80)
    for i, (sender, count) in enumerate(sorted_senders[:30], 1):
        print(f"{i:2d}. ({count:5d}) {sender}")
    
    print("\n" + "="*50)
    print("Review the CSV and decide which to add to senders_to_delete.csv")
    print("="*50)

if __name__ == "__main__":
    main()
