-- FUNCTION: public.find_cost_to_closest(double precision, double precision, text)

-- DROP FUNCTION public.find_cost_to_closest(double precision, double precision, text);

CREATE OR REPLACE FUNCTION public.find_cost_to_closest(
	x double precision,
	y double precision,
	poi_sql text)
    RETURNS double precision
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
AS $BODY$

DECLARE
 cost double precision;
 multiplier double precision;
 long_lat text;
 long_column text;
 lat_column text;
BEGIN
poi_sql = REPLACE(poi_sql, '''', '''''');
EXECUTE format('select max(agg_cost) as cost
    from find_path_to_closest(%s, %s, ''%s'')
    group by end_vid order by max(agg_cost) limit 1', x, y, poi_sql) into cost;
IF cost is not null THEN
 return cost;
else
 poi_sql = REPLACE(poi_sql, '''''', '''');
 multiplier = 2.5;
 long_lat = REPLACE(split_part(split_part(poi_sql, 'select', 2), 'from', 1), ' ', '');
 long_column = split_part(long_lat, ',', 1);
 lat_column = split_part(long_lat, ',', 2);
 execute format('select ST_Distance(ST_MakePoint(%s, %s)::geography, ST_MakePoint(dist.long, dist.lat)::geography)
        from (select b.%s as long, b.%s as lat from (%s) as b where ST_Dwithin(ST_MakePoint(b.%s, b.%s), ST_MakePoint(%s, %s), 10000)
        order by ST_MakePoint(b.%s, b.%s) <-> ST_MakePoint(%s, %s) limit 1) as dist', x, y, long_column, lat_column,
       poi_sql, long_column, lat_column, x, y, long_column, lat_column, x, y) into cost;
 return cost*multiplier;
end if;
END
$BODY$;

ALTER FUNCTION public.find_cost_to_closest(double precision, double precision, text)
    OWNER TO punker;

