#!/usr/bin/env python3
"""
Generate Carousel Script from Sent Emails
Transforms email content into carousel-ready scripts for Gamma/Canva
"""

import os
import sys
import requests
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('carousel_generation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
EMAILS_DATABASE_ID = os.environ.get('EMAILS_DATABASE_ID', 'c2a53e49-4500-48c0-8344-dfcc6066b89f')

# API Headers
NOTION_HEADERS = {
    'Authorization': f'Bearer {NOTION_TOKEN}',
    'Content-Type': 'application/json',
    'Notion-Version': '2022-06-28'
}


def query_emails_for_carousel() -> List[Dict]:
    """Query Notion for recently sent emails that need carousel scripts"""
    url = f'https://api.notion.com/v1/databases/{EMAILS_DATABASE_ID}/query'

    payload = {
        "filter": {
            "and": [
                {
                    "property": "E-mail Status",
                    "select": {
                        "equals": "Scheduled & Sent"
                    }
                },
                {
                    "property": "Kit Broadcast ID",
                    "rich_text": {
                        "is_not_empty": True
                    }
                }
            ]
        },
        "sorts": [
            {
                "property": "Sent Date",
                "direction": "descending"
            }
        ],
        "page_size": 10  # Process last 10 sent emails
    }

    try:
        response = requests.post(url, headers=NOTION_HEADERS, json=payload)
        response.raise_for_status()
        results = response.json().get('results', [])
        logger.info(f"Found {len(results)} sent emails to process for carousel scripts")
        return results
    except requests.exceptions.RequestException as e:
        logger.error(f"Error querying Notion: {e}")
        return []


def get_page_content(page_id: str) -> str:
    """Retrieve the full content of a Notion page (email body)"""
    url = f'https://api.notion.com/v1/blocks/{page_id}/children'

    try:
        response = requests.get(url, headers=NOTION_HEADERS)
        response.raise_for_status()
        blocks = response.json().get('results', [])

        # Extract text content from blocks
        content_parts = []
        for block in blocks:
            block_type = block.get('type')

            if block_type == 'paragraph':
                rich_text = block['paragraph'].get('rich_text', [])
                text = ''.join([rt.get('plain_text', '') for rt in rich_text])
                if text:
                    content_parts.append(text)

            elif block_type in ['heading_1', 'heading_2', 'heading_3']:
                rich_text = block[block_type].get('rich_text', [])
                text = ''.join([rt.get('plain_text', '') for rt in rich_text])
                if text:
                    content_parts.append(f"## {text}")

            elif block_type == 'bulleted_list_item':
                rich_text = block['bulleted_list_item'].get('rich_text', [])
                text = ''.join([rt.get('plain_text', '') for rt in rich_text])
                if text:
                    content_parts.append(f"• {text}")

            elif block_type == 'numbered_list_item':
                rich_text = block['numbered_list_item'].get('rich_text', [])
                text = ''.join([rt.get('plain_text', '') for rt in rich_text])
                if text:
                    content_parts.append(f"- {text}")

        full_content = '\n\n'.join(content_parts)
        logger.info(f"Extracted {len(full_content)} characters from page {page_id}")
        return full_content

    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting page content: {e}")
        return ""


def extract_property_value(properties: Dict, prop_name: str, prop_type: str) -> any:
    """Extract value from Notion property"""
    prop = properties.get(prop_name, {})

    if prop_type == 'title':
        title_array = prop.get('title', [])
        return title_array[0].get('plain_text', '') if title_array else ''

    elif prop_type == 'rich_text':
        text_array = prop.get('rich_text', [])
        return text_array[0].get('plain_text', '') if text_array else ''

    elif prop_type == 'date':
        date_obj = prop.get('date')
        return date_obj.get('start') if date_obj else None

    return None


def create_carousel_script_template(email_title: str, email_content: str) -> str:
    """
    Create a carousel script template from email content
    This is a simple template - you can enhance with your Claude Skill
    """

    script = f"""# CAROUSEL SCRIPT: {email_title}

## SLIDE 1: HOOK
[Create an attention-grabbing opening based on email subject line]
Title: {email_title}

## SLIDES 2-8: MAIN CONTENT
[Transform key points from email into visual slides]

Email content to transform:
---
{email_content[:1000]}...
---

## SLIDE 9: CALL TO ACTION
Title: "Want More Insights Like This?"
Content:
• Join 800+ subscribers
• Get weekly emails with actionable strategies
• Unsubscribe anytime

Button: "Subscribe to Newsletter"
Link: [YOUR NEWSLETTER LINK]

## SLIDE 10: CLOSING
"Follow for more content like this"
[YOUR HANDLE/BRANDING]

---
NOTES FOR GAMMA TEMPLATE:
1. Use 4x5 ratio for Instagram/LinkedIn
2. Keep text concise (max 50 words per slide)
3. Add your brand colors
4. Include visuals for each key point
5. End with clear newsletter CTA
"""

    return script


def update_notion_with_carousel_script(page_id: str, carousel_script: str) -> bool:
    """Add carousel script as a comment on the email page"""
    url = 'https://api.notion.com/v1/comments'

    payload = {
        "parent": {
            "page_id": page_id
        },
        "rich_text": [
            {
                "text": {
                    "content": f"📊 CAROUSEL SCRIPT\n\n{carousel_script[:1900]}"  # Max ~2000 chars
                }
            }
        ]
    }

    try:
        response = requests.post(url, headers=NOTION_HEADERS, json=payload)
        response.raise_for_status()
        logger.info(f"✅ Added carousel script as comment to page {page_id}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Error adding comment: {e}")
        return False


def process_email_for_carousel(email_page: Dict) -> bool:
    """Generate carousel script for a single email"""
    page_id = email_page.get('id')
    properties = email_page.get('properties', {})

    # Extract email details
    email_title = extract_property_value(properties, 'Name', 'title')
    broadcast_id = extract_property_value(properties, 'Kit Broadcast ID', 'rich_text')

    logger.info(f"Processing: {email_title}")

    # Get email content
    email_content = get_page_content(page_id)

    if not email_content:
        logger.warning(f"No content found for email: {email_title}")
        return False

    # Generate carousel script
    carousel_script = create_carousel_script_template(email_title, email_content)

    # Add script as Notion comment
    success = update_notion_with_carousel_script(page_id, carousel_script)

    if success:
        logger.info(f"✅ Carousel script generated for: {email_title}")
    else:
        logger.error(f"❌ Failed to save carousel script for: {email_title}")

    return success


def main():
    """Main execution function"""
    logger.info("=" * 50)
    logger.info("Starting Carousel Script Generation")
    logger.info("=" * 50)

    # Validate environment variables
    if not NOTION_TOKEN:
        logger.error("Missing NOTION_TOKEN environment variable")
        sys.exit(1)

    # Query emails that need carousel scripts
    sent_emails = query_emails_for_carousel()

    if not sent_emails:
        logger.info("No sent emails to process")
        return

    # Process each email
    success_count = 0
    failure_count = 0

    for email in sent_emails[:3]:  # Process last 3 emails for now
        try:
            if process_email_for_carousel(email):
                success_count += 1
            else:
                failure_count += 1
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            failure_count += 1

    # Summary
    logger.info("=" * 50)
    logger.info(f"Carousel Script Generation Complete!")
    logger.info(f"  ✅ Successful: {success_count}")
    logger.info(f"  ❌ Failed: {failure_count}")
    logger.info("=" * 50)
    logger.info("📋 Next steps:")
    logger.info("1. Check Notion comments for carousel scripts")
    logger.info("2. Copy script into your Claude Skill for refinement")
    logger.info("3. Paste refined script into Gamma template")
    logger.info("4. Add newsletter CTA and generate!")


if __name__ == "__main__":
    main()
