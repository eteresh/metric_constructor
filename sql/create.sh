cat actions.csv | clickhouse-client --query="INSERT INTO actions FORMAT CSV"
cat registrations.csv | clickhouse-client --query="INSERT INTO actions FORMAT CSV"
cat searches.csv | clickhouse-client --query="INSERT INTO actions FORMAT CSV"
