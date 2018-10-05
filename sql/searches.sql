INSERT OVERWRITE TABLE hack_ab.searches PARTITION(year=':YEAR', month=':MONTH', day=':DAY')
SELECT IF(host LIKE 'm%', 'mhh', 'xhh') as platform, dt, CAST(hhid AS BIGINT) AS hhid
FROM default.access_log
WHERE (year == ':YEAR' AND month == ':MONTH' AND day == ':DAY'
    AND user_agent != 'load-testing'
    AND cookies['hhuid'] != ''
    AND host LIKE '%hh.ru' AND host NOT LIKE 'api%'
    AND LENGTH(hhuid) == 24
    AND CAST(hhid AS BIGINT) IS NOT NULL
    AND path = '/search/vacancy'
);
