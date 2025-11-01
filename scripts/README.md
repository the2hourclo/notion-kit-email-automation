# Scripts Organization

This folder contains all automation scripts organized by functionality.

## 📁 Folder Structure

```
scripts/
├── email_automation/          # Notion → Kit email automation
│   ├── send_emails_notion_to_kit.py
│   └── sync_email_stats_kit_to_notion.py
│
├── carousel_automation/       # Email → Carousel generation (future)
│   └── generate_carousel_script.py
│
├── tests/                     # Test scripts
│   ├── test_gamma_preserve.py
│   └── test_pdf_to_images.py
│
└── utils/                     # Shared utilities (future)
```

---

## 🔄 Email Automation

### **send_emails_notion_to_kit.py**
Sends emails from Notion to Kit (ConvertKit)

**Triggered by:** `.github/workflows/send-emails.yml`
**Schedule:** Every 30 minutes
**What it does:**
- Queries Notion for "Ready to Send" emails
- Converts Notion content to HTML
- Uploads images to Cloudinary
- Creates broadcasts in Kit
- Updates Notion with broadcast IDs
- Handles segment targeting

### **sync_email_stats_kit_to_notion.py**
Syncs email performance stats from Kit back to Notion

**Triggered by:** `.github/workflows/sync-email-stats.yml`
**Schedule:** Every hour
**What it does:**
- Queries sent emails from Notion
- Fetches stats from Kit API
- Calculates CTOR (excludes system links)
- Updates Notion with metrics:
  - Recipients
  - Total Opens
  - Total Clicks (content only)
  - Open Rate
  - Click to Open Rate

---

## 🎨 Carousel Automation (Future)

### **generate_carousel_script.py**
Generates carousel scripts from sent emails

**Status:** Ready for integration
**What it does:**
- Extracts content from sent emails
- Transforms into carousel format
- Saves script to Notion comments

---

## 🧪 Tests

### **test_gamma_preserve.py**
Tests Gamma API carousel generation with pre-written content

**Usage:**
```bash
export GAMMA_API_KEY=sk-gamma-xxxxx
python scripts/tests/test_gamma_preserve.py
```

### **test_pdf_to_images.py**
Tests PDF to PNG conversion for social media carousels

**Usage:**
```bash
# Place test_carousel.pdf in notion-kit-email-automation folder
python scripts/tests/test_pdf_to_images.py
```

**Requirements:**
- `pdf2image` package
- `poppler` (system dependency)

---

## 🔧 Utils (Future)

Shared utility functions will go here:
- Image processing
- API helpers
- Notion utilities
- Common validators

---

## 🚀 Running Scripts Locally

### Email Automation
```bash
# Set environment variables
export NOTION_TOKEN=secret_xxx
export KIT_API_KEY=xxx
export CLOUDINARY_CLOUD_NAME=xxx
export CLOUDINARY_API_KEY=xxx
export CLOUDINARY_API_SECRET=xxx
export EMAILS_DATABASE_ID=xxx

# Run email sender
python scripts/email_automation/send_emails_notion_to_kit.py

# Run stats sync
python scripts/email_automation/sync_email_stats_kit_to_notion.py
```

### Tests
```bash
# Test Gamma API
export GAMMA_API_KEY=sk-gamma-xxxxx
python scripts/tests/test_gamma_preserve.py

# Test PDF conversion
python scripts/tests/test_pdf_to_images.py
```

---

## 📊 GitHub Actions Integration

All production scripts are triggered by GitHub Actions workflows in `.github/workflows/`:

- **send-emails.yml** → Runs `email_automation/send_emails_notion_to_kit.py`
- **sync-email-stats.yml** → Runs `email_automation/sync_email_stats_kit_to_notion.py`

Logs are automatically uploaded as artifacts and retained for 30 days.

---

## 🔒 Environment Variables Required

**Email Automation:**
- `NOTION_TOKEN` - Notion integration token
- `KIT_API_KEY` - ConvertKit API key
- `CLOUDINARY_CLOUD_NAME` - Cloudinary cloud name
- `CLOUDINARY_API_KEY` - Cloudinary API key
- `CLOUDINARY_API_SECRET` - Cloudinary API secret
- `EMAILS_DATABASE_ID` - Notion database ID

**Carousel Automation (future):**
- `GAMMA_API_KEY` - Gamma Pro API key

---

## 📝 Adding New Scripts

When adding new scripts:

1. **Place in appropriate folder:**
   - Email-related → `email_automation/`
   - Carousel-related → `carousel_automation/`
   - Test scripts → `tests/`
   - Shared utilities → `utils/`

2. **Update this README** with script description

3. **Update GitHub Actions** if script needs automation

4. **Follow naming convention:** `verb_noun.py`
   - ✅ `send_emails_notion_to_kit.py`
   - ✅ `sync_email_stats_kit_to_notion.py`
   - ✅ `generate_carousel_script.py`

---

## 🎯 Current Status

### ✅ Production (Working)
- Email sending automation
- Stats sync automation
- Segment targeting
- CTOR tracking

### 🚧 In Development
- Carousel generation
- PDF → PNG conversion
- Social media scheduling

### 📋 Planned
- Shared utility library
- More comprehensive tests
- Error monitoring
- Performance analytics
