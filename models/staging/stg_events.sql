-- models/staging/stg_events.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Staging layer: parse the raw JSON blob into properly typed columns.
--
-- This is the *only* place we touch event_json. All downstream models
-- reference stg_events (via ref()) so changes to the JSON structure only
-- need to be updated here.
-- ─────────────────────────────────────────────────────────────────────────────

SELECT
    -- User & session identifiers
    event_json->>'user_id'                        AS user_id,
    event_json->>'session_id'                     AS session_id,

    -- Event metadata
    event_json->>'event_type'                     AS event_type,

    -- Product details
    event_json->>'sku'                            AS sku,
    (event_json->>'price')::FLOAT                 AS price,

    -- Timestamps
    (event_json->>'timestamp')::TIMESTAMP         AS event_at,
    ingested_at

FROM {{ source('shopstream', 'raw_events') }}

-- Filter out any rows that slipped past consumer validation
WHERE event_json->>'event_type' IN ('page_view', 'add_to_cart', 'order_placed')
  AND (event_json->>'price')::FLOAT > 0
