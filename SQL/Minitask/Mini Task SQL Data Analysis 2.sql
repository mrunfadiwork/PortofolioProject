
-- 3. Tampilkan tabel berisi nama nama konsumen pada poin pertama yang memiliki spending di atas rata-rata
select customer_name, avg(sales) as average_revenue from orders
-- 1. Tentukan kota mana yang memiliki revenue tertinggi
where city = (select city
	from orders
	group by city
	order by sum(sales) desc
	limit 1)
group by customer_name
-- 2. Dari kota pada poin sebelumnya, hitung rata-rata spending per konsumen pada kota tersebut
having avg(sales) > (Select
	avg(sales)
	from orders
	where city = (
		select city
		from orders
		group by city
		order by sum(sales) desc
		limit 1
		)
	);



