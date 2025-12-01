import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT NOT NULL,
    password TEXT NOT NULL,
    payment TEXT
)
''')

# جدول جديد لتخزين عدد المحاولات لكل اختبار لكل مستخدم
cursor.execute('''
CREATE TABLE IF NOT EXISTS user_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    test_id INTEGER NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    UNIQUE(user_id, test_id)
)
''')

conn.commit()
conn.close()