"""
ShopStream Producer
-------------------
Generates realistic e-commerce events and publishes them to Redpanda.

Key improvements over v1:
- Real UTC timestamps (not random historical dates)
- Session-based events: SKU and price stay consistent within a session
- Funnel logic: page_view -> add_to_cart -> order_placed follows realistic probabilities
- Graceful shutdown with producer.flush()
"""

import json
import time
import random
import uuid
from datetime import datetime, timezone
from kafka import KafkaProducer

BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "ecommerce_events"

# Pre-defined product catalog so SKU/price are consistent
PRODUCTS = [
    {"sku": f"SKU-{i:02d}", "price": round(random.uniform(9.99, 499.99), 2)}
    for i in range(10, 51)
]


def now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def generate_session(user_id: str) -> list[dict]:
    """
    Simulate a realistic user session on an e-commerce store.

    A session always starts with a page_view. From there:
      - 30% of visitors add something to their cart
      - 33% of those (≈10% overall) complete a purchase

    All events in a session share the same session_id, SKU, and price
    so the data can be tracked end-to-end.
    """
    session_id = str(uuid.uuid4())[:8]
    product = random.choice(PRODUCTS)
    events = []

    # Step 1 — always a page view
    events.append(
        {
            "event_type": "page_view",
            "user_id": user_id,
            "session_id": session_id,
            "sku": product["sku"],
            "price": product["price"],
            "timestamp": now_iso(),
        }
    )

    # Step 2 — 30% add to cart
    if random.random() < 0.30:
        events.append(
            {
                "event_type": "add_to_cart",
                "user_id": user_id,
                "session_id": session_id,
                "sku": product["sku"],
                "price": product["price"],
                "timestamp": now_iso(),
            }
        )

        # Step 3 — 33% of cart-adders place an order (~10% overall)
        if random.random() < 0.33:
            events.append(
                {
                    "event_type": "order_placed",
                    "user_id": user_id,
                    "session_id": session_id,
                    "sku": product["sku"],
                    "price": product["price"],
                    "timestamp": now_iso(),
                }
            )

    return events


if __name__ == "__main__":
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        acks="all",  # Wait for broker acknowledgement before continuing
    )

    print(f"🚀 ShopStream Producer started — publishing to '{TOPIC}'")
    print("   Press Ctrl+C to stop.\n")

    events_sent = 0
    try:
        while True:
            user_id = f"usr_{random.randint(1000, 9999)}"
            session_events = generate_session(user_id)

            for event in session_events:
                producer.send(TOPIC, event)
                events_sent += 1
                print(
                    f"  → {event['event_type']:<15} | "
                    f"User: {event['user_id']} | "
                    f"SKU: {event['sku']} | "
                    f"${event['price']:.2f}"
                )

            # Pause between sessions to simulate real traffic
            time.sleep(random.uniform(0.5, 2.0))

    except KeyboardInterrupt:
        print(f"\n✋ Stopping producer. Total events sent: {events_sent}")
    finally:
        producer.flush()
        producer.close()
