from flask import Flask, jsonify, request
app = Flask(__name__)

USERS = [
    {"id": 1, "name": "A"},
    {"id": 2, "name": "B"}
]
POSTS = [
    {
        "id": 1,
        "title": "ABCD",
        "content": "Testing",
        "author_id": 1,
        "tags": ["api", "rest"]
    }
    ]
COMMENTS = [
    {
        "id": 1,
        "post_id": 1,
        "user_id": 2,
        "content": "GG"
    }
]
TAGS = [
    {"id": 1, "name": "api", "user_id": 1},
    {"id": 2, "name": "rest", "user_id": 1}
]
FOLLOWS = [
    {
        "user_id": 1,
        "following_id": 2
    }
]

@app.get("/users/<int:user_id>")
def get_user(user_id):
    user = next((u for u in USERS if u["id"] == user_id), None)

    if user is None:
        return jsonify({"error" : "User not found"}), 404

    return jsonify(user)

@app.post("/users")
def create_user():
    data = request.get_json()

    user = {
        "id": len(USERS) + 1,
        "name": data["name"]
    }

    USERS.append(user)

    return jsonify(user), 201

@app.patch("/users/<int:user_id>")
def update_user(user_id):
    user = next((u for u in USERS if u["id"] == user_id), None)

    if user is None:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()

    if "name" in data:
        user["name"] = data["name"]

    return jsonify(user)

@app.get("/users/<int:user_id>/posts")
def get_user_posts(user_id):

    user = next((u for u in USERS if u["id"] == user_id), None)

    if user is None:
        return jsonify({"error": "User not found"}), 404

    posts = [p for p in POSTS if p["author_id"] == user_id]

    return jsonify(posts)


@app.post("/users/<int:user_id>/posts")
def create_user_post(user_id):

    user = next((u for u in USERS if u["id"] == user_id), None)

    if user is None:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()

    post = {
        "id": len(POSTS) + 1,
        "title": data["title"],
        "content": data["content"],
        "author_id": user_id,
        "tags": data.get("tags", [])
    }

    POSTS.append(post)

    return jsonify(post), 201

@app.patch("/users/<int:user_id>/posts/<int:post_id>")
def update_user_post(user_id, post_id):

    user = next((u for u in USERS if u["id"] == user_id), None)

    if user is None:
        return jsonify({"error": "User not found"}), 404

    post = next((p for p in POSTS if p["id"] == post_id and p["author_id"] == user_id), None)

    if post is None:
        return jsonify({"error": "Post not found"}), 404

    data = request.get_json()

    if "title" in data:
        post["title"] = data["title"]
    if "content" in data:
        post["content"] = data["content"]
    if "tags" in data:
        post["tags"] = data["tags"]

    return jsonify(post)

@app.delete("/users/<int:user_id>/posts/<int:post_id>")
def delete_user_post(user_id, post_id):

    user = next((u for u in USERS if u["id"] == user_id), None)

    if user is None:
        return jsonify({"error": "User not found"}), 404

    post = next((p for p in POSTS if p["id"] == post_id and p["author_id"] == user_id), None)

    if post is None:
        return jsonify({"error": "Post not found"}), 404

    POSTS.remove(post)

    return jsonify({"message": "Post deleted successfully"})

@app.get("/users/<int:user_id>/posts/<int:post_id>/comments")
def get_user_comments(user_id, post_id):

    user = next((u for u in USERS if u["id"] == user_id), None)

    if user is None:
        return jsonify({"error": "User not found"}), 404

    post = next((p for p in POSTS if p["id"] == post_id and p["author_id"] == user_id), None)

    if post is None:
        return jsonify({"error": "Post not found"}), 404

    comments = [c for c in COMMENTS if c["post_id"] == post_id]

    return jsonify(comments)


@app.post("/users/<int:user_id>/posts/<int:post_id>/comments")
def create_user_comment(user_id, post_id):

    user = next((u for u in USERS if u["id"] == user_id),None)

    if user is None:
        return jsonify({"error": "User not found"}), 404

    post = next((p for p in POSTS if p["id"] == post_id and p["author_id"] == user_id), None)

    if post is None:
        return jsonify({"error": "Post not found"}), 404

    data = request.get_json()

    comment = {
        "id": len(COMMENTS) + 1,
        "post_id": data["post_id"],
        "user_id": user_id,
        "content": data["content"]
    }

    COMMENTS.append(comment)

    return jsonify(comment), 201

@app.get("/users/<int:user_id>/posts/<int:post_id>/tags")
def get_user_tags(user_id, post_id):

    tags = [t for t in TAGS if t["user_id"] == user_id and t["post_id"] == post_id]

    return jsonify(tags)

@app.post("/users/<int:user_id>/posts/<int:post_id>/tags")
def create_user_tag(user_id):

    data = request.get_json()

    tag = {
        "id": len(TAGS) + 1,
        "name": data["name"],
        "user_id": user_id,
    }

    TAGS.append(tag)

    return jsonify(tag), 201

@app.get("/users/<int:user_id>/following")
def get_following(user_id):

    following_ids = [f["following_id"] for f in FOLLOWS if f["user_id"] == user_id]

    users = [u for u in USERS if u["id"] in following_ids]

    return jsonify(users)


@app.get("/users/<int:user_id>/followers")
def get_followers(user_id):

    follower_ids = [f["user_id"] for f in FOLLOWS if f["following_id"] == user_id]

    users = [u for u in USERS if u["id"] in follower_ids]

    return jsonify(users)


@app.post("/users/<int:user_id>/following/<int:target_user_id>")
def follow_user(user_id, target_user_id):

    follow = {
        "user_id": user_id,
        "following_id": target_user_id
    }

    FOLLOWS.append(follow)

    return jsonify(follow), 201

if __name__ == "__main__":
    app.run(debug=True)