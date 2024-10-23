-- puntarenas
TRUNCATE port_location;

INSERT INTO
    port_location (port_location)
VALUES
    (point(9.8106338, -84.875245));

-- QUEPOS
TRUNCATE port_location;

INSERT INTO
    port_location (port_location)
VALUES
    (point(9.4241879, -84.1833372));

SELECT
    *,
    'dep'
FROM
    port_departures
UNION
SELECT
    *,
    'arr'
FROM
    port_arrivals;