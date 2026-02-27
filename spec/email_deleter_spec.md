# Yahoo Mail Cleanup - Recommended Implementation Plan

## Executive Summary

Your IMAP script idea is **excellent and technically sound**. This approach offers the best combination of speed, control, privacy, and cost-effectiveness for bulk deleting old emails from Yahoo Mail.

---

## Why IMAP Script is the Best Choice

### Yahoo Mail IMAP Support
- ✅ **Fully supported** - Server: `imap.mail.yahoo.com`, Port: 993
- ✅ **Native bulk deletion** - IMAP protocol handles this efficiently
- ✅ **No rate limits** - Unlike slow web interface
- ⚠️ **Requires App Password** - Not your regular Yahoo password

### Comparison Matrix

| Feature | IMAP Script | Yahoo Web UI | 3rd Party Services |
|---------|-------------|--------------|-------------------|
| **Speed** | ✅ Fast | ❌ Slow | ⚠️ Varies |
| **Control** | ✅ Full | ⚠️ Limited | ❌ No control |
| **Privacy** | ✅ Local only | ✅ Direct | ❌ 3rd party reads emails |
| **Cost** | ✅ Free | ✅ Free | ⚠️ Often paid |
| **Bulk Delete** | ✅ Excellent | ❌ Poor | ✅ Good |
| **Target by Sender** | ✅ Easy | ⚠️ Manual | ✅ Automated |
| **Repeatable** | ✅ Script it | ❌ Manual work | ⚠️ Varies |

---

## Recommended Python Library: `imap_tools`

**Why this library:**
- Trust Score: 7.4/10
- 41 code examples available
- Modern, Pythonic syntax
- Excellent documentation
- Active maintenance
- Built-in chunking for bulk operations

**Alternative:** `IMAPClient` (Trust Score 9.3/10) - More low-level control but steeper learning curve

---

## Implementation Plan

### Phase 1: Preparation (30 minutes)

1. **Install the library**
   ```bash
   pip install imap-tools
   ```

2. **Generate Yahoo App Password**
   - Navigate to: Yahoo Account Security → "Generate app password"
   - Select "Other App" and name it "Email Cleanup Script"
   - Copy the generated password (16 characters)
   - **Never use your regular Yahoo password for IMAP**

3. **Create sender list (CSV)**
   - Manually identify top newsletter senders using Yahoo search
   - Create `senders_to_delete.csv` with format:
     ```csv
     email,description
     newsletters@e.economist.com,Economist Newsletter
     updates@newsletter.com,Random Updates
     ```
   - Prioritize by volume (most emails first)

### Phase 2: Basic Script (15 minutes)

Create `cleanup_yahoo.py`:

```python
from imap_tools import MailBox, AND
import csv
import datetime

# Configuration
IMAP_SERVER = 'imap.mail.yahoo.com'
EMAIL = 'your_email@yahoo.com'
APP_PASSWORD = 'your_app_password_here'  # 16-char Yahoo app password
CSV_FILE = 'senders_to_delete.csv'

# Connect to Yahoo Mail
with MailBox(IMAP_SERVER).login(EMAIL, APP_PASSWORD) as mailbox:
    print(f"Connected to {EMAIL}")
    
    # Read senders from CSV
    with open(CSV_FILE) as f:
        senders = [row['email'] for row in csv.DictReader(f)]
    
    total_deleted = 0
    
    # Process each sender
    for sender in senders:
        print(f"\nProcessing: {sender}")
        
        # Find all emails from this sender
        uids = [msg.uid for msg in mailbox.fetch(AND(from_=sender))]
        
        if uids:
            # Delete in chunks of 100 to avoid server limits
            mailbox.delete(uids, chunks=100)
            total_deleted += len(uids)
            print(f"  ✓ Deleted {len(uids)} emails")
        else:
            print(f"  ℹ No emails found")
    
    print(f"\n{'='*50}")
    print(f"Total deleted: {total_deleted} emails")
    print(f"{'='*50}")
```

### Phase 3: Enhanced Script with Safety Features (Optional)

Add these features for production use:

```python
from imap_tools import MailBox, AND
import csv
import datetime
import time

# Configuration
IMAP_SERVER = 'imap.mail.yahoo.com'
EMAIL = 'your_email@yahoo.com'
APP_PASSWORD = 'your_app_password_here'
CSV_FILE = 'senders_to_delete.csv'
DRY_RUN = True  # Set to False to actually delete

# Optional: Delete old emails by date
DELETE_BEFORE_DATE = datetime.date(2023, 1, 1)  # Delete emails before this date

def main():
    print("Yahoo Mail Cleanup Script")
    print("="*50)
    
    if DRY_RUN:
        print("⚠️  DRY RUN MODE - No emails will be deleted")
    
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
                # Find emails from this sender
                # Optional: Add date filter
                uids = [msg.uid for msg in mailbox.fetch(
                    AND(from_=sender, date_lt=DELETE_BEFORE_DATE)
                )]
                
                if uids:
                    count = len(uids)
                    if not DRY_RUN:
                        mailbox.delete(uids, chunks=100)
                        print(f"  ✓ Deleted {count} emails")
                    else:
                        print(f"  ℹ Would delete {count} emails")
                    total_deleted += count
                else:
                    print(f"  ℹ No matching emails found")
                
                # Be nice to the server
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                continue
        
        print(f"\n{'='*50}")
        action = "Would delete" if DRY_RUN else "Deleted"
        print(f"{action}: {total_deleted} emails")
        print(f"{'='*50}")

if __name__ == "__main__":
    main()
```

---

## Testing Strategy

### Step 1: Dry Run Test
1. Set `DRY_RUN = True` in the script
2. Add ONE low-risk sender to CSV
3. Run script to see what would be deleted
4. Review the count

### Step 2: Small Real Test
1. Set `DRY_RUN = False`
2. Keep only ONE sender in CSV
3. Run script and verify deletion in Yahoo web interface
4. Check that space was freed up

### Step 3: Full Scale
1. Add all senders to CSV
2. Run script for complete cleanup
3. Monitor progress in terminal

---

## Advanced Usage Examples

### Delete All Emails Older Than a Specific Date

```python
from imap_tools import MailBox, AND
import datetime

with MailBox('imap.mail.yahoo.com').login(EMAIL, APP_PASSWORD) as mailbox:
    # Delete everything before Jan 1, 2023
    old_date = datetime.date(2023, 1, 1)
    old_uids = mailbox.uids(AND(date_lt=old_date))
    
    if old_uids:
        mailbox.delete(old_uids, chunks=100)
        print(f"Deleted {len(old_uids)} old emails")
```

### Delete By Subject Pattern

```python
from imap_tools import MailBox, AND

with MailBox('imap.mail.yahoo.com').login(EMAIL, APP_PASSWORD) as mailbox:
    # Delete all "Daily Digest" emails
    uids = [msg.uid for msg in mailbox.fetch(AND(subject='Daily Digest'))]
    
    if uids:
        mailbox.delete(uids, chunks=100)
        print(f"Deleted {len(uids)} digest emails")
```

### Combine Multiple Criteria

```python
from imap_tools import MailBox, AND
import datetime

with MailBox('imap.mail.yahoo.com').login(EMAIL, APP_PASSWORD) as mailbox:
    # Delete old newsletters (before 2024 AND from specific senders)
    criteria = AND(
        from_='newsletters@example.com',
        date_lt=datetime.date(2024, 1, 1)
    )
    
    uids = [msg.uid for msg in mailbox.fetch(criteria)]
    if uids:
        mailbox.delete(uids, chunks=100)
```

---

## Safety Best Practices

### Before Running

1. **Backup Important Emails**
   - Export critical emails to .eml files first
   - Or forward them to another account

2. **Test with Low-Risk Sender**
   - Choose newsletters you definitely don't need
   - Avoid senders that might have important receipts/confirmations

3. **Review Your CSV**
   - Double-check all email addresses
   - One typo could delete wrong emails

### During Execution

4. **Use Dry Run Mode First**
   - Always test with `DRY_RUN = True`
   - Verify counts before actual deletion

5. **Process in Batches**
   - Start with 5-10 senders
   - Verify results before continuing

6. **Monitor Progress**
   - Watch terminal output
   - Check for errors

### After Running

7. **Verify in Yahoo**
   - Log in to Yahoo Mail web interface
   - Check that emails are gone
   - Confirm quota space freed

8. **Keep the Script**
   - Run monthly to prevent future buildup
   - Update CSV as new newsletters arrive

---

## Troubleshooting

### Common Issues

**"Authentication failed"**
- Solution: Use App Password, not regular password
- Generate new one from Yahoo Account Security

**"Connection timeout"**
- Solution: Check firewall/antivirus blocking port 993
- Try different network

**"Too many messages"**
- Solution: Script already handles chunking
- If still issues, reduce chunk size to 50

**Script runs but no space freed**
- Yahoo may need time to process deletions
- Wait 1-2 hours and check again
- Ensure emails are in INBOX (not Archive)

---

## Ongoing Maintenance

### Monthly Cleanup Routine

1. Update CSV with new unwanted senders
2. Run script in dry-run mode
3. Review counts
4. Execute actual deletion

### Preventing Future Buildup

1. **Unsubscribe** from newsletters you delete
   - Script could be modified to save unsubscribe links first
   
2. **Use Filters**
   - Create Yahoo filters to auto-delete or auto-archive
   
3. **Regular Schedule**
   - Set calendar reminder for monthly cleanup
   - Or schedule script with cron/Task Scheduler

---

## Time & Effort Estimate

| Task | Time Estimate |
|------|--------------|
| Setup (install library, get app password) | 15 minutes |
| Create initial sender CSV | 30 minutes |
| Write basic script | 15 minutes |
| Testing and dry runs | 15 minutes |
| Full execution | 10-30 minutes* |
| **Total first time** | **~90 minutes** |
| **Subsequent runs** | **~10 minutes** |

*Depends on number of emails

---

## Cost Analysis

| Approach | Cost | Time Investment |
|----------|------|----------------|
| **IMAP Script (Recommended)** | Free | 90 min setup, 10 min/month |
| Manual deletion (Yahoo web) | Free | 5-10 hours |
| Clean Email service | $10-20/month | 30 min setup |
| Unroll.me | Free (sells data) | 15 min setup |

**ROI:** Script pays for itself after first use.

---

## Summary & Next Steps

### Why This Approach Wins

✅ **Fast** - Processes thousands of emails in minutes  
✅ **Safe** - Dry run mode prevents mistakes  
✅ **Private** - No third parties reading your email  
✅ **Free** - Only your time investment  
✅ **Reusable** - Run monthly to maintain clean inbox  
✅ **Educational** - Learn IMAP and Python scripting  

### Your Action Plan

1. ⬜ Install `imap-tools`: `pip install imap-tools`
2. ⬜ Generate Yahoo App Password
3. ⬜ Create `senders_to_delete.csv` with top 5-10 newsletters
4. ⬜ Copy basic script to `cleanup_yahoo.py`
5. ⬜ Run in dry-run mode and verify counts
6. ⬜ Set `DRY_RUN = False` and execute for real
7. ⬜ Check Yahoo Mail to confirm deletion
8. ⬜ Add more senders and repeat

---

## Additional Resources

- **imap_tools documentation**: https://github.com/ikvk/imap_tools
- **Yahoo IMAP settings**: imap.mail.yahoo.com:993 (SSL/TLS)
- **Yahoo App Passwords**: Yahoo Account → Security → Generate app password

---

**Good luck with your email cleanup! Your instinct to use IMAP was spot-on. This approach gives you maximum control while being fast and efficient.** 🚀