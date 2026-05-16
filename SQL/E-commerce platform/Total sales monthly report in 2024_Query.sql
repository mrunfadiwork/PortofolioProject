--  Total Sales each month in year 2024 report
select extract(month from transaction_date) as bulan, round(SUM(total_paid)::numeric,2) as total_sales
from transaction_detail
where transaction_date between '2024-01-01' and '2024-12-31'
group by bulan
order by bulan asc;