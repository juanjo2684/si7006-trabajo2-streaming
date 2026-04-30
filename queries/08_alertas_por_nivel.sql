SELECT
  alert_level,
  COUNT(*) AS total_alertas
FROM workspace.si7006_t2.gold_alertas_reorder
GROUP BY alert_level
ORDER BY total_alertas DESC;
