import random
import string
import asyncio
from datetime import datetime
from db import add_payment, update_payment_status, get_user, set_premium, get_plan, get_all_plans

def generate_tx_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))

# Placeholder: replace with actual blockchain API calls
async def verify_payment(tx_id, expected_amount, currency, address):
    # Simulate verification after 10 seconds
    await asyncio.sleep(10)
    # For demo, assume success
    return True, "TRANSACTION_CONFIRMED"

async def create_payment(user_id, plan_id, currency):
    plan = get_plan(plan_id)
    if not plan:
        return None
    amount = plan["price"]
    tx_id = generate_tx_id()
    add_payment(user_id, plan_id, amount, currency, tx_id)
    # In production, generate a real address per transaction
    address = "address"  # placeholder
    return {
        "tx_id": tx_id,
        "amount": amount,
        "currency": currency,
        "address": address,
        "expires_in": 120  # minutes
    }

async def check_payment(tx_id):
    success, details = await verify_payment(tx_id, 0, "", "")
    if success:
        payment = get_payment_by_tx(tx_id)
        if payment and payment["status"] == "pending":
            plan = get_plan(payment["plan_id"])
            if plan:
                set_premium(payment["user_id"], plan["duration"])
                update_payment_status(tx_id, "completed")
                return True
    return False
