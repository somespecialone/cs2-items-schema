
CREATE TABLE types (
	id VARCHAR(60) NOT NULL, 
	name VARCHAR(16), 
	PRIMARY KEY (id)
)

;
CREATE TABLE qualities (
	id VARCHAR(60) NOT NULL, 
	name VARCHAR(16), 
	PRIMARY KEY (id)
)

;
CREATE TABLE tints (
	id SMALLINT NOT NULL, 
	name VARCHAR(16), 
	PRIMARY KEY (id)
)

;
CREATE TABLE musics (
	id SMALLINT NOT NULL, 
	name VARCHAR(255), 
	PRIMARY KEY (id)
)

;
CREATE TABLE rarities (
	id VARCHAR(60) NOT NULL, 
	`character` VARCHAR(16), 
	color VARCHAR(16) NOT NULL, 
	nonweapon VARCHAR(16) NOT NULL, 
	weapon VARCHAR(16) NOT NULL, 
	PRIMARY KEY (id)
)

;
CREATE TABLE tournament_events (
	id SMALLINT NOT NULL, 
	name VARCHAR(255), 
	short_name VARCHAR(255), 
	PRIMARY KEY (id)
)

;
CREATE TABLE tournament_teams (
	id SMALLINT NOT NULL, 
	tag VARCHAR(60), 
	geo VARCHAR(16), 
	PRIMARY KEY (id)
)

;
CREATE TABLE tournament_players (
	id BIGINT NOT NULL, 
	name VARCHAR(255), 
	geo VARCHAR(16), 
	PRIMARY KEY (id)
)

;
CREATE TABLE tournament_stages (
	id SMALLINT NOT NULL, 
	name VARCHAR(255), 
	PRIMARY KEY (id)
)

;
CREATE TABLE collections (
	id VARCHAR(60) NOT NULL, 
	name VARCHAR(255), 
	hidden SMALLINT, 
	PRIMARY KEY (id)
)

;
CREATE TABLE definitions (
	defindex SMALLINT NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	type VARCHAR(60), 
	quality VARCHAR(60), 
	rarity VARCHAR(60), 
	tradable SMALLINT, 
	PRIMARY KEY (defindex), 
	FOREIGN KEY(type) REFERENCES types (id), 
	FOREIGN KEY(quality) REFERENCES qualities (id), 
	FOREIGN KEY(rarity) REFERENCES rarities (id)
)

;
CREATE TABLE paints (
	paintindex SMALLINT NOT NULL, 
	name VARCHAR(60) NOT NULL, 
	wear_min FLOAT NOT NULL, 
	wear_max FLOAT NOT NULL, 
	rarity VARCHAR(60) NOT NULL, 
	PRIMARY KEY (paintindex), 
	FOREIGN KEY(rarity) REFERENCES rarities (id)
)

;
CREATE TABLE highlights (
	id SMALLINT NOT NULL, 
	`key` VARCHAR(255) NOT NULL, 
	event SMALLINT NOT NULL, 
	stage SMALLINT NOT NULL, 
	map VARCHAR(60) NOT NULL, 
	team0 SMALLINT NOT NULL, 
	team1 SMALLINT NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (`key`), 
	FOREIGN KEY(event) REFERENCES tournament_events (id), 
	FOREIGN KEY(stage) REFERENCES tournament_stages (id), 
	FOREIGN KEY(team0) REFERENCES tournament_teams (id), 
	FOREIGN KEY(team1) REFERENCES tournament_teams (id)
)

;
CREATE TABLE collection_unusual_sources (
	collection VARCHAR(60) NOT NULL, 
	quality VARCHAR(60) NOT NULL, 
	loot_list VARCHAR(255) NOT NULL, 
	PRIMARY KEY (collection, quality), 
	FOREIGN KEY(collection) REFERENCES collections (id), 
	FOREIGN KEY(quality) REFERENCES qualities (id)
)

;
CREATE TABLE sticker_kits (
	id SMALLINT NOT NULL, 
	name VARCHAR(60), 
	rarity VARCHAR(60), 
	kind VARCHAR(16) NOT NULL, 
	event SMALLINT, 
	team SMALLINT, 
	player BIGINT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(rarity) REFERENCES rarities (id), 
	FOREIGN KEY(event) REFERENCES tournament_events (id), 
	FOREIGN KEY(team) REFERENCES tournament_teams (id), 
	FOREIGN KEY(player) REFERENCES tournament_players (id)
)

;
CREATE TABLE items (
	id VARCHAR(16) NOT NULL, 
	def SMALLINT NOT NULL, 
	paint SMALLINT, 
	PRIMARY KEY (id), 
	CONSTRAINT uniq_paint_def UNIQUE (def, paint), 
	FOREIGN KEY(def) REFERENCES definitions (defindex), 
	FOREIGN KEY(paint) REFERENCES paints (paintindex)
)

;CREATE UNIQUE INDEX ix_paint_def ON items (def, paint);
CREATE TABLE charms (
	id SMALLINT NOT NULL, 
	name VARCHAR(255), 
	description TEXT, 
	rarity VARCHAR(60), 
	quality VARCHAR(60), 
	base SMALLINT, 
	highlight SMALLINT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(rarity) REFERENCES rarities (id), 
	FOREIGN KEY(quality) REFERENCES qualities (id), 
	FOREIGN KEY(base) REFERENCES charms (id), 
	FOREIGN KEY(highlight) REFERENCES highlights (id)
)

;
CREATE TABLE items_collections (
	item VARCHAR(16) NOT NULL, 
	collection VARCHAR(60) NOT NULL, 
	PRIMARY KEY (item, collection), 
	FOREIGN KEY(item) REFERENCES items (id), 
	FOREIGN KEY(collection) REFERENCES collections (id)
)

;
CREATE TABLE containers (
	defindex VARCHAR(16) NOT NULL, 
	associated VARCHAR(16), 
	kind VARCHAR(32) NOT NULL, 
	collection VARCHAR(60), 
	will_produce_stattrak SMALLINT, 
	PRIMARY KEY (defindex), 
	FOREIGN KEY(defindex) REFERENCES items (id), 
	FOREIGN KEY(associated) REFERENCES items (id), 
	FOREIGN KEY(collection) REFERENCES collections (id)
)

;
CREATE TABLE items_containers (
	item VARCHAR(16) NOT NULL, 
	container VARCHAR(16) NOT NULL, 
	PRIMARY KEY (item, container), 
	CONSTRAINT uniq_item_container UNIQUE (item, container), 
	FOREIGN KEY(item) REFERENCES items (id), 
	FOREIGN KEY(container) REFERENCES containers (defindex)
)

;CREATE UNIQUE INDEX idx_item_container ON items_containers (item, container);
CREATE TABLE musics_containers (
	music SMALLINT NOT NULL, 
	container VARCHAR(16) NOT NULL, 
	PRIMARY KEY (music, container), 
	CONSTRAINT uniq_music_container UNIQUE (music, container), 
	FOREIGN KEY(music) REFERENCES musics (id), 
	FOREIGN KEY(container) REFERENCES containers (defindex)
)

;CREATE UNIQUE INDEX idx_music_container ON musics_containers (music, container);
CREATE TABLE sticker_kits_containers (
	kit SMALLINT NOT NULL, 
	container VARCHAR(16) NOT NULL, 
	PRIMARY KEY (kit, container), 
	CONSTRAINT uniq_kit_container UNIQUE (kit, container), 
	FOREIGN KEY(kit) REFERENCES sticker_kits (id), 
	FOREIGN KEY(container) REFERENCES containers (defindex)
)

;CREATE UNIQUE INDEX idx_kit_container ON sticker_kits_containers (kit, container);
CREATE TABLE charms_containers (
	container VARCHAR(16) NOT NULL, 
	charm SMALLINT NOT NULL, 
	PRIMARY KEY (container, charm), 
	FOREIGN KEY(container) REFERENCES containers (defindex), 
	FOREIGN KEY(charm) REFERENCES charms (id)
)

;
CREATE TABLE container_highlight_charms (
	container VARCHAR(16) NOT NULL, 
	charm SMALLINT NOT NULL, 
	PRIMARY KEY (container, charm), 
	FOREIGN KEY(container) REFERENCES containers (defindex), 
	FOREIGN KEY(charm) REFERENCES charms (id)
)

;
