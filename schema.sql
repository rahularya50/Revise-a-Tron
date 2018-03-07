drop table if exists entries;
create table entries (
  id integer primary key autoincrement,
  Paper text not null,
  Year integer not null,
  Month text not null,
  Topics text not null,
  Person text not null,
  Question_link text not null,
  Answer_link text not null
);