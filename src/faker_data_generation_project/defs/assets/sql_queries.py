product_table_insert = ("""
    INSERT INTO products (
          product_name,
          brand_name,
          SKU,
          price,
          order_id,
          product_description,
          data_generated_at
    )
    SELECT
          product_name,
          brand_name,
          SKU,
          price,
          order_id,
          product_description,
          data_generated_at
    from '{constants.EXTRACTED_DATA_FILE_PATH}' 

""")


