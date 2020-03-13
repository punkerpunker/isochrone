
-- DROP FUNCTION public.catchment_area(double precision, double precision, double precision, text);

CREATE OR REPLACE FUNCTION public.catchment_area(
	x double precision,
	y double precision,
	cost double precision,
	type text)
    RETURNS geometry
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
AS $BODY$

DECLARE
  speed text;
  reverse_cost_time_column text;
  cost_time_column text;
  res_area text;
  tab_res_lines text;
  tab_grid text;
  tab_network text;
  node_id bigint;
  statement text;
  geomtext text;
  radius float;
BEGIN

res_area = null;
tab_network = 'ways';
tab_grid = 'grid';
tab_res_lines = concat('lines_', now()::text);
node_id = -1;
IF type = 'car' then
    reverse_cost_time_column = 'rcost_time_car';
	cost_time_column = 'cost_time_car';
	-- speed = '(maxspeed_forward/10)';
	speed = '20';
ELSE
	reverse_cost_time_column = 'cost_time_ped';
    cost_time_column = 'cost_time_ped';
	speed = '5';
end if;

EXECUTE 'SELECT id
        FROM '||tab_network||'_vertices_pgr
        ORDER BY the_geom <-> st_setsrid(st_makepoint('||x||','||y||'),4326)
        LIMIT 1' into node_id;

if node_id > -1 then
        statement = 'CREATE TEMP TABLE "'||tab_res_lines||'" AS (SELECT gid as id, the_geom as geom, node from '||tab_network||'
      join (SELECT node,edge FROM pgr_drivingDistance(
        ''SELECT gid as id, source, target, cost, reverse_cost FROM (SELECT gid, source, target, '||cost_time_column||' as cost, '||reverse_cost_time_column||' as reverse_cost, the_geom
      FROM '||tab_network||'
      WHERE ST_contains(ST_Transform(ST_Buffer(ST_Transform(ST_SetSRID(ST_MakePoint('||x||','||y||'),4326), 3395),
        '||cost||'*'||speed||'*1000.0/3600.0*1.3, 16), 4326), the_geom)) as preSelection'',
        '||node_id||', '||cost||', false
      )) d on '||tab_network||'.gid=d.edge);';
      EXECUTE statement;
	  -- workaround для новой версии pgrouting который не хочет работать с CGAL
	  --statement = 'select st_concavehull(st_setsrid((SELECT ST_Collect(geom) FROM "'||tab_res_lines||'"), 4326), 0.7);';
	  statement = 'select geom from ST_DumpRings(st_setsrid(pgr_pointsAsPolygon(''SELECT '||tab_network||'_vertices_pgr.id::integer, ST_X(the_geom)::float AS x, ST_Y(the_geom)::float AS y
        FROM '||tab_network||'_vertices_pgr join "'||tab_res_lines||'" on '||tab_network||'_vertices_pgr.id = "'||tab_res_lines||'".node''),4326));';
	  BEGIN
			EXECUTE statement into res_area;
			-- Иногда не можем построить зону, если так - строим круг
			exception when others then
			radius = speed::float * cost*10/36;
			statement = 'select ST_Buffer(ST_SetSRID(ST_MakePoint('||x||','||y||'),4326)::geography, '|| radius::text ||')';
			EXECUTE statement into res_area;
				
	  END;
	  -- Иногда возвращает пустую геометрию, если так - строим круг
	  IF res_area is not null then
	  	return res_area;
	  else
	    radius = speed::float * cost*10/36;
	  	statement = 'select ST_Buffer(ST_SetSRID(ST_MakePoint('||x||','||y||'),4326)::geography, '|| radius::text ||')';
		EXECUTE statement into res_area;
		return res_area;
	  end if;
end if;

END
$BODY$;

ALTER FUNCTION public.catchment_area(double precision, double precision, double precision, text)
    OWNER TO punker;

