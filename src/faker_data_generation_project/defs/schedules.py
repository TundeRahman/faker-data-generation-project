
import dagster as dg
from faker_data_generation_project.defs.jobs import extracted_data_job 

generate_personnel_data_schedule = dg.ScheduleDefinition(
    job=extracted_data_job,
    cron_schedule="0/5 * * * *", # every 5th of the month at midnight
)

