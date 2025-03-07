import requests
import json
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from pyngrok import ngrok

# 🔹 Load environment variables
load_dotenv()
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
NGROK_AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN")

# 🔹 Replace with your Webhook URL (e.g., from https://webhook.site/ or ngrok URL)
WEBHOOK_URL = "https://webhook.site/7ccc93d7-ddb4-4d28-95bb-9b176c618b18"

# 🔹 Authentication (if needed) - Update with actual credentials or leave blank
USERNAME = "your-username"
PASSWORD = "your-password"

# 🔹 Helius API endpoint for creating a webhook
HELIUS_WEBHOOK_URL = f"https://api.helius.xyz/v0/webhooks?api-key={HELIUS_API_KEY}"

app = Flask(__name__)

# Create a new webhook for the provided token address with LOCAL WEBHOOK URL FOR TESTING
def create_helius_webhook(token_address, ngrok_url):
    """
    Creates a webhook for tracking price updates of a given Solana token address.
    :param token_address: The Solana token mint address to track.
    :return: Webhook creation response.
    """

    webhook_url = f"{ngrok_url}/webhook"  # Local webhook URL for testing

    payload = {
        "webhookURL": webhook_url,  # NGROK webhook URL for testing
        "webhookType": "enhanced",  # Type of webhook (can be "raw", "enhanced", or "firehose")
        "txnStatus": "all",  # Capture all transaction statuses
        "transactionTypes": ["SWAP"],  # Listen to swap transactions (change if needed)
        "accountAddresses": [token_address],  # Listen to the provided token address
    }

    try:
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

# Get all webhooks (fetch)
def get_all_webhooks():
    url = f"https://api.helius.xyz/v0/webhooks?api-key={HELIUS_API_KEY}"

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        print("✅ Webhooks fetched successfully!")
        return data  # Return webhooks data
    else:
        print(f"❌ Failed to fetch webhooks. Status Code: {response.status_code}")
        return None

# Delete specific webhook by ID
def delete_webhook(webhook_id):
    url = f"https://api.helius.xyz/v0/webhooks/{webhook_id}?api-key={HELIUS_API_KEY}"

    response = requests.delete(url)

    if response.status_code == 200:
        print(f"✅ Webhook with ID {webhook_id} deleted successfully!")
    else:
        print(f"❌ Failed to delete webhook with ID {webhook_id}. Status Code: {response.status_code}")

@app.route("/webhook", methods=["POST"])
def listen_to_swaps():
    data = request.json  # Get JSON data from webhook request
    if data.get("type") == "SWAP":
        print("\n🔔 Swap Event Received:")
        print(json.dumps(data, indent=4))  # Print formatted JSON data of the swap event
    else:
        print("\n🔔 Non-Swap Event Received:")
        print(json.dumps(data, indent=4))  # Print other events for debugging
    return jsonify({"message": "✅ Webhook received"}), 200  # Respond to Helius

def start_ngrok_webhook():
    # Start ngrok tunnel
    ngrok.set_auth_token(NGROK_AUTH_TOKEN)
    public_url = ngrok.connect(5000).public_url
    print(f"🚀 Ngrok Public URL: {public_url}/webhook")

    return public_url

if __name__ == "__main__":
    # Ask user for token address input (e.g., "So11111111111111111111111111111111111111112")
    token_address = "So11111111111111111111111111111111111111112"

    # Fetch and delete all active webhooks
    active_webhooks = get_all_webhooks()
    if active_webhooks:
        for webhook in active_webhooks:
            webhook_id = webhook.get("webhookID")
            delete_webhook(webhook_id)

    # Start ngrok tunnel for testing webhook locally
    public_url = start_ngrok_webhook()

    # Create a new webhook for the provided token address
    if token_address:
        result = create_helius_webhook(token_address, public_url)
        if result:
            print(f"🔔 Webhook Details: {json.dumps(result, indent=4)}")
    else:
        print("❌ No token address provided. Exiting.")

    # Run Flask app
    app.run(host="0.0.0.0", port=5000, debug=False)

