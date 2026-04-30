SELECT
  stock_code,
  description,
  units_sold_total,
  orders_count,
  gross_revenue,
  estimated_stock_left,
  stock_consumed_pct,
  alert_level,
  alert_reason,
  last_event_time
FROM workspace.si7006_t2.gold_alertas_reorder
ORDER BY estimated_stock_left ASC, units_sold_total DESC;
