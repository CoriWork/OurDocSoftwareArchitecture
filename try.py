import psycopg2

print("开始连接数据库...")

conn = psycopg2.connect(
    host="113.44.204.241",
    port=5432,
    database="db",
    user="ourdoc",
    password="1234Abcd",
    sslmode="disable"
)

print("连接成功")

cur = conn.cursor()
cur.execute("SELECT version();")
print(cur.fetchone())

cur.close()
conn.close()
