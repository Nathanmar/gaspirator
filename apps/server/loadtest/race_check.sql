-- Database check after loadtest/locust_race.py: per lot of the race supplier, the
-- reservations made, the quantity reserved and what is left. Expected for every lot:
-- reservations = 1, reserved = 1, remaining_quantity = 0, overbooked = false,
-- consistent = true.
SELECT l.id,
       l.title,
       count(r.id) AS reservations,
       coalesce(sum(r.quantity), 0) AS reserved,
       l.remaining_quantity,
       coalesce(sum(r.quantity), 0) > 1 AS overbooked,
       -- 1 portion was left at the start: what was taken off = what was reserved.
       1 - l.remaining_quantity = coalesce(sum(r.quantity), 0) AS consistent
FROM lots l
LEFT JOIN reservations r ON r.lot_id = l.id
WHERE l.supplier_id = 1
GROUP BY l.id
ORDER BY l.id;
