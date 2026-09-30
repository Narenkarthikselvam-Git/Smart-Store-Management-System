import sqlite3

conn = sqlite3.connect("database.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE products(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
price INTEGER,
quantity INTEGER
)
""")

conn.commit()
conn.close()

print("Database created successfully")