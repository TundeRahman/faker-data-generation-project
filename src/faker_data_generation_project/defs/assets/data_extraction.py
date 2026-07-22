
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
from dagster import Definitions

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 2. create a function to generate personnel data and save it to a CSV file
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@dg.asset
def generate_product_data() -> None:
    number_record = 20000
    product_data = []
    for _ in range(number_record):
      product = {
          'product_name': fake.product_name(),
          'brand_name': fake.brand_name(),
          'SKU': fake.sku(),
          'price': fake.price(),
          'order_id': fake.order_id(), 
          'product_description': fake.product_description(),
          'data_generated_at': pd.Timestamp.now()
      }
      product_data.append(product)

    df = pd.DataFrame(product_data)
    df.to_csv(constants.EXTRACTED_DATA_FILE_PATH, index=False)
    

  
  
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 3. create a function to create a DuckDB table from the generated data
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@dg.asset
def generate_customer_data() -> None:
    number_record = 20000
    customer_data = []
    for _ in range(number_record):
      customer = {
          'customer_name': fake.name(),
          'email': fake.email(),
          'phone': fake.phone_number(),
          'address': fake.address()
      }
      customer_data.append(customer)

    df = pd.DataFrame(customer_data)
    df.to_csv(constants.CUSTOMER_DATA_FILE_PATH, index=False)
    
  

@dg.asset   (  
    deps=["generate_product_data"],
)   
def product_dataset(database: DuckDBResource) -> None:
    """
      The raw taxi zones dataset, loaded into a DuckDB database.
    """

    query = f"""
      create or replace table products as (
        select *
        from read_csv_auto('{constants.EXTRACTED_DATA_FILE_PATH}')
      );
    """

    with database.get_connection() as conn:
        conn.execute(query)
        



