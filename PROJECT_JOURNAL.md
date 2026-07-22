# Project Journal — Faker Data Generation Project

This is a reconstruction of everything that happened in this project, built from git
history (`git log`, `git show`, `git diff`) plus the current uncommitted working-tree
state as of 2026-07-21. Use it as a build log if you want to recreate the project from
scratch, and as a punch list of things to fix along the way instead of repeating them.

## 1. What this project is

A learning project that uses **Dagster** (an orchestration/asset framework) to generate
fake e-commerce data with **Faker**, land it as CSVs, and load it into a **DuckDB**
database as queryable tables. It follows the shape of Dagster's official project
scaffold (`dg` / `dagster-dg-cli`), which is why the folder layout matches Dagster's
"Getting Started" tutorial structure almost exactly.

Two datasets are generated:
- **Products** — product name, brand, SKU, price, order ID, description (via the
  `faker_ecommerce` provider on top of Faker).
- **Customers** — name, email, phone, address (via Faker's built-in providers).

## 2. Repository layout

There are actually **two nested git repositories** here, and this is worth understanding
before you recreate anything:

```
Faker Project/                          <- outer repo (git, no remote)
└── faker-data-generation-project/      <- inner repo (has its own .git, own GitHub remote)
```

- The **outer** repo (`Faker Project/`) has one commit, "update to date code", and its
  only tracked entry is the inner folder — but there is **no `.gitmodules` file**. That
  means this was never registered as a real git submodule; the inner `.git` directory
  was just present when `git add` ran on the outer repo, so git silently recorded it as
  a "gitlink" (a commit-pointer entry) instead of walking into it. This is why
  `git status` in the outer repo shows the inner project as `modified` with "new
  commits, modified content, untracked content" — git is comparing the *pointer* commit
  it recorded against whatever HEAD the inner repo is actually on now, plus flagging
  that the inner repo has its own uncommitted changes.
  - **If you recreate this**: either run `git submodule add <url> faker-data-generation-project`
    properly (which creates `.gitmodules` and tracks it as an intentional submodule), or
    don't nest the repos at all — just make the inner folder the top-level project. The
    current setup works but is accidental and confusing to `git status`.
- The **inner** repo (`faker-data-generation-project/`) is the real project and has a
  GitHub remote: `https://github.com/TundeRahman/faker-data-generation-project.git`.
  All the interesting history lives here.

## 3. Tech stack

From `pyproject.toml` and `uv.lock`:

| Package | Version | Role |
|---|---|---|
| `dagster` | 1.13.14 | Orchestration framework — assets, jobs, schedules |
| `dagster-dg-cli` | (dev) | The `dg` CLI used to scaffold/run the project |
| `dagster-webserver` | (dev) | Local Dagster UI (`dg dev`, http://localhost:3000) |
| `faker` | 40.31.0 | Fake data generation |
| `faker-ecommerce-provider` | 1.2.0 | Adds `product_name`, `brand_name`, `sku`, `price`, `order_id`, `product_description` to Faker |
| `duckdb` / `dagster-duckdb` / `dagster-duckdb-pandas` | latest | Embedded analytical database + Dagster resource wrapper |
| `pandas` | 2.2.3 | DataFrame handling before writing CSV/loading DuckDB |
| `numpy` | 2.2.6 | Pandas dependency, pinned explicitly |
| `ipykernel` | (dev) | Notebook exploration (`data/raw/*.ipynb`) |

Package/environment manager: **uv** (`uv sync`, `uv.lock` committed). Project scaffolding
convention: **`dg`**, Dagster's own project CLI (`[tool.dg]` section in `pyproject.toml`).

## 4. Timeline — what happened, commit by commit

### Commit 1 — `e909955` "initial commit" (2026-07-20, 10:18)
Scaffolded via the Dagster `dg` project template. At this point:
- `constants.py` had one path: `EXTRACTED_DATA_FILE_PATH = "data/raw/extracted_data.csv"`.
- `data_extraction.py` defined **one** asset, `generate_personnel_data`, that used
  `Faker()` + `faker_ecommerce.EcommerceProvider` to generate 20,000 fake products
  (name, brand, SKU, price, timestamp — no `order_id`/`description` yet) and wrote them
  to `extracted_data.csv`.
- `jobs.py` defined `extracted_data_job` selecting the `generate_personnel_data` asset.
- `schedules.py` scheduled that job at `0/5 * * * *` (every 5 minutes).
- `resources.py` pointed the DuckDB resource at `data/staging/data.duckdb`.
- Also committed at this point: a full `.tmp_dagster_home__w4f4frk/` directory —
  Dagster's local run-history SQLite database and hundreds of individual per-run `.db`
  files. **This is Dagster's local instance state, not project source** — it's
  regenerated automatically every time you run `dg dev` and should be gitignored (see
  §6, Known Issues).

### Commit 2 — `3a3556d` "removal of faker module from pyproject.toml file per AI's recommendation" (2026-07-20, 11:03)
A one-line change: removed `"faker-ecommerce-provider==1.2.0"` from the `dependencies`
list in `pyproject.toml`. **The code still imports it** (`from faker_ecommerce import
EcommerceProvider` in `data_extraction.py`), and `uv.lock` still lists
`faker-ecommerce-provider` as a resolved dependency of the project. This is a
self-contradicting change — see Known Issues §6 for why it "works" today anyway and
what breaks if you don't fix it before recreating.

### Commit 3 — `5a9bcdc` "update to date code" (2026-07-20, 20:30)
The big functional commit. Changes:
- **`constants.py`**: added `CUSTOMER_DATA_FILE_PATH = "data/raw/customer_data.csv"`.
- **`data_extraction.py`**:
  - Renamed `generate_personnel_data` → `generate_product_data`, and extended the
    product record with `order_id` and `product_description` fields (using more of the
    `faker_ecommerce` provider's surface area).
  - Added a new asset, `generate_customer_data`, generating 20,000 fake customers
    (name, email, phone, address) via plain Faker, written to `customer_data.csv`.
  - Added a new asset, `product_dataset`, depending on `generate_personnel_data` (this
    dependency string was **not** updated to match the rename — see Known Issues §6) —
    it loads `extracted_data.csv` into a DuckDB table called `products` using:
    ```sql
    create or replace table products as (
      select
        'product_name', 'brand_name', 'SKU', 'price',
        'order_id', 'product_description', 'data_generated_at'
      from '{constants.EXTRACTED_DATA_FILE_PATH}'
    );
    ```
    **Bug**: those are quoted string *literals*, not column references, so every row of
    the resulting `products` table would just contain the literal text
    `"product_name"`, `"brand_name"`, etc. repeated for every row, not the actual CSV
    data. (Fixed later — see §5, uncommitted changes.)
  - Left a commented-out draft asset (`insert_tables`) referencing an
    `insert_table_query` list that didn't exist yet.
- **`sql_queries.py`** (new file): defined `product_table_insert`, an `INSERT INTO
  products (...) SELECT ... FROM '{constants.EXTRACTED_DATA_FILE_PATH}'` string —
  scaffolding for the commented-out `insert_tables` asset. Note this string embeds
  `{constants.EXTRACTED_DATA_FILE_PATH}` as literal text; it was never passed through an
  f-string, so it would need `.format()` or an f-string prefix to actually interpolate.
- **`resources.py`**: changed the DuckDB resource path from `data/staging/data.duckdb`
  to `data/raw/database.duckdb` — consolidating the database next to the raw CSVs
  instead of a separate staging folder.
- **`jobs.py`**: renamed `extracted_data_job` → `generate_product_data_job` (asset
  selection still targeted `generate_personnel_data` at this point, so it was already
  stale relative to the rename in `data_extraction.py`; see Known Issues §6).
- **`schedules.py`**: renamed the schedule accordingly and changed the cron schedule
  from every 5 minutes (`0/5 * * * *`) to **every minute** (`* * * * *`).
- Also committed: `data/raw/customer_data.csv` (40,000 lines), `data/raw/database.duckdb`
  (the actual DuckDB file), regenerated `extracted_data.csv`, and two Jupyter notebooks
  used purely for manual verification:
  - `data/raw/extracted_data_table.ipynb` — reads both CSVs directly with
    `duckdb.read_csv(...)` to eyeball the generated data.
  - `data/raw/product_dataset.ipynb` — connects to `database.duckdb` read-only and runs
    `SELECT * FROM products` to confirm the DuckDB load worked.

## 5. Current uncommitted changes (working tree, as of 2026-07-21)

These fixes exist locally but have **not** been committed yet:
- `data_extraction.py`:
  - `product_dataset`'s `deps=[...]` now correctly points at `"generate_product_data"`
    (matching the commit-3 rename).
  - The broken literal-string `SELECT` was replaced with a correct
    `select * from read_csv_auto('{constants.EXTRACTED_DATA_FILE_PATH}')`, which
    actually reads the CSV's real columns.
  - The commented-out `insert_tables` draft asset is still present (still commented
    out).
- `jobs.py`: the asset selection now correctly targets `"generate_product_data"` instead
  of the stale `"generate_personnel_data"`. (The Python variable is still *named*
  `generate_personnel_data` even though it now selects `generate_product_data` — a
  naming leftover, not a bug, but worth renaming for clarity.)
- `sql_queries.py`: added `insert_table_query = [product_table_insert]` — the list the
  commented-out `insert_tables` asset expects, but the asset itself is still disabled.
- `schedules.py`: whitespace/import path already matched the commit-3 rename here — no
  further change.
- `data/raw/*.csv`, `database.duckdb`, and both notebooks show as modified simply
  because re-running `generate_product_data`/`generate_customer_data`/`product_dataset`
  regenerates fresh fake data and a fresh timestamp every time (this is expected,
  not a bug — Faker output is random per run).
- New untracked `.tmp_dagster_home_*` directories — more disposable local Dagster
  instance state from additional `dg dev` runs (see §6).

**None of this is committed.** If you want today's fixes preserved before doing anything
else, commit them first.

## 6. Known issues / gotchas to fix when recreating

1. **Dagster's local run-history directories are committed to git.**
   `.tmp_dagster_home__w4f4frk/` (and the newer, untracked `.tmp_dagster_home_*` dirs)
   are Dagster's `DAGSTER_HOME`-equivalent scratch space — SQLite run databases created
   automatically by `dg dev`. They contain no project logic, churn on every run, and
   bloat the repo (hundreds of small binary `.db` files). Add `.tmp_dagster_home*/` to
   `.gitignore` and remove the already-committed copy with `git rm -r --cached`.

2. **`faker-ecommerce-provider` was removed from `pyproject.toml` but the code still
   imports it, and `uv.lock` still resolves it.** The import currently works only
   because the package is still physically installed in the `.venv` (or still present
   in the stale lock resolution) from before the removal commit. A completely fresh
   `uv sync` on a clean checkout could either (a) silently keep working if uv doesn't
   invalidate the lock, or (b) fail on `import faker_ecommerce` once the environment is
   truly rebuilt from a pyproject.toml that no longer declares it. **Fix**: either
   re-add `"faker-ecommerce-provider==1.2.0"` to `dependencies` (it's actually used), or
   remove the `faker_ecommerce`/`EcommerceProvider` usage from `data_extraction.py` if
   you intend to drop it — don't leave the two out of sync.

3. **Naming drift between assets, jobs, and dependency strings.** Over the three
   commits, the core asset was renamed `generate_personnel_data` → `generate_product_data`,
   but `jobs.py`'s asset-selection string and `data_extraction.py`'s `deps=[...]` string
   lagged behind for a while (fixed only in the uncommitted working tree — see §5).
   Because Dagster resolves `deps=["some_string"]` and `AssetSelection.assets([...])`
   by string name at load time, a stale string doesn't raise a Python error — it just
   silently fails to find the asset or creates a dangling dependency edge. **Lesson**:
   when renaming a `@dg.asset` function, grep the whole `defs/` folder for the old name
   (job selections, `deps=[...]`, schedules) rather than relying on Python to catch it.

4. **The `product_dataset` SQL bug (now fixed locally, not yet committed).** As
   originally committed, `create or replace table products as (select 'product_name',
   'brand_name', ... from '...')` used quoted literals instead of column references, so
   the loaded DuckDB table did not actually contain the CSV's data — every row repeated
   the same 7 literal strings. The working-tree fix (`select * from
   read_csv_auto(...)`) is correct; make sure it gets committed.

5. **`sql_queries.py`'s `product_table_insert` string never interpolates.** It's a plain
   triple-quoted string (not an f-string), so `{constants.EXTRACTED_DATA_FILE_PATH}`
   inside it is literal text, not a substituted value. If the commented-out
   `insert_tables` asset is ever finished and enabled, this needs to become an f-string
   (or use `.format(...)`) before the query would actually reference the right file
   path. Right now it's dead code (asset commented out) so it hasn't bitten anyone yet.

6. **Cron schedule was tightened to every minute (`* * * * *`).** Fine for local
   development/demoing, but if `dg dev` (or a deployed Dagster instance) is left running,
   this regenerates 20,000+20,000 fake rows and rewrites `database.duckdb` every 60
   seconds indefinitely. Worth dialing back (e.g. hourly or manual-trigger-only) once
   you're done actively testing, to avoid needless disk churn and confusing "the data
   changed and I didn't touch it" moments.

7. **Accidental nested-repo setup.** See §2 — recreate this deliberately (proper
   `git submodule add`, or don't nest at all) rather than by accident.

## 7. Current architecture (target state, including uncommitted fixes)

```
defs/
├── constants.py       # file path constants for the two CSVs
├── resources.py       # DuckDBResource -> data/raw/database.duckdb
├── jobs.py             # generate_product_data_job: runs generate_product_data
├── schedules.py        # generate_product_data_schedule: cron "* * * * *"
└── assets/
    ├── data_extraction.py
    │     generate_product_data()   -> writes data/raw/extracted_data.csv (20k rows)
    │     generate_customer_data()  -> writes data/raw/customer_data.csv (20k rows)
    │     product_dataset(database) -> deps: generate_product_data
    │                                  loads extracted_data.csv into DuckDB `products` table
    └── sql_queries.py   # product_table_insert / insert_table_query (unused — for a
                          # disabled future "insert" asset, not yet wired up)
```

Notably: **`generate_customer_data` isn't loaded into DuckDB by anything** — it only
writes a CSV. There's no `customer_dataset` asset analogous to `product_dataset`, and no
job/schedule touches it directly (it only runs because Dagster picks up all assets in the
`defs/` folder by default when you run `dg dev`, not because a job explicitly selects it).
If you want customers queryable in DuckDB the same way products are, you'd add a
`customer_dataset` asset mirroring `product_dataset`.

## 8. Step-by-step recreation guide

1. Install `uv`. Run `uv sync`, activate `.venv`.
2. `pyproject.toml`: keep `dagster==1.13.14`, `faker==40.31.0`, add back
   `faker-ecommerce-provider==1.2.0` (see Known Issue #2), `duckdb`,
   `numpy==2.2.6`, `pandas==2.2.3`, `dagster-duckdb`, `dagster-duckdb-pandas`. Dev group:
   `dagster-dg-cli`, `dagster-webserver`, `ipykernel`.
2. Scaffold with `dg` (or hand-write to match `[tool.dg]` config: `directory_type =
   "project"`, `root_module = "faker_data_generation_project"`).
3. `defs/assets/constants.py`: two path constants for the two CSVs under `data/raw/`.
4. `defs/assets/data_extraction.py`:
   - `generate_product_data`: loop 20,000×, build dict of
     `product_name/brand_name/SKU/price/order_id/product_description/data_generated_at`
     via `Faker()` + `EcommerceProvider`, `pd.DataFrame(...).to_csv(...)`.
   - `generate_customer_data`: loop 20,000×, build dict of
     `customer_name/email/phone/address` via plain `Faker()`, `.to_csv(...)`.
   - `product_dataset(database: DuckDBResource)`: `deps=["generate_product_data"]`,
     run `create or replace table products as (select * from
     read_csv_auto('{path}'))` — use `read_csv_auto`/`select *`, not literal column
     names (Known Issue #4).
5. `defs/resources.py`: `DuckDBResource(database="data/raw/database.duckdb")`, exposed
   via `@dg.definitions` returning `Definitions(resources={"database": ...})`.
6. `defs/jobs.py`: `AssetSelection.assets(["generate_product_data"])` →
   `define_asset_job("generate_product_data_job", selection=...)`.
7. `defs/schedules.py`: `ScheduleDefinition(job=generate_product_data_job,
   cron_schedule=...)` — pick a sane interval, not `* * * * *`, unless you're actively
   watching it run.
8. Add `.tmp_dagster_home*/` to `.gitignore` from the start (Known Issue #1).
9. `dg dev`, open http://localhost:3000, materialize assets, confirm via a notebook
   (`duckdb.connect("data/raw/database.duckdb").sql("select * from products")`) that
   the DuckDB table actually contains real product rows, not literal column-name
   strings.
10. Decide whether customers need their own DuckDB table (§7) and add a
    `customer_dataset` asset if so.

## 9. Open questions (for you to decide before/while recreating)

- Do you want `generate_customer_data` loaded into DuckDB as its own table
  (`customer_dataset`), the same way `product_dataset` loads products? Right now
  customers only ever land as a CSV.
- Do you want to finish and enable the commented-out `insert_tables` asset (incremental
  `INSERT` instead of `CREATE OR REPLACE TABLE ... AS SELECT`), or delete that
  scaffolding since `product_dataset` already fully replaces the table each run?
- What cron schedule do you actually want long-term — every minute was clearly a
  development/testing setting, not a production one.
- Should the two nested git repos be split apart, or formally linked via
  `git submodule add`?
