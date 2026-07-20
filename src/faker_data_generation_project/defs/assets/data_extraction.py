
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 1. import necessary libraries
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

import dagster as dg
from dagster_duckdb import DuckDBResource
import pandas as pd
from faker import Faker
from faker_ecommerce import EcommerceProvider
from faker_data_generation_project.defs.assets import constants
import os
import pandas as pd
fake = Faker()
fake.add_provider(EcommerceProvider)

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 2. create a function to generate personnel data and save it to a CSV file
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@dg.asset
def generate_personnel_data() -> None:
  number_record = 20000
  product_data = []
  for _ in range(number_record):
    product = {
        'product_name': fake.product_name(),
        'brand_name': fake.brand_name(),
        'SKU': fake.sku(),
        'price': fake.price(),
        'data_generated_at': pd.Timestamp.now()
    }
    product_data.append(product)

  df = pd.DataFrame(product_data)
  df.to_csv(constants.EXTRACTED_DATA_FILE_PATH, index=False)
  
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 3. create a function to create a DuckDB table from the generated data
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------




