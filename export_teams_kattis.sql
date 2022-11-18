CREATE TEMPORARY VIEW kattis_participants AS (
    SELECT
        CONCAT(TRIM(s.first_name), ' ', TRIM(s.last_name)) AS name,
        s.email AS email,
        CASE
            WHEN t.id IS NULL THEN CONCAT(TRIM(s.first_name), ' ', TRIM(s.last_name))
            ELSE t.name
        END AS "team-name",
        'CONTESTANT' AS "team-role",
        u.domain AS "university-domain",
        'ITA' AS "country-code",
        u.kattis_subdivision AS "country-subdivision-code",
        s.kattis_handle AS "kattis-handle"
    FROM
        students s
        JOIN universities u ON u.id = s.university
        LEFT JOIN teams t ON s.team = t.id
    WHERE
        s.confirmed
    ORDER BY
        team
);

CREATE TEMPORARY VIEW kattis_teams AS (
    SELECT
        DISTINCT CASE
            WHEN t.id IS NULL THEN CONCAT(TRIM(s.first_name), ' ', TRIM(s.last_name))
            ELSE t.name
        END AS "team-name",
        u.name AS "site-name",
        u.domain AS "university-domain",
        'ITA' AS "country-code",
        u.kattis_subdivision AS "country-subdivision-code",
        '' AS "icpc-site-id",
        '' AS "icpc-team-id"
    FROM
        students s
        JOIN universities u ON u.id = s.university
        LEFT JOIN teams t ON s.team = t.id
    WHERE
        s.confirmed
    ORDER BY
        team
);

\copy (SELECT * FROM kattis_participants) TO 'kattis-participants.csv' DELIMITER ',' CSV HEADER;
\copy (SELECT * FROM kattis_teams) TO 'kattis-teams.csv' DELIMITER ',' CSV HEADER;
