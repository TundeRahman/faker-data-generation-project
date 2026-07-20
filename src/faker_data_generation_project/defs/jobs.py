# src/dagster_essentials/defs/jobs.py
import dagster as dg


generate_personnel_data = dg.AssetSelection.assets(["generate_personnel_data"])

extracted_data_job = dg.define_asset_job(
    name= "extracted_data_job",
    selection=generate_personnel_data
)