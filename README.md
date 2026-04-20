# ShopStream — Real-Time E-Commerce Analytics Pipeline

An end-to-end streaming data pipeline that simulates e-commerce events, processes them in real time, and surfaces a live analytics dashboard.

**Stack:** Redpanda · DuckDB · dbt · Python · Streamlit

---

## Architecture

```
┌─────────────┐    Kafka API     ┌──────────────┐    DuckDB     ┌─────────────┐
│ producer.py │ ───────────────► │ consumer.py  │ ────────────► │ shopstream  │
│             │                  │              │               │    .db      │
│ Generates   │    Redpanda      │ Validates &  │               └──────┬──────┘
│ mock events │    (Docker)      │ persists     │                      │
└─────────────┘                  └──────────────┘               ┌──────▼──────┐
                                                                 │    dbt      │
                                                                 │  models     │
                                                                 └──────┬──────┘
                                                                        │
                                                                 ┌──────▼──────┐
                                                                 │ dashboard   │
                                                                 │    .py      │
                                                                 │ (Streamlit) │
                                                                 └─────────────┘
```

### Data Flow

1. **Producer** generates realistic e-commerce sessions (page view → add to cart → order placed) with real timestamps and consistent session context
2. **Redpanda** (Kafka-compatible broker) buffers the event stream
3. **Consumer** reads from Redpanda, validates each event, and writes it as raw JSON to DuckDB
4. **dbt** transforms the raw JSON into clean, typed staging and mart models
5. **Streamlit dashboard** queries DuckDB and displays live funnel metrics

---

## Prerequisites

- Python 3.10+
- Docker + Docker Compose
- Git

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/shopstream.git
cd shopstream
```

### 2. Install Python dependencies

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Start Redpanda

```bash
docker compose up -d
```

This starts three containers:
- **redpanda** — the Kafka-compatible broker on port 9092
- **redpanda-console** — web UI at [http://localhost:8080](http://localhost:8080)
- **topic-init** — creates the `ecommerce_events` topic and exits

Wait ~15 seconds for Redpanda to become healthy before running the producer.

---

## Running the Pipeline

Open **three separate terminal windows** (all inside the project directory with the venv active).

### Terminal 1 — Start the consumer

```bash
python consumer.py
```

The consumer connects to Redpanda, creates the `raw_events` table in DuckDB, and waits for events.

### Terminal 2 — Start the producer

```bash
python producer.py
```

The producer generates user sessions and publishes them to Redpanda. You'll see events flowing in the consumer terminal.

### Terminal 3 — Launch the dashboard

```bash
streamlit run dashboard.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser to see the live analytics dashboard.

---

## Running dbt Transformations

While the consumer is **stopped** (to avoid a file lock):

```bash
# Run all models
dbt run --profiles-dir .

# Run tests (not_null, accepted_values, etc.)
dbt test --profiles-dir .

# Generate and serve documentation
dbt docs generate --profiles-dir .
dbt docs serve --profiles-dir .
```

### dbt Model Lineage

```
raw_events (source)
    └── stg_events (staging/view)
            └── fct_conversion_funnel (marts/table)
```

---

## Project Structure

```
shopstream/
├── producer.py              # Generates mock events → Redpanda
├── consumer.py              # Reads from Redpanda → DuckDB
├── dashboard.py             # Streamlit analytics dashboard
├── docker-compose.yml       # Redpanda broker + console + topic init
├── requirements.txt         # Python dependencies
├── dbt_project.yml          # dbt project configuration
├── profiles.yml             # dbt connection profile (DuckDB)
├── models/
│   ├── sources.yml          # dbt source definition (raw_events table)
│   ├── schema.yml           # Model docs + data quality tests
│   ├── staging/
│   │   └── stg_events.sql   # Parses JSON → typed columns (view)
│   └── marts/
│       └── fct_conversion_funnel.sql  # Funnel aggregation (table)
└── data/
    └── shopstream.db        # DuckDB database (git-ignored)
```

---

## Stopping Everything

```bash
# Stop producer/consumer with Ctrl+C in their terminals

# Stop Redpanda
docker compose down
```

---

## Tech Stack

| Tool | Purpose |
|---|---|
| **Redpanda** | Kafka-compatible streaming broker (via Docker) |
| **kafka-python** | Python Kafka client for producer/consumer |
| **DuckDB** | Embedded OLAP database for event storage |
| **dbt-duckdb** | SQL transformation layer with lineage, docs & tests |
| **Streamlit** | Interactive analytics dashboard |
| **Plotly** | Funnel and time-series charts |
| **Faker** | Mock user ID generation |
