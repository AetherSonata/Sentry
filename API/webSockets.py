import requests
import json
from flask import Flask, request, jsonify
from pyngrok import ngrok

# 🔹 Replace with your actual Helius API Key
HELIUS_API_KEY = "286df9ec-31df-4d1e-8152-6222ee113811"

# 🔹 Replace with your Webhook URL (e.g., from https://webhook.site/)
WEBHOOK_URL = "https://webhook.site/7ccc93d7-ddb4-4d28-95bb-9b176c618b18"

# 🔹 Authentication (if needed) - Update with actual credentials or leave blank
USERNAME = "your-username"
PASSWORD = "your-password"

# 🔹 Helius API endpoint for creating a webhook
HELIUS_WEBHOOK_URL = f"https://api.helius.xyz/v0/webhooks?api-key={HELIUS_API_KEY}"


def create_helius_webhook(token_address):
    """
    Creates a webhook for tracking price updates of a given Solana token address.

    :param token_address: The Solana token mint address to track.
    :return: Webhook creation response.
    """

    # Webhook payload
    payload = {
        "webhookURL": WEBHOOK_URL,
        "webhookType": "enhanced",  # Type of webhook (can be "raw", "enhanced", or "firehose")
        # "authHeader": "Basic " + USERNAME + ":" + PASSWORD,  # Optional authentication header
        "txnStatus": "all",  # Capture all transaction statuses
        "transactionTypes": ["SWAP"],  # Listen to swap transactions (change if needed)
        "accountAddresses": [token_address],  # Listen to the provided token address
    }

    try:
        # Send POST request to create the webhook
        response = requests.post(
            HELIUS_WEBHOOK_URL,
            headers={"Authorization": f"Basic {USERNAME}:{PASSWORD}", "Content-Type": "application/json"},
            data=json.dumps(payload),
        )

        if response.status_code == 200:
            print("✅ Webhook successfully created!")
            return response.json()
        else:
            print(f"❌ Failed to create webhook. Status Code: {response.status_code}, Error: {response.text}")
            return None

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        return None
    
def get_all_webhooks():
# Parse the JSON response

    url = f"https://api.helius.xyz/v0/webhooks?api-key={HELIUS_API_KEY}"

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        print("✅ Webhooks fetched successfully!")
        print(data)  # This will print all your webhooks
    else:
        print(f"❌ Failed to fetch webhooks. Status Code: {response.status_code}")
        print(response.text)
    return data

def delete_webhook(webhook_id):
    url = f"https://api.helius.xyz/v0/webhooks/{webhook_id}?api-key={HELIUS_API_KEY}"

    response = requests.delete(url)

    if response.status_code == 200:
        print(f"✅ Webhook with ID {webhook_id} deleted successfully!")
    else:
        print(f"❌ Failed to delete webhook with ID {webhook_id}. Status Code: {response.status_code}")

def start_ngrok_webhook():
    # Start ngrok tunnel
    public_url = ngrok.connect(5000).public_url
    print(f"🚀 Ngrok Public URL: {public_url}/webhook")



if __name__ == "__main__":
    # Ask user for token address input
    token_address = "So11111111111111111111111111111111111111112"

    active_webhooks = get_all_webhooks()
    if active_webhooks:
        for webhook in active_webhooks:
            webhook_id = webhook.get("webhookID")
            delete_webhook(webhook_id)

    # Create a new webhook for the provided token address
    if token_address:
        result = create_helius_webhook(token_address)
        if result:
            print(f"🔔 Webhook Details: {json.dumps(result, indent=4)}")
    else:
        print("❌ No token address provided. Exiting.")


