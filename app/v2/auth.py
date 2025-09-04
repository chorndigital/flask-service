from flask import request, jsonify
from flask_jwt_extended import create_access_token
from . import bp


@bp.post("/auth/login")
def login():
    """
    Demo only: accepts {"user_id": <int>} and returns a JWT.
    In real apps, validate username/password or OAuth, etc.
    """
    data = request.get_json() or {}
    user_id = data.get("user_id")
    if user_id is None:
        return jsonify({"msg": "user_id required"}), 400

    # 🔑 Ensure identity is string
    token = create_access_token(identity=str(user_id))
    return jsonify({"access_token": token}), 200
