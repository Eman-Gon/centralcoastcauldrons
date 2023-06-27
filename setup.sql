CREATE OR REPLACE FUNCTION public.refresh_catalog()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
  shop_record shops%ROWTYPE;
BEGIN
  -- Fetch records from the "shops" table
  FOR shop_record IN SELECT * FROM shops LOOP
    INSERT INTO public.jobs(shop_id, job_type, tick_id)
    VALUES(shop_record.id, 'REFRESH_CATALOG', new.id);
  END LOOP;

  -- do modulo for barrel shopping
  FOR shop_record IN SELECT * FROM shops LOOP
    INSERT INTO public.jobs(shop_id, job_type, tick_id)
    VALUES(shop_record.id, 'PURCHASE_BARRELS', new.id);
  END LOOP;

  return new;
END;
$function$
;

CREATE TRIGGER on_insert
  AFTER INSERT ON public.ticks
  FOR EACH ROW
  EXECUTE PROCEDURE public.refresh_catalog();

DROP PROCEDURE catalog_for_shop;

CREATE OR REPLACE PROCEDURE purchase_from_shop(api_url text, api_key text, shop_id bigint, tick_id bigint, out error text)
LANGUAGE plpgsql
AS $fn$
DECLARE
  result http_response;
  url text;
  stack text;
  message text;
  cart_id text;
  catalog_purchase purchase_plans%ROWTYPE;
  gold int;
  amount_purchased int;
BEGIN
  -- GET CART ID
  BEGIN
    PERFORM http_set_curlopt('CURLOPT_TIMEOUT_MS', '10001');

    CALL generate_purchase_plans(1, shop_id, tick_id);

    result := http((
          'POST',
           api_url || 'carts/',
           ARRAY[http_header('access_token',api_key)],
           'application/json',
           '{"customer": "Bob To be Replaced"}'
        )::http_request);

    if result.status <> 200 then
      error := 'Error creating new cart with code: ' || result.status;
      return;
    end if;

    SELECT json_extract_path(result.content::json, 'cart_id') INTO cart_id;

    if cart_id is null then
      error := 'No cart id returned when trying to create cart.'
      return;
    end if;
  EXCEPTION WHEN OTHERS THEN
      GET STACKED DIAGNOSTICS stack = PG_EXCEPTION_CONTEXT, message = MESSAGE_TEXT;
      error := (message || stack);
      return;
  END;

  gold := 0;

  FOR catalog_purchase IN SELECT * FROM purchase_plans WHERE purchase_plans.shop_id = purchase_from_shop.shop_id AND purchase_plans.tick_id = purchase_from_shop.tick_id
  LOOP

    -- ADD first cart item
    BEGIN
      PERFORM http_set_curlopt('CURLOPT_TIMEOUT_MS', '10001');
      RAISE LOG 'API_URL %', api_url;
      RAISE LOG 'cart_id %', cart_id;
      RAISE LOG 'catalog_purchase %', catalog_purchase;
      url := api_url || 'carts/' || cart_id || '/items/' || catalog_purchase.sku;

      SELECT * INTO result 
       FROM http((
            'PUT',
            url,
            ARRAY[http_header('access_token',api_key)],
            'application/json',
            '{"quantity": ' || catalog_purchase.num_purchasing || '}'
          )::http_request);

      if result.status <> 200 then
        error := 'Error putting item in cart with code: ' || result.status;
      return;
      end if;
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS stack = PG_EXCEPTION_CONTEXT, message = MESSAGE_TEXT;
        error := (message || stack);
        return;
    END;

    insert into potion_ledger_items (shop_id, tick_id, quantity_changed, potion_type)
      values (shop_id, tick_id, -1 * catalog_purchase.num_purchasing, catalog_purchase.supplied_potion);
    gold := gold + catalog_purchase.num_purchasing * catalog_purchase.price;
  END LOOP;

  BEGIN
    PERFORM http_set_curlopt('CURLOPT_TIMEOUT_MS', '10001');
      SELECT * INTO result 
       FROM http((
            'POST',
            api_url || 'carts/' || cart_id || '/checkout',
            ARRAY[http_header('access_token',api_key)],
            'application/json',
            '{"payment": "string","gold_paid": ' || gold || '}'
          )::http_request);

      if result.status <> 200 then
        error := 'Error checking out cart with code: ' || result.status;
        return;
      end if;
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS stack = PG_EXCEPTION_CONTEXT, message = MESSAGE_TEXT;
        error := (message || stack);
        return;
    END;

  insert into gold_ledger_items (shop_id, tick_id, gold_changed)
    values (shop_id, tick_id, gold);
END;
$fn$;

CREATE OR REPLACE PROCEDURE catalog_for_shop(api_url text, shop_id bigint, tick_id bigint, out error text)
LANGUAGE plpgsql
AS $$
DECLARE
  result http_response;
  url text;
  stack text;
  message text;
BEGIN
  url := api_url || 'catalog/';
  BEGIN
    PERFORM http_set_curlopt('CURLOPT_TIMEOUT_MS', '10001');
    result := http_get(url);
  EXCEPTION WHEN OTHERS THEN
      GET STACKED DIAGNOSTICS stack = PG_EXCEPTION_CONTEXT, message = MESSAGE_TEXT;
      error := (message || stack);
      return;
  END;

  INSERT INTO http_responses (url, status, content, shop_id, tick_id)
  VALUES (url, result.status, result.content, shop_id, tick_id);
  COMMIT;

  BEGIN
  insert into catalog_items (sku, name, quantity, potion_type, tick_id, shop_id, price)
    select sku, name, quantity, potion_type, tick_id, shop_id, price
    from
    json_populate_recordset(null::record, result.content::json)
    AS
    (
        sku text,
        name text,
        quantity smallint,
        price smallint,
        potion_type vector(3)
    );
    EXCEPTION WHEN OTHERS THEN
      GET STACKED DIAGNOSTICS stack = PG_EXCEPTION_CONTEXT, message = MESSAGE_TEXT;
      error := (message || stack);
      return;
  END;

  INSERT INTO public.jobs(shop_id, job_type, tick_id)
  VALUES(shop_id, 'PURCHASE_POTIONS', tick_id);
END;
$$;

CREATE OR REPLACE PROCEDURE run_jobs()
LANGUAGE plpgsql
AS $$
DECLARE
  job jobs%ROWTYPE;
  shop shops%ROWTYPE;
  error_message text;
  counter integer := 0;
BEGIN
  while counter < 5 loop
    counter := counter + 1;
    raise log 'Counter %', counter;
    SELECT * INTO job FROM jobs WHERE success IS NULL ORDER BY created_at LIMIT 1;

    if not found then
      raise LOG 'No jobs to execute.';
      return;
    end if;

    SELECT * INTO shop FROM shops WHERE id = job.shop_id;

    error_message := null;

	  case 
		  when job.job_type = 'REFRESH_CATALOG' then
        CALL catalog_for_shop(shop.api_url, job.shop_id, job.tick_id, error_message);
      when job.job_type = 'PURCHASE_POTIONS' then
        CALL purchase_from_shop(shop.api_url, shop.api_key, job.shop_id, job.tick_id, error_message);
      WHEN job.job_type = 'PURCHASE_BARRELS' then
        CALL purchase_barrels(shop.api_url, shop.api_key, job.shop_id, job.tick_id, error_message);
      else
        error_message := ('Unknown job type: ' || job.job_type);
    end case;  
    
    if error_message is null then
      UPDATE jobs SET success = TRUE WHERE id = job.id;
    else
      UPDATE jobs SET success = FALSE, error = error_message where id = job.id;
    end if;
    COMMIT;
  end loop;
END;
$$;

CREATE EXTENSION vector;
DROP TABLE potion_ledger_items;

create table
  public.gold_ledger_items (
    id bigint generated by default as identity not null,
    created_at timestamp with time zone null default now(),
    shop_id bigint not null,
    tick_id bigint not null,
    gold_changed smallint not null,
    constraint gold_ledger_items_pkey primary key (id),
    constraint gold_ledger_items_shop_id_fkey foreign key (shop_id) references shops (id),
    constraint gold_ledger_items_tick_id_fkey foreign key (tick_id) references ticks (id)
  ) tablespace pg_default;


create table
  public.barrel_ledger_items (
    id bigint generated by default as identity not null,
    created_at timestamp with time zone null default now(),
    shop_id bigint not null,
    tick_id bigint not null,
    liters_changed smallint not null,
    potion_type vector(3) not null,
    constraint barrel_ledger_items_pkey primary key (id),
    constraint barrel_ledger_items_shop_id_fkey foreign key (shop_id) references shops (id),
    constraint barrel_ledger_items_tick_id_fkey foreign key (tick_id) references ticks (id)
  ) tablespace pg_default;

create table
  public.potion_ledger_items (
    id bigint generated by default as identity not null,
    created_at timestamp with time zone null default now(),
    shop_id bigint not null,
    tick_id bigint not null,
    quantity_changed smallint not null,
    potion_type vector(3) not null,
    constraint potion_ledger_items_pkey primary key (id),
    constraint potion_ledger_items_shop_id_fkey foreign key (shop_id) references shops (id),
    constraint potion_ledger_items_tick_id_fkey foreign key (tick_id) references ticks (id)
  ) tablespace pg_default;

  create table
  public.jobs (
    id bigint generated by default as identity not null,
    created_at timestamp with time zone null default now(),
    shop_id bigint null,
    job_type text null,
    success boolean null,
    error text null,
    tick_id bigint not null default '1'::bigint,
    constraint jobs_pkey primary key (id),
    constraint jobs_shop_id_fkey foreign key (shop_id) references shops (id)
  ) tablespace pg_default;

  DROP TABLE catalog_items;
  
  create table
  public.catalog_items (
    id bigint generated by default as identity not null,
    created_at timestamp with time zone null default now(),
    sku text null,
    name text null,
    quantity smallint not null,
    potion_type vector(3) not null,
    price smallint not null,
    tick_id bigint not null,
    shop_id bigint not null default '1'::bigint,
    constraint catalog_shop_id_fkey foreign key (shop_id) references shops (id),
    constraint catalog_tick_id_fkey foreign key (tick_id) references ticks (id)
  ) tablespace pg_default;

DROP TABLE barrel_catalog_items;

create table
  public.barrel_catalog_items (
    id bigint generated by default as identity not null,
    created_at timestamp with time zone null default now(),
    sku text not null,
    liters_per_barrel smallint not null,
    color text not null,
    potion_type vector(3) not null,
    price smallint not null,
    quantity smallint not null,
    constraint barrel_catalog_items_pkey primary key (id)
  ) tablespace pg_default;

TRUNCATE barrel_catalog_items;
INSERT INTO barrel_catalog_items
(sku, liters_per_barrel, color, potion_type, price, quantity)
VALUES 
('LARGE_RED_BARREL', 100, 'red'::text, '[100, 0, 0]', 50, 10),
('MEDIUM_RED_BARREL', 25, 'red'::text, '[100, 0, 0]', 25, 10),
('SMALL_RED_BARREL', 5, 'red'::text, '[100, 0, 0]', 10, 10);

  create table
  public.customers (
    id bigint generated by default as identity not null,
    created_at timestamp with time zone null default now(),
    customer_name text not null,
    favorite_shop_id bigint null, 
    constraint customers_pkey primary key (id),
    constraint favorite_shop_id_fkey foreign key (favorite_shop_id) references shops (id)
  ) tablespace pg_default;


  create table
  public.demand_plan (
    id bigint generated by default as identity not null,
    created_at timestamp with time zone null default now(),
    customer_id bigint not null,
    pickiness float8 not null,
    utility float8 not null,
    num_potions_to_buy smallint not null,
    potion_type vector(3) not null,
    constraint demand_plan_customer_id_fkey foreign key (customer_id) references customers (id)
  ) tablespace pg_default;

  create table
  public.http_responses (
    id bigint generated by default as identity not null,
    created_at timestamp with time zone null default now(),
    status integer null,
    content text null,
    url text not null,
    shop_id bigint null,
    tick_id bigint null,
    constraint http_responses_pkey primary key (id),
    constraint http_responses_shop_id_fkey foreign key (shop_id) references shops (id),
    constraint http_responses_tick_id_fkey foreign key (tick_id) references ticks (id)
  ) tablespace pg_default;

  create table
  public.shops (
    id bigint generated by default as identity not null,
    created_at timestamp with time zone null default now(),
    api_url text not null,
    shop_name text not null,
    student text null,
    api_key text null,
    section text null,
    constraint shops_pkey primary key (id)
  ) tablespace pg_default;

DROP TABLE purchase_plans;

 create table
  public.purchase_plans (
    id bigint generated by default as identity not null,
    created_at timestamp with time zone null default now(),
    expected_value double precision null,
    demanded_potion vector(3) null,
    supplied_potion vector(3) null,
    price smallint not null,
    sku text null,
    num_purchasing smallint null,
    shop_id bigint null,
    tick_id bigint null,
    customer_id bigint null,
    total_expected_value double precision null,
    constraint purchase_plans_pkey primary key (id),
    constraint purchase_plans_shop_id_fkey foreign key (shop_id) references shops (id),
    constraint purchase_plans_tick_id_fkey foreign key (tick_id) references ticks (id),
    constraint purchase_plans_customer_id_fkey foreign key (customer_id) references customers (id)
  ) tablespace pg_default; 

create table
  public.ticks (
    id bigint generated by default as identity not null,
    created_at timestamp with time zone null default now(),
    constraint ticks_pkey primary key (id)
  ) tablespace pg_default;

create trigger on_insert
after insert on ticks for each row
execute function refresh_catalog ();

CREATE OR REPLACE FUNCTION utility_curve(distance float8, steepness float8)
  RETURNS numeric
  LANGUAGE plpgsql
AS $$
declare
  window_width float8;
BEGIN
  window_width := 141.42 * (1-steepness);
  if distance > window_width then
    return 0;
  else 
    return (cos((distance*pi())/window_width)+1)/2;
  end if;
END;
$$;

CREATE OR REPLACE PROCEDURE generate_purchase_plans(customer_id bigint, shop_id bigint, tick_id bigint)
AS $$
DECLARE
  rows_inserted INTEGER;
BEGIN
  LOOP
    INSERT INTO purchase_plans (
      expected_value,
      demanded_potion,
      supplied_potion,
      sku,
      num_purchasing,
      price,
      total_expected_value,
      shop_id,
      tick_id,
      customer_id
    )
    WITH already_purchased_demand AS (
      SELECT
        demanded_potion,
        purchase_plans.customer_id,
        purchase_plans.tick_id,
        purchase_plans.shop_id,
        SUM(num_purchasing) AS total_purchased
      FROM
        purchase_plans
      GROUP BY
        demanded_potion,
        purchase_plans.customer_id,
        purchase_plans.tick_id,
        purchase_plans.shop_id
    ),
    already_purchased_supply AS (
      SELECT
        supplied_potion,
        purchase_plans.customer_id,
        purchase_plans.tick_id,
        purchase_plans.shop_id,
        SUM(num_purchasing) AS total_purchased
      FROM
        purchase_plans
      GROUP BY
        supplied_potion,
        purchase_plans.customer_id,
        purchase_plans.tick_id,
        purchase_plans.shop_id
    ),
    sub AS (
      SELECT
        utility_curve(ci.potion_type <-> dp.potion_type, dp.pickiness) * dp.utility - ci.price + random() * 2 AS expected_value,
        dp.potion_type AS demanded_potion,
        ci.potion_type AS supplied_potion,
        ci.sku,
        LEAST(ci.quantity - COALESCE(pp_supply.total_purchased, 0), dp.num_potions_to_buy - COALESCE(pp_demand.total_purchased, 0)) AS num_purchasing,
        ci.price
      FROM
        catalog_items AS ci
        CROSS JOIN demand_plan AS dp
        LEFT JOIN already_purchased_supply AS pp_supply ON pp_supply.shop_id = generate_purchase_plans.shop_id AND pp_supply.tick_id = generate_purchase_plans.tick_id AND pp_supply.supplied_potion = ci.potion_type
        LEFT JOIN already_purchased_demand AS pp_demand ON pp_demand.customer_id = dp.customer_id AND pp_demand.tick_id = generate_purchase_plans.tick_id AND pp_demand.demanded_potion = dp.potion_type
      WHERE
        ci.tick_id = generate_purchase_plans.tick_id
        AND ci.shop_id = generate_purchase_plans.shop_id
        AND dp.customer_id = generate_purchase_plans.customer_id
    )
    SELECT
      sub.*,
      expected_value * num_purchasing AS total_expected_value,
      generate_purchase_plans.shop_id, generate_purchase_plans.tick_id, generate_purchase_plans.customer_id
    FROM
      sub
    WHERE
      expected_value > 0
      AND num_purchasing > 0
    ORDER BY
      expected_value DESC
    LIMIT
      1
    RETURNING
      1
    INTO
      rows_inserted;
    
    RAISE LOG 'looping with %', rows_inserted;

    EXIT WHEN rows_inserted IS null;
  END LOOP;
END;
$$ LANGUAGE plpgsql;

DROP procedure purchase_barrels;

CREATE OR REPLACE PROCEDURE purchase_barrels(api_url text, api_key text, shop_id bigint, tick_id bigint, out error text)
LANGUAGE plpgsql
AS $fn$
DECLARE
  result http_response;
  url text;
  stack text;
  message text;
  cart_id text;
  barrel_catalog json;
  catalog_purchase purchase_plans%ROWTYPE;
  gold int;
  shop_gold int;
  amount_purchased int;
  invalid_skus text;
  quantity_check text;
BEGIN
  -- GET CART ID
  BEGIN
    PERFORM http_set_curlopt('CURLOPT_TIMEOUT_MS', '10001');
    SELECT json_agg(barrels) into barrel_catalog from 
      (select sku, liters_per_barrel, color, price, quantity from barrel_catalog_items) barrels;

    result := http((
          'POST',
           api_url || 'b2b/wholesaler/plan/',
           ARRAY[http_header('access_token',api_key)],
           'application/json',
           barrel_catalog
        )::http_request);

    if result.status <> 200 then
      error := 'Error retrieving wholesale plan: ' || result.status || '/' || result.content;
      return;
    end if;

  insert into barrel_purchases (sku, quantity, shop_id, tick_id)
    select sku, quantity, shop_id, tick_id
    from
    json_populate_recordset(null::record, result.content::json)
    AS
    (
        sku text,
        quantity smallint
    );
  EXCEPTION WHEN OTHERS THEN
      GET STACKED DIAGNOSTICS stack = PG_EXCEPTION_CONTEXT, message = MESSAGE_TEXT;
      error := (message || stack);
      return;
  END;

  -- Validate that has the money for barrels and that they exist.
  SELECT ARRAY_AGG(barrel_purchases.sku) INTO invalid_skus 
   FROM barrel_purchases
    LEFT join barrel_catalog_items ON barrel_catalog_items.sku = barrel_purchases.sku
    where barrel_purchases.shop_id = purchase_barrels.shop_id AND barrel_purchases.tick_id = purchase_barrels.tick_id and barrel_catalog_items.sku is null;

  if invalid_skus is not null then
    error := 'Purchasing skus that do not exist: ' || invalid_skus;
    return;
  end if;

  -- Validate has enough gold 
  SELECT SUM(price*barrel_purchases.quantity) INTO gold 
   FROM barrel_purchases
    join barrel_catalog_items ON barrel_catalog_items.sku = barrel_purchases.sku
    where barrel_purchases.shop_id = purchase_barrels.shop_id AND barrel_purchases.tick_id = purchase_barrels.tick_id;
  
  SELECT shop_gold.gold INTO shop_gold FROM shop_gold where shop_gold.shop_id = purchase_barrels.shop_id;

  if shop_gold < gold then
    error := 'Not enough gold, has ' || shop_gold || ' but requires ' || gold;
    return;
  end if;

  -- Validate that enough of the barrels exist to sell
    select json_agg(quantity_mismatch) into quantity_check from
    (
    SELECT barrel_purchases.sku, quantity_purchased, quantity  FROM (
    SELECT sku, SUM(quantity) quantity_purchased from barrel_purchases 
    WHERE barrel_purchases.shop_id = purchase_barrels.shop_id AND barrel_purchases.tick_id = purchase_barrels.tick_id
    group by sku) as barrel_purchases
    join barrel_catalog_items ON barrel_catalog_items.sku = barrel_purchases.sku
    WHERE barrel_purchases.quantity_purchased > barrel_catalog_items.quantity
    ) quantity_mismatch;

    if quantity_check is not null then
      error := 'Purchasing more barrels than exist: ' || quantity_check;
      return;
    end if;

  -- Purchase barrels by deducting money and adding barrels

    insert into gold_ledger_items (shop_id, tick_id, gold_changed)
      values (shop_id, tick_id, -gold);

    INSERT INTO barrel_ledger_items (liters_changed, potion_type, shop_id, tick_id)
      SELECT SUM(liters_per_barrel*barrel_purchases.quantity) liters_changed, barrel_catalog_items.potion_type, purchase_barrels.shop_id, purchase_barrels.tick_id
      FROM barrel_purchases
      JOIN barrel_catalog_items ON barrel_purchases.sku = barrel_catalog_items.sku
      WHERE barrel_purchases.shop_id = purchase_barrels.shop_id AND barrel_purchases.tick_id = purchase_barrels.tick_id
      GROUP BY potion_type, purchase_barrels.shop_id, purchase_barrels.tick_id;


    -- POST back to deliver barrels.

END;
$fn$;

CREATE VIEW shop_gold as
(SELECT shop_id, SUM(gold_changed) as gold FROM gold_ledger_items GROUP BY shop_id)

CREATE VIEW shop_potions as
(SELECT shop_id, potion_type, SUM(quantity_changed) as quantity from potion_ledger_items group by shop_id, potion_type)

CREATE VIEW shop_barrels as
(SELECT shop_id, potion_type, SUM(liters_changed) as liters from barrel_ledger_items group by shop_id, potion_type)
