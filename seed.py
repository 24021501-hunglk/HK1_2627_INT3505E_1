import sqlite3

DB_FILE = "books.db"

db = sqlite3.connect(DB_FILE)

books = [
    ("Doraemon", "Fujiko F. Fujio", "9784091400011", 25000),
    ("Harry Potter", "J.K. Rowling", "9780747532743", 150000),
    ("Clean Code", "Robert C. Martin", "9780132350884", 320000),
    ("Python Crash Course", "Eric Matthes", "9781593279288", 280000),
    ("The Hobbit", "J.R.R. Tolkien", "9780261102217", 180000),
    ("Database System Concepts", "Abraham Silberschatz", "9780078022159", 450000),
    ("Computer Networks", "Andrew S. Tanenbaum", "9780132126953", 390000),
    ("Java Programming", "James Gosling", "9780000000001", 200000),
    ("Random Book 001", "Unknown Author", None, 10000),
    ("Random Book 002", "Test Author", None, 50000)
]

db.executemany("""
    INSERT INTO books (title, author, isbn, price)
    VALUES (?, ?, ?, ?)
""", books)

orders = [
    (1, 2, "pending"),
    (2, 1, "completed"),
    (3, 5, "pending"),
    (4, 1, "cancelled"),
    (5, 3, "pending")
]

db.executemany("""
    INSERT INTO orders (book_id, quantity, status)
    VALUES (?, ?, ?)
""", orders)

db.commit()
db.close()