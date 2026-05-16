
-- Please display the sales volume (quantity sold) per category for each year from 2020 to 2024.
select extract(year from b.order_date) as tahun, a.category, sum(b.quantity) as quantity from product_detail a
inner join order_detail b
on a.sku_id = b.sku_id
where b.order_date between '2020-01-01 00:00:00' and '2024-12-31 23:59:59'
group by a.category, tahun
order by tahun;