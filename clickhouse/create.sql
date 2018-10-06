CREATE TABLE actions (
    day Date,
    platform FixedString(3),
    dt String,
    uid Int32,
    action String
)
ENGINE MergeTree(day, (day, dt, uid), 8192);
