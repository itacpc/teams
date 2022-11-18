SELECT
        CONCAT(s.first_name, ' ', s.last_name) AS name,
        s.email AS email,
        CASE WHEN t.id IS NULL THEN CONCAT(s.first_name, ' ', s.last_name) ELSE t.name END AS "team-name",
        'CONTESTANT' as "team-role",
        u.domain AS "university-domain",
        u.country_code as "country-code",
	u.country_subdivision_code AS "country-subdivision-code",
        s.kattis_handle AS "kattis-handle"
    FROM
        students s
        JOIN universities u ON u.id = s.university
        LEFT JOIN teams t ON s.team = t.id
    WHERE
        s.confirmed
    ORDER BY
        team;

SELECT
        CASE WHEN t.id IS NULL THEN CONCAT(s.first_name, ' ', s.last_name) ELSE t.name END AS "team-name",
	u.name AS "site-name",
        u.domain AS "university-domain",
        u.country_code as "country-code",
	u.country_subdivision_code AS "country-subdivision-code",
        '' AS "icpc-site-id",
	'' AS "icpc-team-id"
    FROM
        students s
        JOIN universities u ON u.id = s.university
        LEFT JOIN teams t ON s.team = t.id
    WHERE
        s.confirmed
    ORDER BY
        team;