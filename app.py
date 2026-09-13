from flask import Flask, jsonify, request
from uuid import uuid4
app = Flask(__name__)
BOOKS = [
    {"id":"1", "title": "Book 1", "author": "Author 1"},
    {"id":"2", "title": "Book 2", "author": "Author 2"},
    {"id":"3", "title": "Book 3", "author": "Author 3"},
]

def find_by_id(book_id):
    for book in BOOKS:
        if book["id"] == str(book_id):
            return book
    return None

@app.route("/books/<book_id>", methods = ["GET"])
def get_book(book_id):
    book = find_by_id(book_id)
    if book is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(book), 200

@app.route("/items/<int:item_id>")
def get_item(item_id):
    return jsonify({"id": item_id}), 200

if __name__ == "__main__":
    app.run(host = "127.0.0.1", port = 5000,debug=True)