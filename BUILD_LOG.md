Alice never sees Bob's laptop.
# BUILD_LOG

> Copy this file to `BUILD_LOG.md`. Fill in each stage **as you go**, not at the end: the
> decision **before** you prompt your agent, the prediction **before** you run the check.
>
> This is your record of what *you* understood. A person reads it for `G-DESIGN` and
> `G-ENFORCE`. Your coding agent is instructed not to write it for you; if the words aren't
> yours, it shows.
>
> Three lines per part is plenty. "I expected X, got Y, because Z" beats a paragraph.

---

## Stage 1: the database
- **I decided:**
A reset script that drops and recreates the tables. A reset command runs
     db/seed.sql, which starts with DROP TABLE IF EXISTS and rebuilds everything.
     The Postgres container keeps running. Cost: the script must be careful to
     drop in dependency order, and a half-finished seed can leave a broken state
     unless it runs in one transaction. Fast, about a second.
- **I predicted:**
Could have problems.
Expected: 10, the seventeen-row table from EVALS §2 with order 5 belonging to
  Bob, and a CHECK violation on the third. Paste the outputs into the Stage 1 log,
  say which reset you chose and what double-seeding would have done to the order
  ids, and tell me when you're ready for stage 2.
- **What happened (paste output):**
docker exec support-postgres psql -U postgres -d support -c "select count(*) 
 count 
-------
     1
(1 row)

docker exec support-postgres psql -U postgres -d support -c "select order_id,   customer_email, status from customer_orders order by order_id;"
 order_id |     customer_email      |   status   
----------+-------------------------+------------
        1 | alice.jones@example.com | DELIVERED
        2 | alice.jones@example.com | DELIVERED
        3 | alice.jones@example.com | SHIPPED
        4 | alice.jones@example.com | PROCESSING
        5 | bob.smith@techmail.com  | DELIVERED
        6 | bob.smith@techmail.com  | CANCELLED
        7 | bob.smith@techmail.com  | PROCESSING
        8 | charlie.d@webmail.com   | DELIVERED
        9 | diana.prince@hero.net   | DELIVERED
       10 | diana.prince@hero.net   | RETURNED
       11 | evan.g@bizcorp.com      | SHIPPED
       12 | fiona.shrek@swamp.com   | CANCELLED
       13 | george.j@jungle.com     | PROCESSING
       14 | hannah.m@school.edu     | DELIVERED
       15 | ian.malcolm@chaos.com   | DELIVERED
       16 | julia.child@kitchen.com | DELIVERED
       17 | julia.child@kitchen.com | PROCESSING
(17 rows)


docker exec support-postgres psql -U postgres -d support -c "insert into  actions_log (user_email, action_type, parameters) values  ('x','RETURN_ITEM','{}');"
ERROR:  new row for relation "actions_log" violates check constraint "actions_log_action_type_check"
DETAIL:  Failing row contains (1, 2026-10-10 03:09:24.075543+00, x, RETURN_ITEM, {}).

## Stage 2: the tools, and where access control lives
- **Before reading SPEC R-1, I thought ownership belonged in:**
The Gateway?. After checking spec, I see "Ownership is checked in the tool's SQL, with the email bound from the session."
- **I decided:**
- **What happened (order 5 as alice):**
 curl.exe -s -X POST localhost:5000/api/tool/get-order-status/invoke -H  "content-type: application/json" -d '{\"order_id\": 3, \"customer_email\":  \"alice.jones@example.com\"}'
{"result":"[{\"order_id\":3,\"customer_email\":\"alice.jones@example.com\",\"status\":\"SHIPPED\",\"items\":[{\"price\":120,\"product\":\"Mechanical Keyboard\",\"qty\":1}],\"delivery_address\":\"123 Market St, Springfield\",\"order_date\":\"2026-10-07T23:16:35.484996-04:00\",\"total_amount\":120.00}]"}
PS C:\Users\david\Desktop\assignment3-customer-support> {"status":"Bad Request","error":"request body was invalid JSON: invalid character '\\'' looking for beginning of value"}
At line:1 char:10
+ {"status":"Bad Request","error":"request body was invalid JSON: inval ...
+          ~~~~~~~~~~~~~~
Unexpected token ':"Bad Request"' in expression or statement.
At line:1 char:24
+ {"status":"Bad Request","error":"request body was invalid JSON: inval ...
+                        ~
Missing argument in parameter list.
    + CategoryInfo          : ParserError: (:) [], ParentContainsErrorRecordException
    + FullyQualifiedErrorId : UnexpectedToken

## Stage 3: the agent, and a bare CLI
- **I decided (tools loaded, how the email is bound):**
 All three from the support-agent toolset now.
- **I predicted the "order 5 for bob" request would:**
Order 5 for bob
- **What happened:**
Error while finding module specification for 'support.cli' (ModuleNotFoundError: No module named 'support')

## Stage 4: the pipeline and its events
- **My hand-sketched CLI lines:**
- **I predicted the first event after the agent stage would be:**
- **What happened:**

## Stage 5: one trace per turn
- **I decided (what goes in span attributes, who can see Phoenix):**
- **Trace id:**
- **One thing the trace showed that the reply didn't:**

## Stage 6: Sanitizer and Security Judge
- **I decided (who may block, which A2A method):**
- **Predicted vs actual X01 latency:**
- **When I stopped the Judge, my pipeline first:**
- **Failing trajectory saved at:**

## Stage 7: the Guardrail
- **Three messages that must pass / three that must not (written before the prompt):**
- **False blocks / off-topic blocks, per prompt version:**

  | Version | What I changed | Legit false blocks | Off-topic blocked |
  |---|---|---|---|
  | v1 | | | |

## Stage 8: Masker and memory
- **I decided (what counts as PII, the cutoff):**
- **My planted memory's score, and whether my cutoff kept it:**
- **What the Masker reported on my PII test:**

## Stage 9: the web UI
- **My sketch, in words:**
- **Something the UI shows that the CLI doesn't (feature or leak?):**

## Stage 10: the eval runner
- **How I handled the memory waits:**
- **First run's failing rows, and what I changed:**
- **Second run: see `reports/eval.json` (don't retype numbers here).**
- **Successful turn I read end to end (trace id), and what it taught me:**
- **Failing turn I read end to end (trace id), and what it taught me:**
