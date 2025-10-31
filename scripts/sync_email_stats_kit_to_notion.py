#!/usr/bin/env python3
"""
Kit to Notion Email Stats Sync
Syncs email performance stats from Kit back to Notion
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
        logging.FileHandler('stats_sync.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
KIT_API_KEY = os.environ.get('KIT_API_KEY')
EMAILS_DATABASE_ID = os.environ.get('EMAILS_DATABASE_ID', 'c2a53e49-4500-48c0-8344-dfcc6066b89f')

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


def query_sent_emails() -> List[Dict]:
    """Query Notion for emails that have been sent (have Kit Broadcast ID)"""
    url = f'https://api.notion.com/v1/databases/{EMAILS_DATABASE_ID}/query'

    payload = {
        "filter": {
            "property": "Kit Broadcast ID",
            "rich_text": {
                "is_not_empty": True
            }
        }
    }

    try:
        response = requests.post(url, headers=NOTION_HEADERS, json=payload)
        response.raise_for_status()
        results = response.json().get('results', [])
        logger.info(f"Found {len(results)} sent emails to sync")
        return results
    except requests.exceptions.RequestException as e:
        logger.error(f"Error querying Notion: {e}")
        return []


def get_kit_broadcast_stats(broadcast_id: str) -> Optional[Dict]:
    """Get broadcast statistics from Kit API"""
    url = f'https://api.kit.com/v4/broadcasts/{broadcast_id}/stats'

    try:
        response = requests.get(url, headers=KIT_HEADERS)
        response.raise_for_status()
        response_data = response.json()
        logger.info(f"Kit API response for broadcast {broadcast_id}: {response_data}")

        # Kit API returns: { "broadcast": { "id": ..., "stats": { ... } } }
        broadcast = response_data.get('broadcast', {})
        stats = broadcast.get('stats', {})
        logger.info(f"Retrieved stats for broadcast {broadcast_id}: {stats}")
        return stats
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting Kit broadcast stats: {e}")
        logger.error(f"Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
        return None


def extract_property_value(properties: Dict, prop_name: str, prop_type: str) -> any:
    """Extract value from Notion property"""
    prop = properties.get(prop_name, {})

    if prop_type == 'title':
        title_array = prop.get('title', [])
        return title_array[0].get('plain_text', '') if title_array else ''

    elif prop_type == 'rich_text':
        text_array = prop.get('rich_text', [])
        return text_array[0].get('plain_text', '') if text_array else ''

    elif prop_type == 'number':
        return prop.get('number')

    return None


def calculate_rate(numerator: int, denominator: int) -> float:
    """Calculate percentage rate"""
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def update_notion_email_stats(page_id: str, stats: Dict) -> bool:
    """Update Notion page with Kit broadcast stats"""
    url = f'https://api.notion.com/v1/pages/{page_id}'

    # Extract stats from Kit response
    # Kit API v4 returns: recipients, emails_opened, total_clicks, open_rate, click_rate
    recipients = stats.get('recipients', 0)
    total_opens = stats.get('emails_opened', 0)
    total_clicks = stats.get('total_clicks', 0)

    # Kit provides pre-calculated rates as percentages (e.g., 18.09 = 18.09%)
    # Notion percent format expects decimals (e.g., 0.1809 = 18.09%)
    # Convert: divide by 100 to get decimal format
    kit_open_rate = stats.get('open_rate', 0)
    kit_click_rate = stats.get('click_rate', 0)

    open_rate = round(kit_open_rate / 100, 4)  # 18.09 → 0.1809
    click_rate = round(kit_click_rate / 100, 4)  # 0.23 → 0.0023

    logger.info(f"Extracted stats - Recipients: {recipients}, Opens: {total_opens}, Clicks: {total_clicks}")
    logger.info(f"Kit rates (percentage): Open Rate: {kit_open_rate}%, Click Rate: {kit_click_rate}%")
    logger.info(f"Notion rates (decimal): Open Rate: {open_rate}, Click Rate: {click_rate}")

    payload = {
        "properties": {
            "Recipients": {
                "number": recipients
            },
            "Total Opens": {
                "number": total_opens
            },
            "Total Clicks": {
                "number": total_clicks
            },
            "Open Rate": {
                "number": open_rate
            },
            "Click Rate": {
                "number": click_rate
            }
        }
    }

    logger.info(f"Notion update payload: {payload}")

    try:
        response = requests.patch(url, headers=NOTION_HEADERS, json=payload)
        response.raise_for_status()
        logger.info(f"Updated stats for page {page_id}: OR={open_rate}%, CR={click_rate}%")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Error updating Notion page: {e}")
        logger.error(f"Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
        return False


def sync_email_stats(email_page: Dict) -> bool:
    """Sync stats for a single email from Kit to Notion"""
    page_id = email_page.get('id')
    properties = email_page.get('properties', {})

    # Extract email name and broadcast ID
    name = extract_property_value(properties, 'Name', 'title')
    broadcast_id = extract_property_value(properties, 'Kit Broadcast ID', 'rich_text')

    if not broadcast_id:
        logger.warning(f"Email {name} has no Kit Broadcast ID")
        return False

    logger.info(f"Syncing stats for: {name} (Broadcast: {broadcast_id})")

    # Get stats from Kit
    stats = get_kit_broadcast_stats(broadcast_id)

    if stats is None:
        logger.error(f"Failed to get stats for broadcast {broadcast_id} - API returned None")
        return False

    if not stats:
        logger.error(f"Failed to get stats for broadcast {broadcast_id} - stats dict is empty: {stats}")
        return False

    logger.info(f"Stats to sync: {stats}")

    # Update Notion with stats
    success = update_notion_email_stats(page_id, stats)

    if success:
        logger.info(f"✅ Successfully synced stats for: {name}")
    else:
        logger.error(f"❌ Failed to sync stats for: {name}")

    return success


def main():
    """Main execution function"""
    logger.info("=" * 50)
    logger.info("Starting Kit to Notion Stats Sync")
    logger.info("=" * 50)

    # Validate environment variables
    required_vars = ['NOTION_TOKEN', 'KIT_API_KEY']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)

    # Query sent emails
    sent_emails = query_sent_emails()

    if not sent_emails:
        logger.info("No sent emails to sync")
        return

    # Sync stats for each email
    success_count = 0
    failure_count = 0

    for email in sent_emails:
        try:
            if sync_email_stats(email):
                success_count += 1
            else:
                failure_count += 1
        except Exception as e:
            logger.error(f"Unexpected error syncing email stats: {e}")
            failure_count += 1

    # Summary
    logger.info("=" * 50)
    logger.info(f"Sync Complete!")
    logger.info(f"  ✅ Successful: {success_count}")
    logger.info(f"  ❌ Failed: {failure_count}")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
