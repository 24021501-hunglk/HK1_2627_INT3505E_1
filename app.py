from flask import Flask, jsonify, request, make_response
import sqlite3, hashlib, json
app = Flask(__name__)
DB_FILE = "books.db"

DEFAULT_SIZE, MAX_SIZE = 20, 100
def get_db():
    db = sqlite3.connect(DB_FILE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT,
            price REAL
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            status TEXT NOT NULL DEFAULT 'pending'
            )
    """)
    db.commit()
    db.close()

def row_to_book(row):
    return {
        'id': row['id'],
        'title': row['title'],
        'author': row['author'],
        'isbn': row['isbn'],
        'price': row['price']
    }

def row_to_order(row):
    return {
        'id': row['id'],
        'book_id': row['book_id'],
        'quantity': row['quantity'],
        'status': row['status']
    }

@app.get("/books")
def list_books():
    db = get_db()
    rows = db.execute("SELECT * FROM books").fetchall()
    return jsonify([row_to_book(r) for r in rows]), 200

@app.get('/books/<int:bid>')
def fetch(bid):
    db = get_db()
    row = db.execute('SELECT * FROM books WHERE id = ?', (bid,)).fetchone()
    if row is None:
        return jsonify(error = 'not found'), 404

    book = row_to_book(row)
    book_json = json.dumps(book, sort_keys = True, separators = ("," , ":"))

    etag = hashlib.sha256(book_json.encode("utf-8")).hexdigest()

    etag = f'"{etag}"'

    client_etag = request.headers.get("If-None-Match")

    if client_etag == etag:
        resp = make_response('', 304)
        resp.headers['ETag'] = etag
        resp.headers['Cache-Control'] = 'max-age=60'
        return resp
    
    resp = make_response(jsonify(book),200)
    resp.headers['ETag'] = etag
    resp.headers['Cache-Control'] = 'max-age=60'
    return resp

@app.put("/books/<int:bid>")
def put(bid):
    db = get_db()
    row = db.execute('SELECT * FROM books WHERE id = ?', (bid,)).fetchone()
    if row is None:
        return jsonify(error = 'not found'), 404
    p = request.get_json(silent=True) or {}
    t, a = p.get('title'), p.get('author')
    if not t or not a:
        return jsonify(error = 'title and author are required'), 422
    db.execute(
        'UPDATE books SET title = ?, author = ?, isbn = ?, price = ? WHERE id = ?',
        (t.strip(), a.strip(), p.get('isbn'), p.get('price'), bid)
    )
    db.commit()
    updated = db.execute('SELECT * FROM books WHERE id = ?', (bid,)).fetchone()
    return jsonify(row_to_book(updated)), 200

@app.patch("/books/<int:bid>")
def patch(bid):
    db = get_db()
    row = db.execute('SELECT * FROM books WHERE id = ?', (bid,)).fetchone()
    if row is None:
        return jsonify(error = 'not found'), 404
    p = request.get_json(silent=True) or {}
    t, a = p.get('title'), p.get('author')
    if not t or not a:
        return jsonify(error = 'title and author are required'), 422
    db.execute(
        'UPDATE books SET title = ?, author = ?, isbn = ?, price = ? WHERE id = ?',
        (t.strip(), a.strip(), p.get('isbn'), p.get('price'), bid)
    )
    db.commit()
    updated = db.execute('SELECT * FROM books WHERE id = ?', (bid,)).fetchone()
    return jsonify(row_to_book(updated)), 200

@app.delete("/books/<int:bid>")
def delete(bid):
    db = get_db()
    row = db.execute('SELECT * FROM books WHERE id = ?', (bid,)).fetchone()
    if row is None:
        return jsonify(error = 'not found'), 404
    db.execute('DELETE FROM books WHERE id = ?', (bid,))
    db.commit()
    return '', 204

@app.post("/books")
def create_book():
    p = request.get_json(silent=True) or {}
    t, a = p.get("title"), p.get("author")
    if not t or not a:
        return jsonify(error="need title + author"), 422
    db = get_db()
    cur = db.execute(
        'INSERT INTO books (title, author, isbn, price) VALUES (?, ?, ?, ?)',
        (t.strip(), a.strip(), p.get("isbn"), p.get("price"))
    )
    db.commit()
    new_row = db.execute('SELECT * FROM books WHERE id = ?', (cur.lastrowid,)).fetchone()
    return jsonify(row_to_book(new_row)), 201

@app.get('/orders/<int:oid>')
def fetch_order(oid):
    db = get_db()
    row = db.execute('SELECT * FROM orders WHERE id = ?', (oid,)).fetchone()
    if row is None:
        return jsonify(error = 'not found'), 404
    return jsonify(row_to_order(row)), 200

if __name__ == "__main__":
    init_db()
    app.run(debug=True)