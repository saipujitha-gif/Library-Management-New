from db import get_connection

try:
    conn = get_connection()
    print("MySQL Database Connected Successfully!")
    conn.close()

except Exception as e:
    print("Database Connection Failed:", e)