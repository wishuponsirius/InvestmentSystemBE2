-- Runs second — Docker connects to investment_db automatically via POSTGRES_DB override
-- All tables and seed data go here

-- =========================
-- DROP TABLES (reverse order)
-- =========================
DROP TABLE IF EXISTS market_price_raw CASCADE;
DROP TABLE IF EXISTS asset_portfolio CASCADE;
DROP TABLE IF EXISTS exchange_rates CASCADE;
DROP TABLE IF EXISTS asset_class CASCADE;
DROP TABLE IF EXISTS unit_conversion CASCADE;
DROP TABLE IF EXISTS units CASCADE;
DROP TABLE IF EXISTS regions CASCADE;
DROP TABLE IF EXISTS data_sources CASCADE;
DROP TABLE IF EXISTS institutional_user CASCADE;
DROP TABLE IF EXISTS currencies CASCADE;

-- =========================
-- MASTER / DIMENSION TABLES
-- =========================

CREATE TABLE currencies (
  currency_code VARCHAR(10) PRIMARY KEY,
  is_active BOOLEAN DEFAULT true
);

CREATE TABLE institutional_user (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  avatar_url VARCHAR(512),
  org_name VARCHAR(255) NOT NULL,
  contact_email VARCHAR(255) NOT NULL,
  password VARCHAR(255) NOT NULL,
  activation_token_expiry TIMESTAMP,
  activation_token VARCHAR(255),
  is_active BOOLEAN DEFAULT false,
  role VARCHAR(50),
  create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  is_delete BOOLEAN DEFAULT false,
  update_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX uq_institutional_user_email
ON institutional_user (LOWER(contact_email));

CREATE TABLE units (
  unit_id SERIAL PRIMARY KEY,
  unit_name VARCHAR(100) NOT NULL,
  symbol VARCHAR(20) NOT NULL
);

CREATE TABLE regions (
  region_id SERIAL PRIMARY KEY,
  region_code VARCHAR(20) NOT NULL UNIQUE,
  region_name VARCHAR(100) NOT NULL,
  country_code VARCHAR(10) NOT NULL
);

CREATE TABLE data_sources (
  source_id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  country_code VARCHAR(10) NOT NULL
);

CREATE TABLE asset_class (
  asset_id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  is_active BOOLEAN DEFAULT true
);

-- =========================
-- RELATION TABLES
-- =========================

CREATE TABLE unit_conversion (
  from_unit_id INTEGER NOT NULL,
  to_unit_id INTEGER NOT NULL,
  factor NUMERIC(20,10) NOT NULL,
  PRIMARY KEY (from_unit_id, to_unit_id),
  FOREIGN KEY (from_unit_id) REFERENCES units(unit_id) ON DELETE CASCADE,
  FOREIGN KEY (to_unit_id) REFERENCES units(unit_id) ON DELETE CASCADE
);

CREATE TABLE exchange_rates (
  rate_id SERIAL PRIMARY KEY,
  currency_code VARCHAR(10) NOT NULL,
  buy_price NUMERIC(20,6) CHECK (buy_price > 0),
  transfer_price NUMERIC(20,6) CHECK (transfer_price > 0),
  sell_price NUMERIC(20,6) CHECK (sell_price > 0),
  source_id INTEGER,
  base_currency_code VARCHAR(10) NOT NULL DEFAULT 'VND',
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CHECK (
    buy_price IS NOT NULL
    OR sell_price IS NOT NULL
    OR transfer_price IS NOT NULL
  ),
  FOREIGN KEY (currency_code) REFERENCES currencies(currency_code),
  FOREIGN KEY (base_currency_code) REFERENCES currencies(currency_code),
  FOREIGN KEY (source_id) REFERENCES data_sources(source_id) ON DELETE SET NULL
);

CREATE TABLE market_price_raw (
  price_id SERIAL PRIMARY KEY,
  asset_id INTEGER NOT NULL,
  source_id INTEGER NOT NULL,
  region_id INTEGER NOT NULL,
  unit_id INTEGER NOT NULL,
  currency_code VARCHAR(10) NOT NULL,
  buy_price NUMERIC(20,6) CHECK (buy_price > 0),
  sell_price NUMERIC(20,6) CHECK (sell_price > 0),
  transfer_price NUMERIC(20,6) CHECK (transfer_price > 0),
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  spread NUMERIC(20,6) GENERATED ALWAYS AS (sell_price - buy_price) STORED,
  CHECK (
    buy_price IS NOT NULL
    OR sell_price IS NOT NULL
    OR transfer_price IS NOT NULL
  ),
  FOREIGN KEY (asset_id) REFERENCES asset_class(asset_id) ON DELETE CASCADE,
  FOREIGN KEY (source_id) REFERENCES data_sources(source_id) ON DELETE CASCADE,
  FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE,
  FOREIGN KEY (unit_id) REFERENCES units(unit_id),
  FOREIGN KEY (currency_code) REFERENCES currencies(currency_code)
);

CREATE UNIQUE INDEX uq_market_price_dedupe
ON market_price_raw (asset_id, source_id, region_id, unit_id, currency_code, timestamp);

CREATE UNIQUE INDEX uq_exchange_rates_dedupe
ON exchange_rates (currency_code, source_id, base_currency_code, timestamp);

CREATE TABLE asset_portfolio (
  portfolio_id SERIAL PRIMARY KEY,
  user_id UUID NOT NULL,
  asset_id INTEGER NOT NULL,
  quantity NUMERIC(20,10) NOT NULL CHECK (quantity > 0),
  unit_id INTEGER NOT NULL,
  entry_price NUMERIC(20,6),
  currency_code VARCHAR(10) DEFAULT 'VND',
  FOREIGN KEY (user_id) REFERENCES institutional_user(id) ON DELETE CASCADE,
  FOREIGN KEY (asset_id) REFERENCES asset_class(asset_id) ON DELETE CASCADE,
  FOREIGN KEY (unit_id) REFERENCES units(unit_id),
  FOREIGN KEY (currency_code) REFERENCES currencies(currency_code)
);

-- =========================
-- INDEXES
-- =========================
CREATE INDEX idx_market_price_asset ON market_price_raw(asset_id);
CREATE INDEX idx_market_price_region ON market_price_raw(region_id);
CREATE INDEX idx_market_price_timestamp ON market_price_raw(timestamp);
CREATE INDEX idx_exchange_rates_currency ON exchange_rates(currency_code);
CREATE INDEX idx_portfolio_user
ON asset_portfolio(user_id);
CREATE INDEX idx_portfolio_user_asset
ON asset_portfolio(user_id, asset_id);
-- =========================
-- SEED DATA
-- =========================

INSERT INTO currencies (currency_code) VALUES
('AUD'), ('CAD'), ('CHF'), ('CNY'), ('DKK'),
('EUR'), ('GBP'), ('HKD'), ('INR'), ('JPY'),
('KRW'), ('KWD'), ('MYR'), ('NOK'), ('RUB'),
('SEK'), ('SGD'), ('THB'), ('USD'), ('VND');

INSERT INTO asset_class (name) VALUES ('Gold'), ('Silver');

INSERT INTO regions (region_code, region_name, country_code) VALUES
('VN-HN', 'Hà Nội', 'VN'),
('VN-HCM', 'Hồ Chí Minh', 'VN'),
('VN-DNG', 'Đà Nẵng', 'VN'),
('VN-CT', 'Cần Thơ', 'VN'),
('VN-TN', 'Tây Nguyên', 'VN'),
('VN-DNB', 'Đông Nam Bộ', 'VN'),
('VN-ALL', 'Toàn Việt Nam', 'VN'),
('GLOBAL', 'Quốc Tế', 'GLB');

INSERT INTO units (unit_name, symbol) VALUES
('Lượng', 'lượng'),
('Chỉ', 'chỉ'),
('Gram', 'g'),
('Troy Ounce', 'oz'),
('Tael', 'tael'),
('Kilogram','kg');

INSERT INTO unit_conversion (from_unit_id, to_unit_id, factor) VALUES
(1,2,10),(2,1,0.1),
(1,3,37.5),(3,1,0.0266667),
(2,3,3.75),(3,2,0.266667),
(4,3,31.1034768),(3,4,0.0321507),
(5,3,37.7993642),(3,5,0.0264555);

INSERT INTO data_sources (name, country_code) VALUES
('CafeF', 'VN'),
('Kitcon', 'GLOBAL'),
('Vietcombank', 'VN');

ALTER TABLE asset_portfolio
ADD CONSTRAINT unique_user_asset
UNIQUE (user_id, asset_id);
