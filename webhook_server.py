from flask import Flask, request, jsonify
import stripe
import os
from dotenv import load_dotenv
import firestore_client

load_dotenv()
app = Flask(__name__)

# --- Stripe and Plan Configuration ---
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

PLAN_DETAILS = {
    os.getenv("PRICE_ID_LIGHT"): {"name": "Light", "uses": 50},
}
DEFAULT_PLAN = {"name": "Free", "uses": 5}

@app.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        return 'Webhook error', 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_id = session.get('customer')
        subscription_id = session.get('subscription')
        if subscription_id:
            subscription = stripe.Subscription.retrieve(subscription_id)
            price_id = subscription['items']['data'][0]['price']['id']
            plan_info = PLAN_DETAILS.get(price_id)
            if customer_id and plan_info:
                firestore_client.update_user_plan(customer_id, plan_info["name"], plan_info["uses"])

    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        customer_id = subscription.get('customer')
        if customer_id:
            firestore_client.update_user_plan(customer_id, DEFAULT_PLAN["name"], DEFAULT_PLAN["uses"])

    return jsonify(success=True)

if __name__ == '__main__':
    app.run(port=int(os.getenv("PORT", 8080)))
