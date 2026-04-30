SELECT
  stock_code,
  description,
  estimated_stock_left,
  stock_consumed_pct,
  units_sold_total,
  alert_level
FROM workspace.si7006_t2.gold_alertas_reorder
ORDER BY estimated_stock_left ASC, units_sold_total DESC
LIMIT 10;
