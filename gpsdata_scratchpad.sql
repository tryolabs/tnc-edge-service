with t as ( 
    select *, ROW_NUMBER() OVER (ORDER BY gps_datetime) from gpsdata 
) select 
t1.gps_datetime, t2.gps_datetime, 
t1.lat, t1.lon, t2.lat, t2.lon, 
(t1.lat - t2.lat)*110.574 as latkmdiff, 
cos(t1.lat*3.14159265/180)*(t1.lon-t2.lon)*111.320 as lonkmdiff, 
sqrt(
    ((t1.lat - t2.lat)*110.574)^2 + 
    (cos(t1.lat*3.14159265/180)*(t1.lon-t2.lon)*111.320)^2
) as distance, 
sqrt(
    ((t1.lat - t2.lat)*110.574)^2 + 
    (cos(t1.lat*3.14159265/180)*(t1.lon-t2.lon)*111.320)^2
)/(extract(epoch from t1.gps_datetime - t2.gps_datetime)/3600) as kph 
from t t1 
join t t2 on t2.row_number = t1.row_number-1 
where t1.row_number > 200 
limit 500;


with t as ( 
    select *, ROW_NUMBER() OVER (ORDER BY gps_datetime) from gpsdata 
) select 
-- (t1.lat - t2.lat)*100000 as latdiff,
-- (t1.lon - t2.lon)*100000 as londiff,
t1.gps_datetime,
sqrt(
    ((t1.lat - t2.lat)*110.574)^2 + 
    (cos(t1.lat*3.14159265/180)*(t1.lon-t2.lon)*111.320)^2
)/(extract(epoch from t1.gps_datetime - t2.gps_datetime)/3600) as kph,
    case 
        when t1.lon-t2.lon = 0 then 0 
        else (6 - sign(t1.lon-t2.lon)*(sign(t1.lon-t2.lon)*atan((t1.lat - t2.lat)/(cos(t1.lat*3.14159265/180)*(t1.lon-t2.lon)))/3.14159 + 0.5 ) * 6 )
    end as clockheading
from t t1 
join t t2 on t2.row_number = t1.row_number-1
limit 10;
;

copy (
    with t as ( 
        select *, ROW_NUMBER() OVER (ORDER BY gps_datetime) from gpsdata 
    ) select 
    --  (t1.lat - t2.lat)*100000 as latdiff,
    --  (t1.lon - t2.lon)*100000 as londiff,
    t1.gps_datetime,
    sqrt(
        ((t1.lat - t2.lat)*110.574)^2 + 
        (cos(t1.lat*3.14159265/180)*(t1.lon-t2.lon)*111.320)^2
    )/(extract(epoch from t1.gps_datetime - t2.gps_datetime)/3600) as kph,
    case 
        when t1.lon-t2.lon = 0 then 0 
        else (6 - sign(t1.lon-t2.lon)*(sign(t1.lon-t2.lon)*atan((t1.lat - t2.lat)/(cos(t1.lat*3.14159265/180)*(t1.lon-t2.lon)))/3.14159 + 0.5 ) * 6 )
    end as clockheading
    from t t1 
    join t t2 on t2.row_number = t1.row_number-1
    -- limit 10
) to stdout csv header
;
