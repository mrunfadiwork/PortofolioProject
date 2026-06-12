-- Begineer
-- 1. Show the 5 most expensive trips by total_fare
select trip_id, total_fare from trips
where status = 'completed'
order by total_fare desc
limit 5;

-- 2. How many drivers joined after January 1, 2023?
select count(driver_id) as total_driver from drivers
where join_date >= '2023-01-01';

-- 3. How many trips were paid by cash?
select count(*) as cash_Trips from trips
where payment_method = 'cash' AND status = 'completed';

-- 4. List all zones of type 'airport'
select zone_name , zone_type from locations
where zone_type = 'airport';

-- 5. List the first 10 trips ordered by requested_at
select * from trips
order by requested_at asc
limit 10;

-- Intermediate
-- 1.Find the top 5 drivers by total number of completed trips
select b.driver_id, count(a.status) as Completed_trips from trips a
join drivers b on a.driver_id = b.driver_id
where status = 'completed'
group by b.driver_id
order by Completed_trips desc
limit 5;

-- 2. What is the total revenue (sum of total_fare) per month?
select EXTRACT(YEAR FROM completed_at) AS year, EXTRACT(MONTH FROM completed_at) AS month, sum(total_fare) as total_revenue from trips
where status = 'completed'
group by year, month
order by year, month asc ;

-- 3. Which pickup zone generates the most revenue?
with zone_revenue as(
	select b.zone_type as zone, sum(a.total_fare) as revenue from trips a
	join locations b on a.pickup_location_id = b.location_id
	group by zone)

SELECT zone, revenue
FROM zone_revenue
WHERE revenue = (
    SELECT MAX(revenue)
    FROM zone_revenue
);

-- 4. What percentage of trips were cancelled?
with trip_summary as (
select count(*) as total_trips, 
	sum(
		case
			when status = 'cancelled' then 1
		else 0
	end)
	as cancelled_flag
from trips
)

select round((cancelled_flag * 100)/total_trips,2) as Percentage_cancelled from trip_summary;

-- 5. Find the average trip duration per zone_type
select b.zone_type as zone, round(avg(a.duration_mins),2) from trips a
join locations b
on a.pickup_location_id = b.location_id
group by zone
;

-- 6. What is the average wait time (minutes between requested_at and started_at) per city
select b.city, 
	round(avg(extract(epoch from(a.started_at - a.requested_at)) / 60 ),2) as average_wait_time
	from trips a join locations b on a.pickup_location_id = b.location_id
group by city;

-- 7. Find drivers who have both completed trips and cancellations in the same month
with driver_completed_trips as(
	select driver_id, date_trunc('month', requested_at) as trip_month
	from trips
	where status = 'completed'
),

driver_cancelled_trips as(
	select driver_id, date_trunc('month', requested_at) as trip_month
	from trips
	where status = 'cancelled'

)

select distinct a.driver_id, a.trip_month from driver_completed_trips a join driver_cancelled_trips b
on a.driver_id = b.driver_id and
a.trip_month = b.trip_month
;

-- 8. Which zone pair (pickup → dropoff) is the most frequent route?
select b.zone_type as location_pickup, c.zone_type as location_dropoff, count(*) as total_trips from trips a
join locations b on a.pickup_location_id = b.location_id
join locations c on a.dropoff_location_id = c.location_id
group by location_pickup, location_dropoff
order by total_trips desc
;

-- Advanced

-- 1.  Rank drivers by total revenue generated (use RANK window function)
with Total_revenue_driver as (
	Select b.driver_id, c.name,
	sum(a.total_fare) as total_revenue from trips a
	join drivers b
	on a.driver_id = b. driver_id
	join users c
	on b.user_id = c.user_id
	where a.status = 'completed'
	group by b.driver_id, c.name
	)

select driver_id, name, total_revenue, rank() over(order by total_revenue desc) as revenue_rank
from Total_revenue_driver;



-- 2. Show month-over-month revenue growth rate as a percentage
with monthly_revenue as (
	select EXTRACT(YEAR FROM completed_at) AS year,
	EXTRACT(MONTH FROM completed_at)AS month,
	sum(total_fare) as revenue
	from trips
	where status = 'completed'
	group by year, month
	)

select *,
	round(
		(
		(revenue - lag(revenue) over (order by year, month)) / lag(revenue) over (order by year, month) * 100)::numeric
	,2) as Revenue_growth
from monthly_Revenue
order by year,month asc;


-- 3. Build a full driver performance summary: total trips, avg rating, total revenue, cancellation rate, avg trip duration
with total_trip as (select driver_id, count(completed_at) as total_trips from trips
where status = 'completed'
group by driver_id),

avg_rating as (select b.driver_id, round(avg(a.rating),2) as Average_rating from reviews a 
join trips b on a.trip_id = b.trip_id
where status = 'completed'
group by b.driver_id),

total_revenue as (select driver_id, sum(total_fare) as total_revenues from trips
where status = 'completed'
group by driver_id),

cancel_rate as (select driver_id,
	round(
		sum(
			case
				when status = 'cancelled' then 1
				else 0
			end
		)::numeric
		/ count(*) * 100,2
	) as cancellation_rate
from trips
group by driver_id),

average_trip_duration as (select driver_id, round(avg(duration_mins),2) as avg_trip_duration from trips
where status = 'completed'
group by driver_id)

select a.driver_id, a.total_trips, b.Average_rating, c.total_revenues, d.cancellation_rate, e.avg_trip_duration
from total_trip a
join avg_rating b on a.driver_id = b.driver_id
join total_revenue c on a.driver_id = c.driver_id
join cancel_rate d on a.driver_id = d.driver_id
join average_trip_duration e on a.driver_id = e.driver_id;

