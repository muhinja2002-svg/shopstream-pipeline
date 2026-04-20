-- models/marts/fct_conversion_funnel.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Fact table: conversion funnel aggregated across all users.
--
-- Columns:
--   total_visitors        — unique users with at least one page_view
--   total_adds            — unique users who added to cart
--   total_purchases       — unique users who placed an order
--   page_to_cart_pct      — % of visitors who added to cart
--   cart_to_order_pct     — % of cart-adders who completed a purchase
--   overall_conversion_pct — % of visitors who ultimately purchased
-- ─────────────────────────────────────────────────────────────────────────────

WITH user_journey AS (
    -- Collapse all events to one row per user,
    -- flagging which funnel steps they completed.
    SELECT
        user_id,
        MAX(CASE WHEN event_type = 'page_view'    THEN 1 ELSE 0 END) AS saw_page,
        MAX(CASE WHEN event_type = 'add_to_cart'  THEN 1 ELSE 0 END) AS added_to_cart,
        MAX(CASE WHEN event_type = 'order_placed' THEN 1 ELSE 0 END) AS purchased
    FROM {{ ref('stg_events') }}
    GROUP BY user_id
),

funnel_totals AS (
    SELECT
        SUM(saw_page)       AS total_visitors,
        SUM(added_to_cart)  AS total_adds,
        SUM(purchased)      AS total_purchases
    FROM user_journey
)

SELECT
    total_visitors,
    total_adds,
    total_purchases,

    -- Drop-off rates
    ROUND(total_adds::FLOAT        / NULLIF(total_visitors, 0) * 100, 2) AS page_to_cart_pct,
    ROUND(total_purchases::FLOAT   / NULLIF(total_adds, 0)     * 100, 2) AS cart_to_order_pct,
    ROUND(total_purchases::FLOAT   / NULLIF(total_visitors, 0) * 100, 2) AS overall_conversion_pct

FROM funnel_totals
