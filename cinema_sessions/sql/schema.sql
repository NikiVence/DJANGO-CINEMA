PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS halls (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    hall_type TEXT NOT NULL CHECK (hall_type IN ('стандартный', 'комфорт', 'VIP'))
);
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE CHECK (slug <> 'statistics'),
    show_type TEXT NOT NULL CHECK (show_type IN ('утренний', 'дневной', 'вечерний')),
    show_date TEXT NOT NULL,
    duration INTEGER NOT NULL CHECK (duration > 0),
    tickets INTEGER NOT NULL CHECK (tickets >= 0),
    status TEXT NOT NULL CHECK (status IN ('запланирован', 'идёт', 'завершён')),
    hall_id INTEGER NOT NULL REFERENCES halls(id)
);
CREATE INDEX IF NOT EXISTS sessions_hall_idx ON sessions(hall_id);
CREATE INDEX IF NOT EXISTS sessions_date_idx ON sessions(show_date);
