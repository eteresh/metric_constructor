INSERT OVERWRITE TABLE hack_ab.actions PARTITION(year=':YEAR', month=':MONTH', day=':DAY')
SELECT platform, dt, uid, 'response' AS action
FROM hack_ab.responses
WHERE (year=':YEAR' AND month=':MONTH' AND day=':DAY');
