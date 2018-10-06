cat actions.csv | clickhouse-client --query="INSERT INTO actions FORMAT TSV"
