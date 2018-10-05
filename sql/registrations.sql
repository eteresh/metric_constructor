WITH user_registration AS (
    SELECT creation_time AS dt, hhid
    FROM snapshot2.hhuser
    WHERE (TO_DATE(creation_time) == ':YEAR-:MONTH-:DAY')
), users AS (
    SELECT IF(host = 'm.hh.ru', 'mhh', 'xhh') as platform,
        CAST(hhid AS BIGINT) AS hhid
    FROM default.access_log
    WHERE (year == ':YEAR' AND month == ':MONTH' AND day == ':DAY'
        AND user_agent != 'load-testing'
        AND cookies['hhuid'] != ''
        AND (cookies['hhrole'] IS NULL OR cookies['hhrole'] NOT IN ('employer', 'back_office_user'))
        AND host LIKE '%hh.ru' and host != 'api.hh.ru'
        AND LENGTH(hhuid) == 24
        AND CAST(hhid AS BIGINT) IS NOT NULL
    )
)
INSERT OVERWRITE TABLE hack_ab.registrations PARTITION(year=':YEAR', month=':MONTH', day=':DAY')
SELECT MAX(platform) AS platform, dt, user_registration.hhid AS uid
FROM user_registration
INNER JOIN users
ON (user_registration.hhid = users.hhid)
GROUP BY dt, user_registration.hhid;
