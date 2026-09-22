from flask import Flask, jsonify, request, make_response
app = Flask(__name__)
DEFAULT_SIZE, MAX_SIZE = 20, 100
BOOKS = [
    {"id": 1, "title": "A", "author": "B"},
    {"id": 2, "title": "C", "author": "D"},
    {"id": 3, "title": "E", "author": "F"},
    {"id": 4, "title": "G", "author": "H"},
    {"id": 5, "title": "I", "author": "J"},
    {"id": 6, "title": "K", "author": "L"},
    {"id": 7, "title": "M", "author": "N"}
]
"""_next_id = 1"""

@app.get("/books")
def list_books():
    try:
        page = int(request.args.get("page", 1))
        size = int(request.args.get("size", DEFAULT_SIZE))
    except ValueError:
        return jsonify(error = "page and size must be int"), 400
    page = max(page, 1)
    size = max(min(size, MAX_SIZE), 1)
    print("size = ", size)
    fit = BOOKS
    a = request.args.get("author")
    if a:
        fit = [b for b in fit if b["author"].lower() == a.lower()]
    q = (request.args.get("q")or "").lower()
    if q:
        fit = [b for b in fit if q in b["title"].lower()]

    total = len(fit)
    start = (page - 1) * size
    end = start + size
    items = fit[start:end]
    print("start =", start)
    print("end =", end)
    print("items =", items)
    last = (total+size-1)//size

    def u(p):
        return f"/books?page={p}&size={size}"
    links = {"self":{"href":u(page)}, "first":{"href":u(1)}}
    if page > 1: 
        links["prev"] = {"href":u(page-1)}
    if end < total:
        links["next"] = {"href":u(page+1)}
    body = {"data":items, "pagination":{"page": page, "size": size, "total": total, "total_pages": last}, "_links": links}
    resp = make_response(jsonify(body), 200)
    resp.headers["Cache-Control"] = "max-age=30"
    return resp

'''@app.put("/books/<int:bid>")
def put(bid):
    i = next((k for k, b in enumerate(BOOKS) if b["id"] == bid), None)
    if i is None:
        return jsonify(error = "not found"), 404
    p = request.get_json(silent = True) or {}
    t, a = p.get("title"), p.get("author")
    if not t or not a:
        return jsonify(error = "need title + author"), 422
    BOOKS[i] = {"id": bid, "title": t.strip(), "author": a.strip(),
                "isbn": p.get("isbn"), "price": p.get("price")}
    return jsonify(BOOKS[i]), 200

@app.patch("/books/<int:bid>")
def patch(bid):
    i = next((k for k,b in enumerate(BOOKS) if b["id"] == bid), None)
    if i is None:
        return jsonify(error = "not found"), 404
    p = request.get_json(silent = True) or {}
    if p.get("price", 0) < 0:
        return jsonify(error = "price must be positive"), 422
    for k in "title author isbn price".split():
        if k in p: BOOKS[i][k] = p[k]
    return jsonify(BOOKS[i]), 200

@app.delete("/books/<int:bid>")
def delete(bid):
    i = next((k for k, b in enumerate(BOOKS) if b["id"] == bid), None)
    if i is None:
        return jsonify(error = "not found"), 404
    BOOKS.pop(i)
    return "", 204

@app.post("/books")
def create_book():
    global _next_id
    if not request.is_json:
        return jsonify(error = "expected JSON"), 415
    p = request.get_json(silent=True) or {}
    t = (p.get("title") or "").strip()
    a = (p.get("author") or "").strip()
    if not t or not a:
        return jsonify(error = "title and author required"), 422
    book = {"id": _next_id, "title": t, "author": a}
    BOOKS.append(book); _next_id += 1
    resp = make_response(jsonify(book), 201)
    resp.headers["Location"] = f"/books/{book["id"]}"
    return resp'''

if __name__ == "__main__":
    app.run(debug=True)