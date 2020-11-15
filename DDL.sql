-- テーブル作成
create table fish_info(
    fish_id VARCHAR (20) primary key,
    fish_name VARCHAR (20),
    fish_icon TEXT,
    min_length integer,
    max_length integer,
    rarity integer,
    comment TEXT,
    created_at timestamp not null default current_timestamp,
    updated_at timestamp not null default current_timestamp
);

create table fish_catch(
    fish_id VARCHAR (20),
    angler_id VARCHAR (20),
    min_length integer,
    max_length integer,
    count integer,
    point integer,
    created_at timestamp not null default current_timestamp,
    updated_at timestamp not null default current_timestamp,
    CONSTRAINT fish_catch_pk PRIMARY KEY(fish_id, angler_id)
);

create table angler_ranking(
    angler_id VARCHAR (20),
    total_point integer,
    weekly_point integer,
    monthly_point integer,
    created_at timestamp not null default current_timestamp,
    updated_at timestamp not null default current_timestamp,
    constraint upsert_pk primary key(angler_id)
);

create table weights(
    rarity integer primary key,
    weights real,
    created_at timestamp not null default current_timestamp,
    updated_at timestamp not null default current_timestamp
);

-- 更新日時のトリガー作成
create function set_update_time() returns opaque as '
  begin
    new.updated_at := ''now'';
    return new;
  end;
' language 'plpgsql';

create trigger update_tri before
update
    on fish_info for each row execute procedure set_update_time();

create trigger update_tri before
update
    on fish_catch for each row execute procedure set_update_time();

create trigger update_tri before
update
    on angler_ranking for each row execute procedure set_update_time();

create trigger update_tri before
update
    on weights for each row execute procedure set_update_time();


-- 新規作成時のストアド作成
DROP function angler_ranking_trigger_function CASCADE;
-- CREATE
-- OR  REPLACE FUNCTION angler_ranking_trigger_function(
--     ) RETURNS TRIGGER AS $BODY$
--     BEGIN
--         -- TG_TABLE_NAME :name of the table that caused the trigger invocation
--         IF(TG_TABLE_NAME = 'fish_catch') THEN
--             --TG_OP : operation the trigger was fired
--             DELETE FROM angler_ranking;
--             INSERT INTO angler_ranking(angler_id, total_point)
--             (
--                 SELECT
--                     angler_id,
--                     SUM(point * count)
--                 FROM
--                     fish_catch
--                 GROUP BY
--                     angler_id
--             );
--             RETURN NEW;
--         END IF;
--     END;
-- $BODY$ LANGUAGE plpgsql VOLATILE COST 100;
-- ALTER FUNCTION angler_ranking_trigger_function() OWNER TO postgres;

DROP TRIGGER angler_ranking_trigger;
-- 新規作成トリガー
-- CREATE TRIGGER angler_ranking_trigger AFTER INSERT
--     ON  fish_catch FOR EACH ROW EXECUTE PROCEDURE angler_ranking_trigger_function();