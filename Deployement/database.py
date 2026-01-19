import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Raman162004@@@",   # your MySQL password
    "database": "bnpl_system"
}

def init_db():
    conn = mysql.connector.connect(**DB_CONFIG)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS bnpl_users (
            user_id VARCHAR(255) PRIMARY KEY,
            monthly_income INT NULL,
            num_active_bnpl_plans INT NULL,
            total_bnpl_amount INT NULL,
            average_emi INT NULL,
            bnpl_income_ratio FLOAT NULL,
            password VARCHAR(255) NOT NULL,
            Emi_delayed INT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = mysql.connector.connect(**DB_CONFIG)
    c = conn.cursor(dictionary=True)   # return dict instead of tuple
    c.execute("SELECT * FROM bnpl_users WHERE user_id=%s", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def add_user(user_id, password):
    conn = mysql.connector.connect(**DB_CONFIG)
    c = conn.cursor()
    c.execute("""
        INSERT INTO bnpl_users (
            user_id, monthly_income, num_active_bnpl_plans, total_bnpl_amount,
            average_emi, bnpl_income_ratio, password, Emi_delayed
        )
        VALUES (%s, NULL, NULL, NULL, NULL, NULL, %s, NULL)
    """, (user_id, password))
    conn.commit()
    conn.close()