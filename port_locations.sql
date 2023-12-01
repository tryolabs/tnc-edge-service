
-- puntarenas
truncate port_location;
insert into port_location (port_location) values (point(9.8106338, -84.875245));



-- QUEPOS
truncate port_location;
insert into port_location (port_location) values (point(9.4241879,-84.1833372));


select *, 'dep' from port_departures union select *, 'arr' from port_arrivals;
