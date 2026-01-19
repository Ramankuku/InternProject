import pymysql
import pandas as pd

df = pd.read_csv(r"C:\Intern\Notebook\final_data.csv")

conn = pymysql.connect(
    host="localhost",
    user="root",          
    password="Raman164@",
    database="bnpl_system",
    charset="utf8mb4"
)

cursor = conn.cursor()

insert_query = """
INSERT INTO bnpl_users (
    user_id,
    monthly_income,
    num_active_bnpl_plans,
    total_bnpl_amount,
    average_emi,
    bnpl_income_ratio,
    password,
    Emi_delayed
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""

data = list(df.itertuples(index=False, name=None))

cursor.executemany(insert_query, data)

conn.commit()
cursor.close()
conn.close()

print("✅ Data inserted successfully into bnpl_users table")
