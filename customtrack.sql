select
r.id,
rt.name as source,
u.bedrooms,
u.unit_code,
c.first_name,
c.last_name,
concat(c.first_name," " ,c.last_name) as full_name,
c.email_address,
c.address1,
c.city,
c.`state`,
c.zip,
checkin_date,
checkout_date,
r.created_at,
r.rent,
r.payment_total,
r.remaining_balance,
r.total,
datediff(r.created_at, current_date) as age,
datediff(r.checkout_date, r.checkin_date) as nights,
datediff(r.checkin_date, r.created_at) as booking_lead,
r.rent / (datediff(r.checkout_date, r.checkin_date)) as rent_per_night,
r.rent / (datediff(r.checkout_date, r.checkin_date)*u.bedrooms) as rent_per_bed_per_night,
r.created_by,
r.has_early_checkin,
r.cancelled_at,
r.status,
c.email_address
from reservation r
inner join reservation_types rt on r.type = rt.id
inner join units u on u.id = r.cabin_id
inner join customer c on c.id = r.customer_id