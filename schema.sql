DROP TABLE IF EXISTS entries;
DROP TABLE IF EXISTS topics_table;

CREATE TABLE entries
(
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  "Paper"         TEXT    NOT NULL,
  "Year"          INTEGER NOT NULL,
  "Month"         TEXT    NOT NULL,
  "Person"        TEXT    NOT NULL,
  "Question_link" TEXT    NOT NULL,
  "Answer_link"   TEXT    NOT NULL
);

CREATE TABLE topics_table
(
  id    INT NOT NULL
    CONSTRAINT entries_id
    REFERENCES entries (id)
      ON DELETE CASCADE,
  value TEXT
);