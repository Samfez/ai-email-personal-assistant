import os

from dotenv import load_dotenv
from nylas import Client
from nylas.models.webhooks import CreateWebhookRequest, WebhookTriggers

load_dotenv()

nylas = Client(
    api_key=os.environ.get("NYLAS_API_KEY", ""),
    api_uri=os.environ.get("NYLAS_API_URI", ""),
)

# Define the webhook properties
request_body = CreateWebhookRequest(
    trigger_types=[WebhookTriggers.MESSAGE_CREATED],
    # In the format https://YOURSERVER.COM/webhook
    webhook_url=os.environ.get("SERVER_URL", "") + "/events",
    description="Message Created Webhook",
    notification_email_addresses=[os.environ.get("EMAIL", "")],
)

# Create the webhook
webhook, _, _ = nylas.webhooks.create(request_body=request_body)
webhook_secret = webhook.webhook_secret

# Print the newly created webhook
print(webhook)
print(webhook_secret)