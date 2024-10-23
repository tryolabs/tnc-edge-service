WITH t AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            ORDER BY
                gps_datetime
        )
    FROM
        gpsdata
)
SELECT
    t1.gps_datetime,
    t2.gps_datetime,
    t1.lat,
    t1.lon,
    t2.lat,
    t2.lon,
    (t1.lat - t2.lat) * 110.574 AS latkmdiff,
    cos(t1.lat * 3.14159265 / 180) *(t1.lon - t2.lon) * 111.320 AS lonkmdiff,
    sqrt(
        ((t1.lat - t2.lat) * 110.574) ^ 2 + (
            cos(t1.lat * 3.14159265 / 180) *(t1.lon - t2.lon) * 111.320
        ) ^ 2
    ) AS distance,
    sqrt(
        ((t1.lat - t2.lat) * 110.574) ^ 2 + (
            cos(t1.lat * 3.14159265 / 180) *(t1.lon - t2.lon) * 111.320
        ) ^ 2
    ) /(
        extract(
            epoch
            FROM
                t1.gps_datetime - t2.gps_datetime
        ) / 3600
    ) AS kph
FROM
    t t1
    JOIN t t2 ON t2.row_number = t1.row_number -1
WHERE
    t1.row_number > 200
LIMIT
    500;

WITH t AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            ORDER BY
                gps_datetime
        )
    FROM
        gpsdata
)
SELECT
    -- (t1.lat - t2.lat)*100000 as latdiff,
    -- (t1.lon - t2.lon)*100000 as londiff,
    t1.gps_datetime,
    sqrt(
        ((t1.lat - t2.lat) * 110.574) ^ 2 + (
            cos(t1.lat * 3.14159265 / 180) *(t1.lon - t2.lon) * 111.320
        ) ^ 2
    ) /(
        extract(
            epoch
            FROM
                t1.gps_datetime - t2.gps_datetime
        ) / 3600
    ) AS kph,
    CASE
        WHEN t1.lon - t2.lon = 0 THEN 0
        ELSE (
            6 - sign(t1.lon - t2.lon) *(
                sign(t1.lon - t2.lon) * atan(
                    (t1.lat - t2.lat) /(
                        cos(t1.lat * 3.14159265 / 180) *(t1.lon - t2.lon)
                    )
                ) / 3.14159 + 0.5
            ) * 6
        )
    END AS clockheading
FROM
    t t1
    JOIN t t2 ON t2.row_number = t1.row_number -1
LIMIT
    10;

;

copy (
    WITH t AS (
        SELECT
            *,
            ROW_NUMBER() OVER (
                ORDER BY
                    gps_datetime
            )
        FROM
            gpsdata
    )
    SELECT
        --  (t1.lat - t2.lat)*100000 as latdiff,
        --  (t1.lon - t2.lon)*100000 as londiff,
        t1.gps_datetime,
        sqrt(
            ((t1.lat - t2.lat) * 110.574) ^ 2 + (
                cos(t1.lat * 3.14159265 / 180) *(t1.lon - t2.lon) * 111.320
            ) ^ 2
        ) /(
            extract(
                epoch
                FROM
                    t1.gps_datetime - t2.gps_datetime
            ) / 3600
        ) AS kph,
        CASE
            WHEN t1.lon - t2.lon = 0 THEN 0
            ELSE (
                6 - sign(t1.lon - t2.lon) *(
                    sign(t1.lon - t2.lon) * atan(
                        (t1.lat - t2.lat) /(
                            cos(t1.lat * 3.14159265 / 180) *(t1.lon - t2.lon)
                        )
                    ) / 3.14159 + 0.5
                ) * 6
            )
        END AS clockheading
    FROM
        t t1
        JOIN t t2 ON t2.row_number = t1.row_number -1 -- limit 10
) TO stdout csv header;