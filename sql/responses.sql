INSERT OVERWRITE TABLE hack_ab.responses PARTITION(year=':YEAR', month=':MONTH', day=':DAY')
SELECT
    IF (host LIKE 'm.%', 'mhh', 'xhh') AS platform,
    dt,
    CAST(hhid AS BIGINT) AS uid,
    CAST(query_all_values['vacancy_id'] AS BIGINT) AS vacancy_id
FROM default.access_log
WHERE (
    year = ':YEAR' AND month = ':MONTH' AND day = ':DAY'
    AND status BETWEEN 200 AND 399
    AND host NOT LIKE 'api.%'
    AND user_agent != 'load-testing'
    AND cookies['hhuid'] != ''
    AND LENGTH(hhuid) = 24
    AND http_method = 'POST'
    AND CAST(hhid AS BIGINT) IS NOT NULL
    AND (
        (
            path IN ('/applicant/vacancy_response/popup', '/applicant/vacancy_response')
            AND host NOT LIKE 'm.%'
        )
        OR (
            path = '/vacancy_response'
            AND host LIKE 'm.%'
        )
    )
    AND (cookies['hhrole'] IS NULL
        OR cookies['hhrole'] NOT IN ('employer', 'back_office_user')
    )
);
