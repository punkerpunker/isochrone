-- FUNCTION: public.find_path_to_closest(double precision, double precision, text)

-- DROP FUNCTION public.find_path_to_closest(double precision, double precision, text);

CREATE OR REPLACE FUNCTION public.find_path_to_closest(
	x double precision,
	y double precision,
	poi_sql text)
    RETURNS TABLE(seq integer, path_seq integer, end_vid bigint, node bigint, edge bigint, cost double precision, agg_cost double precision, the_geom geometry) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
DECLARE
 node_id integer;
 statement text;
 long_lat text;
 long_column text;
 lat_column text;
 points_table text;
 tab_network text default 'ways';
 nodes_array bigint[];
 node_x float;
 node_y float;
BEGIN

EXECUTE 'SELECT id, ST_X(the_geom), ST_Y(the_geom)
        FROM '||tab_network||'_vertices_pgr
        ORDER BY the_geom <-> st_setsrid(st_makepoint('||x||','||y||'),4326)
        LIMIT 1' into node_id, node_x, node_y;

points_table = concat('points_', now()::text);

 long_lat = REPLACE(split_part(split_part(poi_sql, 'select', 2), 'from', 1), ' ', '');
 long_column = split_part(long_lat, ',', 1);
 lat_column = split_part(long_lat, ',', 2);

 statement = format('create temp table "%s" as (select ST_MakePoint(%s, %s)::geography as poi_geom from (%s) as poi_sql
      order by ST_MakePoint(%s, %s)::geography <-> ST_MakePoint(%s, %s)::geography limit 3)',
        points_table, long_column, lat_column, poi_sql, long_column, lat_column, x, y);
 execute statement;
 statement = format('select array_agg(closest_nodes.id)
         from "%s" as poi
      join lateral (select id
           from %s_vertices_pgr as nodes
           order by nodes.the_geom <-> poi.poi_geom::geometry limit 1) as closest_nodes on True', points_table, tab_network);

 execute statement into nodes_array;
 return query select d.*, n.the_geom from pgr_dijkstra
        (format('SELECT gid as id,  source,  target, length_m as cost
         FROM %s as r ,(select ST_Expand(ST_Extent(the_geom), 0.05) as box from %s as l1 where l1.source = %s) as box
         WHERE r.the_geom && box.box', tab_network, tab_network, node_id),
        node_id, ARRAY[nodes_array[1], nodes_array[2], nodes_array[3]]) as d left join ways as n on n.gid = d.edge;
END
$BODY$;

ALTER FUNCTION public.find_path_to_closest(double precision, double precision, text)
    OWNER TO punker;

