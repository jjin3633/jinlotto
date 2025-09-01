import os
import json
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)


def post_to_slack(text: str, webhook_url: Optional[str] = None) -> None:
    """Send a simple text message to Slack via Incoming Webhook.

    Reads SLACK_WEBHOOK_URL from environment if webhook_url is not provided.
    """
    url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        logger.info("SLACK_WEBHOOK_URL not set. Skipping Slack notification.")
        return
    try:
        payload = {"text": text}
        headers = {"Content-Type": "application/json"}
        resp = requests.post(url, data=json.dumps(payload), headers=headers, timeout=10)
        resp.raise_for_status()
    except Exception as exc:
        logger.error("Failed to send Slack notification: %s", exc)


