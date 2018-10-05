CREATE TABLE actions (
    platform FixedString(3),
    dt String,
    uid Int32,
    action String
)
ENGINE MergeTree();
