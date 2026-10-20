-- Named queries are loaded and executed by sessions/db.py.
-- name: session_list
SELECT s.*, h.name AS hall_name, h.capacity, h.hall_type
FROM sessions AS s JOIN halls AS h ON h.id = s.hall_id
WHERE s.tickets >= :tickets
ORDER BY
    CASE WHEN :sort = 'date' THEN s.show_date END ASC,
    CASE WHEN :sort = '-date' THEN s.show_date END DESC,
    CASE WHEN :sort = 'tickets' THEN s.tickets END ASC,
    CASE WHEN :sort = '-tickets' THEN s.tickets END DESC,
    s.id ASC
LIMIT :limit;

-- name: session_detail
SELECT s.*, h.name AS hall_name, h.capacity, h.hall_type
FROM sessions AS s JOIN halls AS h ON h.id = s.hall_id
WHERE s.slug = :slug;

-- name: halls
SELECT id, name, capacity, hall_type FROM halls ORDER BY id;

-- name: count
SELECT COUNT(*) AS total FROM sessions;

-- name: statistics
SELECT show_type, COUNT(*) AS session_count, SUM(tickets) AS tickets_total
FROM sessions
GROUP BY show_type
HAVING COUNT(*) >= :minimum
ORDER BY session_count DESC, show_type ASC;
