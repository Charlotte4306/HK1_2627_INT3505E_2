from flask import Flask, jsonify, request, url_for

app = Flask(__name__)

POSTS = []
next_post_id = 1

#Lấy danh sách tất cả bài viết
@app.get("/api/v1/posts")
def list_post():
    return jsonify({
        "data": POSTS,
        "total": len(POSTS)
    }), 200

#Tạo bài viết mới
@app.post("/api/v1/posts")
def create_post():
    global next_post_id 
    
    if not request.is_json:
        return jsonify(error="expected JSON"), 415
    data = request.get_json(silent=True)
    
    if not isinstance(data, dict):
        return jsonify(error="invalid JSON"), 400
    
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()
    author_id = data.get("author_id")
    if not title or not content:
        return jsonify(error="title and content required"), 400
    
    if not isinstance(author_id, int) or author_id < 1:
        return jsonify(error="author_id must be a positive integer"), 400
    
    post = {
        "id": next_post_id,
        "title": title,
        "content": content,
        "author_id": author_id
    }
    
    POSTS.append(post)
    next_post_id += 1
    
    #Tạo URL của bài viết vừa tạo, dùng url_for sau này dễ mở rộng
    location = url_for("get_post", post_id=post["id"], _external=True)
    return jsonify(post), 201, {"Location": location}

#Lấy bài viết theo id
@app.get("/api/v1/posts/<int:post_id>")
def get_post(post_id):
    for post in POSTS:
        if post["id"] == post_id:
            return jsonify(post), 200
        
    return jsonify(error="Post not found"), 404

if __name__ == "__main__":
    app.run(port=5000, debug=True)