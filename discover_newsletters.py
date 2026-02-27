from imap_tools import MailBox, AND
import csv
import os
import re
from collections import defaultdict
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Configuration
IMAP_SERVER = 'imap.mail.yahoo.com'
EMAIL = 'kcolgan@yahoo.com'
APP_PASSWORD = os.getenv('YAHOO_APP_PASSWORD')
OUTPUT_FILE = 'discovered_newsletters.csv'

# Patterns that suggest a newsletter/marketing email
NEWSLETTER_PATTERNS = [
    r'newsletter',
    r'noreply',
    r'no-reply',
    r'marketing',
    r'updates',
    r'digest',
    r'announce',
    r'notification',
    r'alert',
    r'promo',
    r'subscribe',
    r'news',
    r'hello@',
    r'info@',
]

def check_for_newsletter_indicators(msg):
    """Check if an email has newsletter indicators"""
    indicators = []
    
    # Check sender address
    sender = msg.from_
    if sender:
        sender_lower = sender.lower()
        for pattern in NEWSLETTER_PATTERNS:
            if re.search(pattern, sender_lower):
                indicators.append(f"sender:{pattern}")
                break
    
    # Check for List-ID header (standard mailing list indicator)
    if hasattr(msg, 'headers') and msg.headers:
        if 'List-ID' in msg.headers:
            indicators.append("List-ID header")
        if 'List-Unsubscribe' in msg.headers:
            indicators.append("List-Unsubscribe header")
    
    return indicators

def main():
    print("Newsletter Discovery Script")
    print("="*50)
    
    if not APP_PASSWORD:
        print("❌ Error: YAHOO_APP_PASSWORD not found in .env file")
        return
    
    with MailBox(IMAP_SERVER).login(EMAIL, APP_PASSWORD) as mailbox:
        print(f"✓ Connected to {EMAIL}\n")
        print("Scanning mailbox for newsletter patterns...")
        
        # Collect all emails with their sender info
        sender_info = defaultdict(lambda: {
            'count': 0,
            'indicators': set(),
            'first_seen': None,
            'last_seen': None,
        })
        
        try:
            # Fetch all emails (limit to recent ones for speed)
            print("Fetching emails...")
            email_count = 0
            
            for msg in mailbox.fetch():
                email_count += 1
                if email_count % 500 == 0:
                    print(f"  Scanned {email_count} emails...")
                
                sender = msg.from_
                if not sender:
                    continue
                
                indicators = check_for_newsletter_indicators(msg)
                
                # Only track emails with newsletter indicators
                if indicators:
                    if sender not in sender_info:
                        sender_info[sender]['first_seen'] = msg.date
                    
                    sender_info[sender]['count'] += 1
                    sender_info[sender]['last_seen'] = msg.date
                    
                    # Combine indicators
                    for indicator in indicators:
                        sender_info[sender]['indicators'].add(indicator)
            
            print(f"  Total emails scanned: {email_count}")
        
        except KeyboardInterrupt:
            print("\n⚠️  Scan interrupted by user")
        except Exception as e:
            print(f"⚠️  Error during scan: {str(e)}")
    
    # Sort by email count (most frequent first)
    sorted_senders = sorted(
        sender_info.items(),
        key=lambda x: x[1]['count'],
        reverse=True
    )
    
    print(f"\nFound {len(sorted_senders)} potential newsletter senders\n")
    
    # Write to CSV
    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['email', 'email_count', 'indicators', 'last_received'])
        
        for sender, info in sorted_senders:
            indicators_str = '; '.join(sorted(info['indicators']))
            last_seen = info['last_seen'].strftime('%Y-%m-%d') if info['last_seen'] else ''
            writer.writerow([
                sender,
                info['count'],
                indicators_str,
                last_seen,
            ])
    
    print(f"✓ Results saved to {OUTPUT_FILE}")
    print(f"\nTop 10 newsletter candidates:")
    print("-" * 80)
    for i, (sender, info) in enumerate(sorted_senders[:10], 1):
        indicators_str = '; '.join(sorted(info['indicators']))
        print(f"{i}. {sender}")
        print(f"   Count: {info['count']} | Indicators: {indicators_str}")
    
    print("\n" + "="*50)
    print(f"Review {OUTPUT_FILE} and decide which ones to delete")
    print("Then copy rows you want to delete to senders_to_delete.csv")
    print("="*50)

if __name__ == "__main__":
    main()
