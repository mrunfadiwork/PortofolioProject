-- Funnel performance report for “Organic” events in funnel_detail
-- Period: January 1 – December 31, 2024
-- 1. Total number of organic events per channel_source.
-- 2. Total unique order_id (“converted”) from organic events.
-- 3. Conversion rate = total_orders ÷ total_events × 100%.
-- This analysis is used to measure the effectiveness of organic channels.

with data as (
	select channel_source, count(channel_source) as Total_jumlah_event,
	count(distinct order_id) as total_converted_order
	from funnel_detail
	where event = 'Organic' AND funnel_date between '2024-01-01' and '2024-12-31'
	group by channel_source
)

select *, round((total_converted_order::numeric / nullif(Total_jumlah_event,0)) * 100,2)
from data;
