-- No. 1 Prove that one customer name only has one customer ID!


select customer_name, count (distinct customer_id) as "Berapa costumer ID" from orders
group by customer_name
having count(distinct customer_id) > 1;



-- No. 2 Which product (product_name) is the best-selling by quantity?

select product_name, COUNT(product_name) AS total_produk 
FROM orders
GROUP BY product_name
having count(product_name) = (select
	max(total_produk)
	from (
		select product_name,
		count(product_name) as total_produk
		from orders
		group by product_name
	)
)
;

-- optional
select product_name, count(product_name) as total_produk
from orders
group by product_name
order by total_produk desc
limit 1;



-- No. 3 Which product caused the greatest loss during 2017?

SELECT product_name, SUM(profit) AS kerugian
FROM orders
WHERE order_date BETWEEN '2017-01-01' AND '2017-12-31'
GROUP BY product_name
HAVING SUM(profit) = (
    SELECT MIN(x)
    FROM (
        SELECT SUM(profit) AS x
        FROM orders
        WHERE order_date BETWEEN '2017-01-01' AND '2017-12-31'
        GROUP BY product_name
    ) AS data
);

-- Optional
select product_name, sum(profit) as Kerugian
from orders
where order_date BETWEEN '2017-01-01' AND '2017-12-31'
group by product_name
order by kerugian asc
limit 1;