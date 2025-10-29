# Notion to Kit Email Automation

Automatically send emails from your Notion database to Kit (ConvertKit) with image hosting via Cloudinary, and sync performance stats back to Notion.

## Features

✅ **Send Emails** - Notion → Kit with scheduled publishing
✅ **Image Hosting** - Auto-upload images to Cloudinary for permanent URLs
✅ **Performance Tracking** - Sync Open Rate, Click Rate, Recipients back to Notion
✅ **Test Mode** - Send test emails to yourself before going live
✅ **Manual + Automatic** - Trigger manually or run daily automatically
✅ **Rich Formatting** - Supports bold, italic, links, lists, headings, images

---

## Prerequisites

1. **Notion Account** - With Integration access
2. **Kit (ConvertKit) Account** - With API access
3. **Cloudinary Account** - Free tier is sufficient
4. **GitHub Account** - For running automations

---

## Setup Instructions

### Step 1: Notion Setup

1. **Duplicate the E-mails Database Template** (or use existing database)

2. **Required Properties:**
   - Name (Title) - Email title/internal reference
   - SL1 (Rich Text) - Subject line (primary)
   - Pre-Text (Rich Text) - Email preview text
   - E-mail Status (Select) - Options: Draft, Ready to Send, Scheduled & Sent, Reviewed
   - Publish Date (Date) - When to send the email
   - Segments (Multi-select) - Options: Test, Everyone
   - Kit Broadcast ID (Rich Text) - Auto-filled after sending
   - Sent Date (Date) - Auto-filled after sending
   - Open Rate (Number) - Auto-synced from Kit
   - Click Rate (Number) - Auto-synced from Kit
   - Recipients (Number) - Auto-synced from Kit
   - Total Opens (Number) - Auto-synced from Kit
   - Total Clicks (Number) - Auto-synced from Kit

3. **Create Notion Integration:**
   - Go to https://www.notion.so/my-integrations
   - Click "New Integration"
   - Name it "Email Automation"
   - Copy the "Internal Integration Token" (save for later)

4. **Connect Integration to Database:**
   - Open your E-mails database
   - Click "..." menu → Connections
   - Add your "Email Automation" integration

5. **Get Database ID:**
   - Open database in browser
   - Copy ID from URL: `notion.so/WORKSPACE/DATABASE_ID?v=VIEW_ID`
   - Example: `c2a53e49-4500-48c0-8344-dfcc6066b89f`

---

### Step 2: Kit (ConvertKit) Setup

1. **Get API Key:**
   - Go to https://app.kit.com/account_settings/advanced_settings
   - Scroll to "API Key"
   - Copy your API Key (save for later)

2. **Get Test Email Subscriber ID:**
   - Make sure your personal email is subscribed to your Kit account
   - We'll use this for "Test" segment sends

---

### Step 3: Cloudinary Setup

1. **Create Free Account:**
   - Go to https://cloudinary.com/users/register_free
   - Sign up (free tier: 25GB storage, 25GB bandwidth/month)

2. **Get Credentials:**
   - Go to Dashboard after signup
   - Copy these 3 values (save for later):
     - **Cloud Name**
     - **API Key**
     - **API Secret**

---

### Step 4: GitHub Setup

1. **Fork or Upload Repository:**
   - Upload these files to your GitHub repository:
     - `send_emails_notion_to_kit.py`
     - `sync_email_stats_kit_to_notion.py`
     - `requirements.txt`
     - `.github/workflows/send-emails.yml`
     - `.github/workflows/sync-email-stats.yml`

2. **Add GitHub Secrets:**
   - Go to your GitHub repository
   - Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Add these secrets:

   | Secret Name | Value | Where to Get It |
   |-------------|-------|-----------------|
   | `NOTION_TOKEN` | Your Notion Integration Token | Step 1.3 |
   | `KIT_API_KEY` | Your Kit API Key | Step 2.1 |
   | `CLOUDINARY_CLOUD_NAME` | Your Cloudinary Cloud Name | Step 3.2 |
   | `CLOUDINARY_API_KEY` | Your Cloudinary API Key | Step 3.2 |
   | `CLOUDINARY_API_SECRET` | Your Cloudinary API Secret | Step 3.2 |
   | `EMAILS_DATABASE_ID` | Your Notion Database ID | Step 1.5 |
   | `TEST_EMAIL` | Your test email address | Your personal email subscribed to Kit |

---

## How to Use

### Send an Email

1. **Write Email in Notion:**
   - Create new page in E-mails database
   - Fill in:
     - Name: "Day 1 - Welcome Email" (internal reference)
     - SL1: "Welcome to the journey!" (actual subject line)
     - Pre-Text: "Here's what to expect..." (preview text)
     - Publish Date: Set date/time when email should be sent
     - Segments: Select "Test" (for testing) or "Everyone" (for all subscribers)
     - Write email content in page body (supports images, formatting, lists, etc.)

2. **Mark Ready to Send:**
   - Change E-mail Status → "Ready to Send"

3. **Send Email:**

   **Option A: Manual Trigger**
   - Go to GitHub repository → Actions tab
   - Click "Send Emails from Notion to Kit"
   - Click "Run workflow" button
   - Click "Run workflow" again to confirm

   **Option B: Automatic (Daily at 8 AM UTC)**
   - Just wait! Automation runs daily automatically
   - Any emails with "Ready to Send" status will be scheduled

4. **Check Results:**
   - Email status changes to "Scheduled & Sent"
   - Kit Broadcast ID is filled in
   - Sent Date is recorded
   - Email is scheduled in Kit for your Publish Date

---

### Test Before Sending to Everyone

**Always test first!**

1. Set Segments = "Test"
2. Set Status = "Ready to Send"
3. Trigger workflow
4. Check your test email inbox
5. Once verified, duplicate email, set Segments = "Everyone", send again

---

### View Email Stats

**Stats sync automatically daily at 9 AM UTC**, or trigger manually:

1. Go to GitHub → Actions → "Sync Email Stats from Kit to Notion"
2. Click "Run workflow"
3. Check Notion - Open Rate, Click Rate, Recipients, Total Opens, Total Clicks updated!

---

## Automation Schedule

| Workflow | Schedule | Purpose |
|----------|----------|---------|
| Send Emails | Daily 8:00 AM UTC | Checks for "Ready to Send" emails and schedules them in Kit |
| Sync Stats | Daily 9:00 AM UTC | Updates email performance metrics from Kit to Notion |

**Both workflows** also have manual trigger buttons for on-demand execution.

---

## Troubleshooting

### Email Not Sending

**Check:**
- ✅ E-mail Status = "Ready to Send" (not Draft!)
- ✅ Publish Date is set
- ✅ SL1 or Name is filled (subject line)
- ✅ Email has content blocks
- ✅ GitHub Secrets are configured correctly

**View Logs:**
- GitHub → Actions → Click on workflow run → View logs
- Download artifact "email-sender-logs" for detailed logs

---

### Stats Not Syncing

**Check:**
- ✅ Email has Kit Broadcast ID (was sent successfully)
- ✅ Broadcast ID is valid in Kit dashboard
- ✅ GitHub Secrets for NOTION_TOKEN and KIT_API_KEY are correct

**Note:** Stats may take a few hours to populate in Kit after sending.

---

### Images Not Showing

**Check:**
- ✅ Cloudinary credentials are correct
- ✅ Images in Notion are uploaded (not external links that expired)
- ✅ Check email_sender.log for Cloudinary upload errors

---

## Architecture

```
┌─────────────┐
│   Notion    │
│  Database   │
│             │
│ Status:     │
│ Ready to    │
│ Send        │
└──────┬──────┘
       │
       │ 1. Query Ready Emails
       │
       ▼
┌─────────────────────────────┐
│  GitHub Actions             │
│  send_emails_notion_to_kit  │
│                             │
│  • Read email content       │
│  • Download images          │
│  • Upload to Cloudinary ─────────► Cloudinary
│  • Convert to HTML          │      (Permanent Image URLs)
│  • Schedule in Kit ──────────────► Kit (ConvertKit)
│  • Update Notion            │      (Create Broadcast)
└──────┬──────────────────────┘
       │
       │ 2. Update Status
       ▼
┌─────────────┐
│   Notion    │
│  Database   │
│             │
│ Status:     │
│ Scheduled & │
│ Sent        │
│             │
│ Kit ID: 123 │
└──────▲──────┘
       │
       │ 3. Sync Stats
       │
┌─────────────────────────────┐
│  GitHub Actions             │
│  sync_email_stats_kit_to... │
│                             │
│  • Query sent emails        │
│  • Get stats from Kit ◄──────────── Kit API
│  • Update Notion metrics    │       (Broadcast Stats)
└─────────────────────────────┘
```

---

## Files Overview

| File | Purpose |
|------|---------|
| `send_emails_notion_to_kit.py` | Main script: Notion → Kit email sending |
| `sync_email_stats_kit_to_notion.py` | Stats sync: Kit → Notion metrics |
| `requirements.txt` | Python dependencies |
| `.github/workflows/send-emails.yml` | GitHub Actions workflow for sending |
| `.github/workflows/sync-email-stats.yml` | GitHub Actions workflow for stats |

---

## Subject Line Logic

**Priority:**
1. Use **SL1** if filled
2. Fall back to **Name** if SL1 is empty
3. **SL2** is ignored (keep for your notes/future use)

**Example:**
- Name: "Day 3 - Productivity Tips"
- SL1: "The Secret to 10x Productivity"
- Email sends with subject: **"The Secret to 10x Productivity"**

---

## Segments Logic

| Segment | Behavior |
|---------|----------|
| **Test** | Sends only to TEST_EMAIL address |
| **Everyone** (or empty) | Sends to all subscribers |

---

## Cost

**100% FREE for moderate usage:**
- GitHub Actions: 2,000 minutes/month free
- Cloudinary: 25GB storage + 25GB bandwidth/month free
- Kit: Depends on your plan (API is included)
- Notion: Your existing plan

**This automation uses ~2 minutes/day = 60 minutes/month (well under free tier!)**

---

## Client Deployment

To set this up for a client:

1. **Share this README** with them
2. **They need to:**
   - Create their Notion database (or use template)
   - Get their own API keys (Notion, Kit, Cloudinary)
   - Fork your GitHub repo (or create their own)
   - Add GitHub Secrets
   - Done!

**Total setup time: 15-20 minutes**

---

## Support

If you encounter issues:
1. Check troubleshooting section above
2. Review GitHub Actions logs
3. Verify all secrets are configured correctly
4. Ensure Notion database has all required properties

---

## Future Enhancements

Possible additions (not implemented yet):
- UTM tracking for revenue attribution
- A/B testing with SL2
- Segment-based sending (beyond Test/Everyone)
- Email templates/styles
- Scheduling queue dashboard

---

Built with ❤️ using Notion API, Kit API, Cloudinary, and GitHub Actions
