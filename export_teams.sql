CREATE TEMPORARY VIEW itacpc22 AS (
    SELECT
        COALESCE(t.id, -1) AS team_id,
        COALESCE(t.name, s.first_name || ' ' || s.last_name) AS team_name,
        u.domain AS university,
        s.first_name AS first_name,
        s.last_name AS last_name,
        s.email AS school_email,
        s.kattis_handle AS kattis_handle
    FROM
        students s
        JOIN universities u ON u.id = s.university
        LEFT JOIN teams t ON s.team = t.id
    WHERE
        s.confirmed
    ORDER BY
        team_id
);

-- SELECT
--     *
-- FROM
--     itacpc22;

-- \copy itacpc22 to 'itacpc22.csv' csv delimiter ','
