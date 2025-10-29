#!/usr/bin/env python3
"""
Notion to Kit Email Automation
Sends emails from Notion database to Kit (ConvertKit) with Cloudinary image hosting
"""

import os
import sys
import json
import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_sender.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
KIT_API_KEY = os.environ.get('KIT_API_KEY')
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')
EMAILS_DATABASE_ID = os.environ.get('EMAILS_DATABASE_ID', 'c2a53e49-4500-48c0-8344-dfcc6066b89f')
TEST_MODE = os.environ.get('TEST_MODE', 'false').lower() == 'true'
TEST_EMAIL = os.environ.get('TEST_EMAIL', '')

# API Headers
NOTION_HEADERS = {
    'Authorization': f'Bearer {NOTION_TOKEN}',
    'Content-Type': 'application/json',
    'Notion-Version': '2022-06-28'
}

KIT_HEADERS = {
    'X-Kit-Api-Key': KIT_API_KEY,
    'Content-Type': 'application/json'
}


def query_ready_emails() -> List[Dict]:
    """Query Notion for emails with status 'Ready to Send'"""
    url = f'https://api.notion.com/v1/databases/{EMAILS_DATABASE_ID}/query'

    payload = {
        "filter": {
            "property": "E-mail Status",
            "select": {
                "equals": "Ready to Send"
            }
        }
    }

    try:
        response = requests.post(url, headers=NOTION_HEADERS, json=payload)
        response.raise_for_status()
        results = response.json().get('results', [])
        logger.info(f"Found {len(results)} emails ready to send")
        return results
    except requests.exceptions.RequestException as e:
        logger.error(f"Error querying Notion: {e}")
        return []


def get_page_content(page_id: str) -> List[Dict]:
    """Get all content blocks from a Notion page"""
    url = f'https://api.notion.com/v1/blocks/{page_id}/children'
    blocks = []

    try:
        has_more = True
        start_cursor = None

        while has_more:
            params = {'start_cursor': start_cursor} if start_cursor else {}
            response = requests.get(url, headers=NOTION_HEADERS, params=params)
            response.raise_for_status()
            data = response.json()

            blocks.extend(data.get('results', []))
            has_more = data.get('has_more', False)
            start_cursor = data.get('next_cursor')

        logger.info(f"Retrieved {len(blocks)} content blocks from page {page_id}")
        return blocks
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting page content: {e}")
        return []


def upload_to_cloudinary(image_url: str, public_id: str) -> Optional[str]:
    """Upload image to Cloudinary and return permanent URL"""
    import cloudinary
    import cloudinary.uploader

    # Configure Cloudinary
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET
    )

    try:
        result = cloudinary.uploader.upload(
            image_url,
            public_id=public_id,
            folder="notion-emails"
        )
        cloudinary_url = result.get('secure_url')
        logger.info(f"Uploaded image to Cloudinary: {cloudinary_url}")
        return cloudinary_url
    except Exception as e:
        logger.error(f"Error uploading to Cloudinary: {e}")
        return None


def block_to_html(block: Dict, image_counter: Dict) -> str:
    """Convert a Notion block to HTML"""
    block_type = block.get('type')

    if block_type == 'paragraph':
        rich_text = block['paragraph'].get('rich_text', [])
        html = rich_text_to_html(rich_text)
        return f'<p>{html}</p>' if html else ''

    elif block_type == 'heading_1':
        rich_text = block['heading_1'].get('rich_text', [])
        html = rich_text_to_html(rich_text)
        return f'<h1>{html}</h1>' if html else ''

    elif block_type == 'heading_2':
        rich_text = block['heading_2'].get('rich_text', [])
        html = rich_text_to_html(rich_text)
        return f'<h2>{html}</h2>' if html else ''

    elif block_type == 'heading_3':
        rich_text = block['heading_3'].get('rich_text', [])
        html = rich_text_to_html(rich_text)
        return f'<h3>{html}</h3>' if html else ''

    elif block_type == 'bulleted_list_item':
        rich_text = block['bulleted_list_item'].get('rich_text', [])
        html = rich_text_to_html(rich_text)
        return f'<li>{html}</li>' if html else ''

    elif block_type == 'numbered_list_item':
        rich_text = block['numbered_list_item'].get('rich_text', [])
        html = rich_text_to_html(rich_text)
        return f'<li>{html}</li>' if html else ''

    elif block_type == 'image':
        image_data = block['image']
        image_url = None

        # Get image URL (Notion hosted or external)
        if image_data.get('type') == 'file':
            image_url = image_data['file'].get('url')
        elif image_data.get('type') == 'external':
            image_url = image_data['external'].get('url')

        if image_url:
            # Upload to Cloudinary for permanent hosting
            image_counter['count'] += 1
            public_id = f"email_{image_counter['email_id']}_{image_counter['count']}"
            cloudinary_url = upload_to_cloudinary(image_url, public_id)

            if cloudinary_url:
                return f'<p><img src="{cloudinary_url}" alt="Email image" style="max-width: 100%; height: auto;"></p>'

        return ''

    elif block_type == 'divider':
        return '<hr>'

    elif block_type == 'quote':
        rich_text = block['quote'].get('rich_text', [])
        html = rich_text_to_html(rich_text)
        return f'<blockquote>{html}</blockquote>' if html else ''

    else:
        # Unsupported block type
        return ''


def rich_text_to_html(rich_text_array: List[Dict]) -> str:
    """Convert Notion rich text array to HTML"""
    html = ''

    for text_obj in rich_text_array:
        content = text_obj.get('plain_text', '')
        annotations = text_obj.get('annotations', {})
        href = text_obj.get('href')

        # Apply formatting
        if annotations.get('bold'):
            content = f'<strong>{content}</strong>'
        if annotations.get('italic'):
            content = f'<em>{content}</em>'
        if annotations.get('strikethrough'):
            content = f'<s>{content}</s>'
        if annotations.get('underline'):
            content = f'<u>{content}</u>'
        if annotations.get('code'):
            content = f'<code>{content}</code>'

        # Add link
        if href:
            content = f'<a href="{href}">{content}</a>'

        html += content

    return html


def blocks_to_html(blocks: List[Dict], email_id: str) -> str:
    """Convert Notion blocks to HTML email body"""
    html_parts = []
    image_counter = {'count': 0, 'email_id': email_id}

    in_bullet_list = False
    in_numbered_list = False

    for block in blocks:
        block_type = block.get('type')

        # Handle list transitions
        if block_type == 'bulleted_list_item':
            if not in_bullet_list:
                html_parts.append('<ul>')
                in_bullet_list = True
            if in_numbered_list:
                html_parts.append('</ol>')
                in_numbered_list = False
        elif block_type == 'numbered_list_item':
            if not in_numbered_list:
                html_parts.append('<ol>')
                in_numbered_list = True
            if in_bullet_list:
                html_parts.append('</ul>')
                in_bullet_list = False
        else:
            # Close any open lists
            if in_bullet_list:
                html_parts.append('</ul>')
                in_bullet_list = False
            if in_numbered_list:
                html_parts.append('</ol>')
                in_numbered_list = False

        # Convert block to HTML
        block_html = block_to_html(block, image_counter)
        if block_html:
            html_parts.append(block_html)

    # Close any remaining open lists
    if in_bullet_list:
        html_parts.append('</ul>')
    if in_numbered_list:
        html_parts.append('</ol>')

    return '\n'.join(html_parts)


def get_kit_tag_id(tag_name: str) -> Optional[int]:
    """Get Kit tag ID by tag name"""
    url = 'https://api.kit.com/v4/tags'

    try:
        response = requests.get(url, headers=KIT_HEADERS)
        response.raise_for_status()
        data = response.json()

        tags = data.get('tags', [])
        for tag in tags:
            if tag.get('name', '').lower() == tag_name.lower():
                tag_id = tag.get('id')
                logger.info(f"Found Kit tag: {tag_name} (ID: {tag_id})")
                return tag_id

        logger.warning(f"No Kit tag found with name: {tag_name}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting Kit tags: {e}")
        return None


def get_kit_segment_id(segment_name: str) -> Optional[int]:
    """Get Kit segment ID by segment name"""
    url = 'https://api.kit.com/v4/segments'

    try:
        response = requests.get(url, headers=KIT_HEADERS)
        response.raise_for_status()
        data = response.json()

        segments = data.get('segments', [])
        for segment in segments:
            if segment.get('name', '').lower() == segment_name.lower():
                segment_id = segment.get('id')
                logger.info(f"Found Kit segment: {segment_name} (ID: {segment_id})")
                return segment_id

        logger.warning(f"No Kit segment found with name: {segment_name}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting Kit segments: {e}")
        return None


def create_kit_broadcast(subject: str, preview_text: str, html_body: str,
                        publish_date: Optional[str], segments: List[str]) -> Optional[str]:
    """Create a Kit broadcast and return broadcast ID

    Segments mapping:
    - TEST_MODE=true → Override all settings and send only to TEST_EMAIL
    - Empty or "Everyone" → Send to ALL subscribers
    - Any other segment name → Send to Kit tag/segment with that name
    """
    url = 'https://api.kit.com/v4/broadcasts'

    # Determine recipient settings based on segments
    recipient_settings = {}

    # SAFETY MODE: If TEST_MODE is enabled, send only to TEST_EMAIL
    if TEST_MODE:
        if not TEST_EMAIL:
            logger.error("❌ TEST_MODE enabled but TEST_EMAIL not set - cannot send")
            return None

        logger.warning("🔒 TEST MODE ACTIVE - Sending only to: " + TEST_EMAIL)
        recipient_settings = {
            "subscriber_filter": {
                "filter": "email",
                "match": TEST_EMAIL
            }
        }
    elif not segments or "Everyone" in segments:
        # Send to all subscribers
        recipient_settings = {
            "send_to_all": True
        }
        logger.info("📧 Sending to: ALL subscribers")
    else:
        # Send to specific Kit tags/segments
        tag_ids = []
        segment_ids = []

        for segment_name in segments:
            # Try to find as a tag first
            tag_id = get_kit_tag_id(segment_name)
            if tag_id:
                tag_ids.append(tag_id)
            else:
                # Try to find as a segment
                segment_id = get_kit_segment_id(segment_name)
                if segment_id:
                    segment_ids.append(segment_id)
                else:
                    logger.warning(f"⚠️  Segment/Tag '{segment_name}' not found in Kit - skipping")

        if not tag_ids and not segment_ids:
            logger.error("❌ No valid Kit tags or segments found - cannot send")
            return None

        # Kit API supports sending to tags or segments
        if tag_ids:
            recipient_settings['tag_ids'] = tag_ids
            logger.info(f"📧 Sending to Kit tags: {tag_ids}")
        if segment_ids:
            recipient_settings['segment_ids'] = segment_ids
            logger.info(f"📧 Sending to Kit segments: {segment_ids}")

    payload = {
        "subject": subject,
        "preview_text": preview_text,
        "content": html_body,
        "public": False,
        "published": True if publish_date else False,
        "published_at": publish_date if publish_date else None,
        **recipient_settings
    }

    # Log the exact payload being sent to Kit
    logger.info(f"📤 Creating Kit broadcast with published_at: {publish_date}")
    if 'T' in (publish_date or ''):
        logger.info(f"   ⏰ Scheduled for SPECIFIC TIME: {publish_date}")
    else:
        logger.info(f"   📅 Scheduled for DATE ONLY: {publish_date}")
        logger.warning(f"   ⚠️  Kit may send immediately! Consider adding a time in Notion.")

    try:
        response = requests.post(url, headers=KIT_HEADERS, json=payload)
        response.raise_for_status()
        broadcast = response.json().get('broadcast', {})
        broadcast_id = str(broadcast.get('id'))
        logger.info(f"✅ Created Kit broadcast: {broadcast_id}")
        return broadcast_id
    except requests.exceptions.RequestException as e:
        logger.error(f"Error creating Kit broadcast: {e}")
        logger.error(f"Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
        return None


def update_notion_page(page_id: str, broadcast_id: str, sent_date: str) -> bool:
    """Update Notion page with broadcast info"""
    url = f'https://api.notion.com/v1/pages/{page_id}'

    payload = {
        "properties": {
            "E-mail Status": {
                "select": {
                    "name": "Scheduled & Sent"
                }
            },
            "Kit Broadcast ID": {
                "rich_text": [
                    {
                        "text": {
                            "content": broadcast_id
                        }
                    }
                ]
            },
            "Sent Date": {
                "date": {
                    "start": sent_date
                }
            }
        }
    }

    try:
        response = requests.patch(url, headers=NOTION_HEADERS, json=payload)
        response.raise_for_status()
        logger.info(f"Updated Notion page {page_id}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Error updating Notion page: {e}")
        return False


def extract_property_value(properties: Dict, prop_name: str, prop_type: str) -> any:
    """Extract value from Notion property"""
    prop = properties.get(prop_name, {})

    if prop_type == 'title':
        title_array = prop.get('title', [])
        return title_array[0].get('plain_text', '') if title_array else ''

    elif prop_type == 'rich_text':
        text_array = prop.get('rich_text', [])
        return text_array[0].get('plain_text', '') if text_array else ''

    elif prop_type == 'select':
        select_obj = prop.get('select')
        return select_obj.get('name', '') if select_obj else ''

    elif prop_type == 'multi_select':
        multi_select = prop.get('multi_select', [])
        return [item.get('name', '') for item in multi_select]

    elif prop_type == 'date':
        date_obj = prop.get('date')
        return date_obj.get('start') if date_obj else None

    return None


def process_email(email_page: Dict) -> bool:
    """Process a single email: convert to HTML and send via Kit"""
    page_id = email_page.get('id')
    properties = email_page.get('properties', {})

    # Extract properties
    name = extract_property_value(properties, 'Name', 'title')
    sl1 = extract_property_value(properties, 'SL1', 'rich_text')
    pre_text = extract_property_value(properties, 'Pre-Text', 'rich_text')
    publish_date = extract_property_value(properties, 'Publish Date', 'date')
    segments = extract_property_value(properties, 'Segments', 'multi_select')

    # Determine subject line: SL1 or Name
    subject = sl1 if sl1 else name

    if not subject:
        logger.error(f"Email {page_id} has no subject line (SL1 or Name)")
        return False

    if not publish_date:
        logger.error(f"Email {page_id} has no Publish Date")
        return False

    # SAFETY CHECK: Skip emails with past publish dates
    try:
        # Parse the publish date (format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
        if 'T' in publish_date:
            # DateTime with time component - use exact time
            publish_datetime = datetime.fromisoformat(publish_date.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)

            if publish_datetime < now:
                logger.warning(f"⏭️  SKIPPED: Email '{subject}' has past Publish Date ({publish_date})")
                logger.warning(f"    Current time: {now.isoformat()}")
                logger.warning(f"    To send this email, update its Publish Date to a future date")
                return False
        else:
            # Date-only format (YYYY-MM-DD) - use end of day UTC to be lenient
            # This gives the full 24-hour period regardless of user's timezone
            publish_datetime = datetime.fromisoformat(publish_date + 'T23:59:59+00:00')
            now = datetime.now(timezone.utc)

            if publish_datetime < now:
                logger.warning(f"⏭️  SKIPPED: Email '{subject}' has past Publish Date ({publish_date})")
                logger.warning(f"    Current date: {now.date().isoformat()}")
                logger.warning(f"    To send this email, update its Publish Date to a future date")
                return False

    except Exception as e:
        logger.error(f"Error parsing Publish Date '{publish_date}': {e}")
        return False

    logger.info(f"Processing email: {subject}")
    logger.info(f"  Publish Date: {publish_date}")
    logger.info(f"  Segments: {segments}")

    # Get page content blocks
    blocks = get_page_content(page_id)

    if not blocks:
        logger.error(f"Email {page_id} has no content")
        return False

    # Convert blocks to HTML
    html_body = blocks_to_html(blocks, page_id)

    # Use pre-text or first paragraph as preview
    if not pre_text:
        # Extract first paragraph as preview
        for block in blocks:
            if block.get('type') == 'paragraph':
                rich_text = block['paragraph'].get('rich_text', [])
                if rich_text:
                    pre_text = rich_text[0].get('plain_text', '')[:150]
                    break

    # Create Kit broadcast
    broadcast_id = create_kit_broadcast(
        subject=subject,
        preview_text=pre_text,
        html_body=html_body,
        publish_date=publish_date,
        segments=segments
    )

    if not broadcast_id:
        logger.error(f"Failed to create broadcast for email {page_id}")
        return False

    # Update Notion page
    sent_date = datetime.now().isoformat()
    success = update_notion_page(page_id, broadcast_id, sent_date)

    if success:
        logger.info(f"✅ Successfully processed email: {subject}")
    else:
        logger.warning(f"⚠️ Email sent but failed to update Notion for: {subject}")

    return success


def main():
    """Main execution function"""
    logger.info("=" * 50)
    logger.info("Starting Notion to Kit Email Automation")
    logger.info("=" * 50)

    # Show test mode status
    if TEST_MODE:
        logger.warning("🔒 TEST MODE ENABLED - All emails will be sent ONLY to: " + TEST_EMAIL)
        logger.warning("    Set TEST_MODE=false to disable test mode")
    else:
        logger.info("📧 PRODUCTION MODE - Emails will be sent to configured segments")

    # Validate environment variables
    required_vars = [
        'NOTION_TOKEN', 'KIT_API_KEY',
        'CLOUDINARY_CLOUD_NAME', 'CLOUDINARY_API_KEY', 'CLOUDINARY_API_SECRET'
    ]

    missing_vars = [var for var in required_vars if not os.environ.get(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)

    # Query ready emails
    ready_emails = query_ready_emails()

    if not ready_emails:
        logger.info("No emails ready to send")
        return

    # Process each email
    success_count = 0
    failure_count = 0

    for email in ready_emails:
        try:
            if process_email(email):
                success_count += 1
            else:
                failure_count += 1
        except Exception as e:
            logger.error(f"Unexpected error processing email: {e}")
            failure_count += 1

    # Summary
    logger.info("=" * 50)
    logger.info(f"Processing Complete!")
    logger.info(f"  ✅ Successful: {success_count}")
    logger.info(f"  ❌ Failed: {failure_count}")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
