
CREATE TABLE types (
	id SMALLINT NOT NULL, 
	name VARCHAR(16) NULL, 
	PRIMARY KEY (id)
)

;
CREATE TABLE origins (
	id SMALLINT NOT NULL, 
	name VARCHAR(30) NULL, 
	PRIMARY KEY (id)
)

;
CREATE TABLE qualities (
	id SMALLINT NOT NULL, 
	name VARCHAR(16) NULL, 
	PRIMARY KEY (id)
)

;
CREATE TABLE phases (
	id SMALLINT NOT NULL, 
	name VARCHAR(16) NULL, 
	PRIMARY KEY (id)
)

;
CREATE TABLE tints (
	id SMALLINT NOT NULL, 
	name VARCHAR(16) NULL, 
	PRIMARY KEY (id)
)

;
CREATE TABLE musics (
	id SMALLINT NOT NULL, 
	name VARCHAR(16) NULL, 
	PRIMARY KEY (id)
)

;
CREATE TABLE rarities (
	id SMALLINT NOT NULL, 
	character VARCHAR(16) NULL, 
	color VARCHAR(16) NOT NULL, 
	nonweapon VARCHAR(16) NOT NULL, 
	weapon VARCHAR(16) NOT NULL, 
	PRIMARY KEY (id)
)

;
CREATE TABLE wears (
	name VARCHAR(30) NOT NULL, 
	[from] FLOAT NOT NULL, 
	[to] FLOAT NOT NULL, 
	PRIMARY KEY (name)
)

;
CREATE TABLE definitions (
	defindex SMALLINT NOT NULL, 
	name VARCHAR(60) NOT NULL, 
	type SMALLINT NOT NULL, 
	quality SMALLINT NULL, 
	rarity SMALLINT NULL, 
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
	rarity SMALLINT NOT NULL, 
	phase SMALLINT NULL, 
	PRIMARY KEY (paintindex), 
	FOREIGN KEY(rarity) REFERENCES rarities (id), 
	FOREIGN KEY(phase) REFERENCES phases (id)
)

;
CREATE TABLE sticker_kits (
	id SMALLINT NOT NULL, 
	name VARCHAR(60) NOT NULL, 
	rarity SMALLINT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(rarity) REFERENCES rarities (id)
)

;
CREATE TABLE items (
	id VARCHAR(16) NOT NULL, 
	def SMALLINT NOT NULL, 
	paint SMALLINT NULL, 
	image VARCHAR(255) NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uniq_paint_def UNIQUE (def, paint), 
	FOREIGN KEY(def) REFERENCES definitions (defindex), 
	FOREIGN KEY(paint) REFERENCES paints (paintindex)
)

;CREATE UNIQUE INDEX ix_paint_def ON items (def, paint);
CREATE TABLE containers (
	defindex SMALLINT NOT NULL, 
	associated SMALLINT NULL, 
	[set] VARCHAR(60) NULL, 
	PRIMARY KEY (defindex), 
	FOREIGN KEY(defindex) REFERENCES items (id), 
	FOREIGN KEY(associated) REFERENCES items (id)
)

;
CREATE TABLE sticker_kit_containers (
	defindex SMALLINT NOT NULL, 
	PRIMARY KEY (defindex), 
	FOREIGN KEY(defindex) REFERENCES items (id)
)

;
CREATE TABLE music_kits (
	defindex SMALLINT NOT NULL, 
	PRIMARY KEY (defindex), 
	FOREIGN KEY(defindex) REFERENCES items (id)
)

;
CREATE TABLE items_containers (
	item VARCHAR(16) NOT NULL, 
	container SMALLINT NOT NULL, 
	PRIMARY KEY (item, container), 
	CONSTRAINT uniq_item_container UNIQUE (item, container), 
	FOREIGN KEY(item) REFERENCES items (id), 
	FOREIGN KEY(container) REFERENCES containers (defindex)
)

;CREATE UNIQUE INDEX idx_item_container ON items_containers (item, container);
CREATE TABLE musics_music_kits (
	music SMALLINT NOT NULL, 
	container SMALLINT NOT NULL, 
	PRIMARY KEY (music, container), 
	CONSTRAINT uniq_music_container UNIQUE (music, container), 
	FOREIGN KEY(music) REFERENCES musics (id), 
	FOREIGN KEY(container) REFERENCES music_kits (defindex)
)

;CREATE UNIQUE INDEX idx_music_container ON musics_music_kits (music, container);
CREATE TABLE sticker_kits_containers (
	kit SMALLINT NOT NULL, 
	container SMALLINT NOT NULL, 
	PRIMARY KEY (kit, container), 
	CONSTRAINT uniq_kit_container UNIQUE (kit, container), 
	FOREIGN KEY(kit) REFERENCES sticker_kits (id), 
	FOREIGN KEY(container) REFERENCES sticker_kit_containers (defindex)
)

;CREATE UNIQUE INDEX idx_kit_container ON sticker_kits_containers (kit, container);
