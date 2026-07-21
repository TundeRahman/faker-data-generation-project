# src/dagster_essentials/defs/resources.py
import dagster as dg
from dagster_duckdb import DuckDBResource


database_resource = DuckDBResource(
    database="data/raw/database.duckdb"
)


@dg.definitions
def resources() -> dg.Definitions:
    return dg.Definitions(resources={"database": database_resource})
