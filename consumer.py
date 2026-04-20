"""
ShopStream Consumer
-------------------
Reads e-commerce events from Redpanda and persists them to DuckDB.

Key improvements over v1:
- group_id prevents replaying all messages on every restart
- try/finally guarantees the DB connection is always closed cleanly
- Basic validation rejects malformed events before they pollute the DB
- ingested_at column added so we can track pipeline latency
"""

import json
import os
import duckdb
from kafka import KafkaConsumer

BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "ecommerce_events"
GROUP_ID = "shopstream-consumer-v1"
DB_PATH = "data/shopstream.db"

VALID_EVENT_TYPES = {"page_view", "add_to_cart", "order_placed"}
REQUIRED_FIELDS = {"event_type", "user_id", "session_id", "sku", "price", "timestamp"}


def validate_event(event: dict) -> tuple[bool, str]:
    """
    Validate an incoming event.

    Returns (is_valid, reason). We check:
      1. All required fields are present
      2. event_type is one of the known types
      3. price is a positive number
    """
    missing = REQUIRED_FIELDS - event.keys()
    if missing:
        return False, f"Missing fields: {missing}"

    if event["event_type"] not in VALID_EVENT_TYPES:
        return False, f"Unknown event_type: {event['event_type']}"

    try:
        price = float(event["price"])
        if price <= 0:
            return False, f"Price must be positive, got: {price}"
    except (TypeError, ValueError):
        return False, f"Invalid price value: {event['price']}"

    return True, "ok"


if __name__ == "__main__":
    # Ensure the data directory exists
    os.makedirs("data", exist_ok=True)

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,          # Kafka remembers our position; restarts pick up where we left off
        auto_offset_reset="earliest",  # On first run, read from the beginning
        enable_auto_commit=True,
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
    )

    db = duckdb.connect(DB_PATH)
    db.execute("""
        CREATE TABLE IF NOT EXISTS raw_events (
            event_json  JSON,
            ingested_at TIMESTAMP DEFAULT current_timestamp
        )
    """)

    print(f"📥 Consumer started — listening on '{TOPIC}' (group: {GROUP_ID})")
    print(f"   Writing to: {DB_PATH}\n")

    valid_count = 0
    invalid_count = 0

    try:
        for message in consumer:
            event = message.value

            is_valid, reason = validate_event(event)
            if not is_valid:
                invalid_count += 1
                print(f"  ✗ Skipped invalid event ({reason}): {event}")
                continue

            db.execute(
                "INSERT INTO raw_events (event_json) VALUES (?)",
                [json.dumps(event)],
            )
            valid_count += 1
            print(
                f"  ✓ {event['event_type']:<15} | "
                f"User: {event['user_id']} | "
                f"SKU: {event['sku']}"
            )

    except KeyboardInterrupt:
        print(
            f"\n✋ Stopping consumer.\n"
            f"   Stored:  {valid_count} events\n"
            f"   Skipped: {invalid_count} invalid events"
        )
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        raise
    finally:
        db.close()
        consumer.close()
