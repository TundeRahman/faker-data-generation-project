
import dagster as dg
from faker_data_generation_project.defs.jobs import generate_product_data_job 

generate_product_data_schedule = dg.ScheduleDefinition(
    job=generate_product_data_job,
    cron_schedule="* * * * *", # every minute
)

