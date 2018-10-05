CREATE TABLE hack_ab.responses (
    platform STRING,
    dt TIMESTAMP,
    uid BIGINT,
    vacancy_id BIGINT
)
PARTITIONED BY (
    year STRING,
    month STRING,
    day STRING
);

CREATE TABLE hack_ab.registrations (
    platform STRING,
    dt TIMESTAMP,
    uid BIGINT
)
PARTITIONED BY (
    year STRING,
    month STRING,
    day STRING
);

CREATE TABLE hack_ab.searches (
    platform STRING,
    dt TIMESTAMP,
    uid BIGINT
)
PARTITIONED BY (
    year STRING,
    month STRING,
    day STRING
);

DROP TABLE hack_ab.actions;
CREATE TABLE hack_ab.actions (
    platform STRING,
    dt TIMESTAMP,
    uid STRING,
    action STRING
)
PARTITIONED BY (
    year STRING,
    month STRING,
    day STRING
);
