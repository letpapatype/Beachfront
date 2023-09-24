SELECT
u.unit_code,
u.bedrooms,
ra.date,
ra.rate,
ra.rate / u.bedrooms as per_bed_price,
ra.min_stay
from
    rates_daily ra
    inner join units u on u.id = ra.unit_id