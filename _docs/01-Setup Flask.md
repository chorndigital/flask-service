# Setup Flask Service Project

Awesome brief. Here’s a complete, batteries-included guide + reference project you can copy-paste. It starts at zero,
uses the Application Factory pattern, Blueprints for `/api/v1` and `/api/v2` (with JWT), request/response logging hooks,
caching, pytest, GitHub Actions CI, and a production Docker setup with Gunicorn.

---

# 1) Scaffold the project

```bash
# Windows-style virtualenv (your request):
py -m venv venv
venv\Scripts\activate

# (Mac/Linux alternative)
# python3 -m venv venv && source venv/bin/activate

mkdir flask-project && cd flask-project
mkdir -p app/models app/v1 app/v2 tests
```

### `requirements.txt`

```txt
Flask==3.0.3
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.7
Flask-JWT-Extended==4.6.0
Flask-Caching==2.3.0
python-dotenv==1.0.1
gunicorn==22.0.0

# Dev/Test
pytest==8.3.2
pytest-cov==5.0.0

# DB drivers (SQLite default; Postgres in Docker)
psycopg2-binary==2.9.9
```

```bash
pip install -r requirements.txt
```

---

# 2) Application code

## `app/config.py`

```python
import os


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    CACHE_TYPE = os.getenv("CACHE_TYPE", "SimpleCache")
    CACHE_DEFAULT_TIMEOUT = int(os.getenv("CACHE_DEFAULT_TIMEOUT", "60"))


class DevConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///dev.db")
    DEBUG = True


class TestConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


class ProdConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@db:5432/postgres")
    DEBUG = False


config_by_name = {
    "development": DevConfig,
    "testing": TestConfig,
    "production": ProdConfig,
}
```

## `app/extensions.py`

```python
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_caching import Cache

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cache = Cache()
```

## `app/__init__.py` (Application Factory + hooks + error handler)

```python
import logging, json, time
from flask import Flask, request, jsonify
from .config import config_by_name
from .extensions import db, migrate, jwt, cache


def create_app(config_name: str = "development"):
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cache.init_app(app)

    # Logging (stdout)
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    # Blueprints
    from .v1 import bp as v1_bp
    from .v2 import bp as v2_bp
    app.register_blueprint(v1_bp, url_prefix="/api/v1")
    app.register_blueprint(v2_bp, url_prefix="/api/v2")

    # Health
    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}, 200

    # Request/Response logging hooks
    @app.before_request
    def log_request():
        request.start_time = time.time()
        try:
            body = request.get_json(silent=True)
        except Exception:
            body = None
        app.logger.info(json.dumps({
            "event": "request",
            "method": request.method,
            "path": request.path,
            "args": request.args.to_dict(),
            "json": body
        }))

    @app.after_request
    def log_response(response):
        duration = None
        if hasattr(request, "start_time"):
            duration = round(time.time() - request.start_time, 4)
        app.logger.info(json.dumps({
            "event": "response",
            "status": response.status_code,
            "path": request.path,
            "duration_s": duration
        }))
        return response

    # Custom 404 JSON
    @app.errorhandler(404)
    def not_found(err):
        return jsonify({"error": "Not Found", "message": str(err)}), 404

    return app
```

## `app/models/__init__.py`

```python
from .post import Post  # noqa
```

## `app/models/post.py`

```python
from app.extensions import db


class Post(db.Model):
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    body = db.Column(db.String(200), nullable=False)

    def to_dict(self):
        return {"id": self.id, "userId": self.userId, "title": self.title, "body": self.body}
```

## `app/v1/__init__.py` (Blueprint without JWT, with caching)

```python
from flask import Blueprint

bp = Blueprint("v1", __name__)
from . import routes  # noqa
```

## `app/v1/routes.py`

```python
from flask import request, jsonify
from . import bp
from app.extensions import db, cache
from app.models import Post


@bp.get("/posts")
@cache.cached(timeout=60, key_prefix="v1_posts_list")
def list_posts():
    posts = Post.query.all()
    return jsonify([p.to_dict() for p in posts]), 200


@bp.get("/posts/<int:post_id>")
def get_post(post_id):
    post = Post.query.get_or_404(post_id)
    return jsonify(post.to_dict()), 200


@bp.post("/posts")
def create_post():
    data = request.get_json() or {}
    post = Post(userId=data.get("userId"), title=data.get("title"), body=data.get("body"))
    db.session.add(post)
    db.session.commit()
    cache.delete("v1_posts_list")
    return jsonify(post.to_dict()), 201


@bp.put("/posts/<int:post_id>")
@bp.patch("/posts/<int:post_id>")
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    data = request.get_json() or {}
    for k in ("userId", "title", "body"):
        if k in data:
            setattr(post, k, data[k])
    db.session.commit()
    cache.delete("v1_posts_list")
    return jsonify(post.to_dict()), 200


@bp.delete("/posts/<int:post_id>")
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    cache.delete("v1_posts_list")
    return jsonify({"deleted": post_id}), 200
```

## `app/v2/__init__.py` (Blueprint with JWT)

```python
from flask import Blueprint

bp = Blueprint("v2", __name__)
from . import routes, auth  # noqa
```

## `app/v2/auth.py` (simple demo login to mint JWT)

```python
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
    token = create_access_token(identity=int(user_id))
    return jsonify({"access_token": token}), 200
```

## `app/v2/routes.py` (CRUD protected with JWT)

```python
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import bp
from app.extensions import db, cache
from app.models import Post


@bp.get("/posts")
@jwt_required()
@cache.cached(timeout=60, key_prefix="v2_posts_list")
def list_posts():
    posts = Post.query.all()
    return jsonify([p.to_dict() for p in posts]), 200


@bp.get("/posts/<int:post_id>")
@jwt_required()
def get_post(post_id):
    post = Post.query.get_or_404(post_id)
    return jsonify(post.to_dict()), 200


@bp.post("/posts")
@jwt_required()
def create_post():
    _ = get_jwt_identity()  # example: enforce auth
    data = request.get_json() or {}
    post = Post(userId=data.get("userId"), title=data.get("title"), body=data.get("body"))
    db.session.add(post)
    db.session.commit()
    cache.delete("v2_posts_list")
    return jsonify(post.to_dict()), 201


@bp.put("/posts/<int:post_id>")
@bp.patch("/posts/<int:post_id>")
@jwt_required()
def update_post(post_id):
    _ = get_jwt_identity()
    post = Post.query.get_or_404(post_id)
    data = request.get_json() or {}
    for k in ("userId", "title", "body"):
        if k in data:
            setattr(post, k, data[k])
    db.session.commit()
    cache.delete("v2_posts_list")
    return jsonify(post.to_dict()), 200


@bp.delete("/posts/<int:post_id>")
@jwt_required()
def delete_post(post_id):
    _ = get_jwt_identity()
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    cache.delete("v2_posts_list")
    return jsonify({"deleted": post_id}), 200
```

## `wsgi.py` (Gunicorn entry)

```python
import os
from app import create_app

# APP_ENV accepts: development | testing | production
app = create_app(os.getenv("APP_ENV", "development"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

---

# 3) Database & Migrations

Initialize the migration repo and create the `posts` table:

```bash
# point FLASK_APP to wsgi:app (factory-aware)
$env:FLASK_APP="wsgi:app"         # PowerShell
$env:APP_ENV="development"
flask db init
flask db migrate -m "create posts"
flask db upgrade
```

SQLite file `dev.db` will appear in project root (DevConfig).

---

# 4) Run locally (dev)

```bash
$env:APP_ENV="development"
$env:FLASK_APP="wsgi:app"
flask run
# or python wsgi.py
```

Sample requests (no auth, v1):

```bash
curl -X POST http://localhost:5000/api/v1/posts -H "Content-Type: application/json" ^
  -d "{\"userId\":1,\"title\":\"Hello\",\"body\":\"World\"}"
curl http://localhost:5000/api/v1/posts
```

JWT flow (v2):

```bash
# get token
TOKEN=$(curl -s -X POST http://localhost:5000/api/v2/auth/login \
  -H "Content-Type: application/json" -d '{"user_id":123}' | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# use token
curl -H "Authorization: Bearer %TOKEN%" http://localhost:5000/api/v2/posts
```

---

# 5) Pytest setup

## `pytest.ini`

```ini
[pytest]
testpaths = tests
addopts = -q
```

## `tests/conftest.py`

```python
import os, pytest
from app import create_app
from app.extensions import db as _db


@pytest.fixture(scope="session")
def app():
    os.environ["APP_ENV"] = "testing"
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
```

## `tests/test_v1_posts.py`

```python
def test_v1_crud(client):
    # create
    r = client.post("/api/v1/posts", json={"userId": 1, "title": "T", "body": "B"})
    assert r.status_code == 201
    pid = r.get_json()["id"]

    # list
    r = client.get("/api/v1/posts")
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)

    # get
    r = client.get(f"/api/v1/posts/{pid}")
    assert r.status_code == 200
    assert r.get_json()["title"] == "T"

    # update
    r = client.patch(f"/api/v1/posts/{pid}", json={"title": "T2"})
    assert r.status_code == 200
    assert r.get_json()["title"] == "T2"

    # delete
    r = client.delete(f"/api/v1/posts/{pid}")
    assert r.status_code == 200
```

## `tests/test_v2_posts.py`

```python
def _token(client):
    r = client.post("/api/v2/auth/login", json={"user_id": 42})
    assert r.status_code == 200
    return r.get_json()["access_token"]


def test_v2_auth_and_crud(client):
    token = _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # create
    r = client.post("/api/v2/posts", json={"userId": 2, "title": "A", "body": "B"}, headers=headers)
    assert r.status_code == 201
    pid = r.get_json()["id"]

    # list (cached)
    r = client.get("/api/v2/posts", headers=headers)
    assert r.status_code == 200

    # get
    r = client.get(f"/api/v2/posts/{pid}", headers=headers)
    assert r.status_code == 200
    assert r.get_json()["title"] == "A"

    # update
    r = client.patch(f"/api/v2/posts/{pid}", json={"title": "AA"}, headers=headers)
    assert r.status_code == 200
    assert r.get_json()["title"] == "AA"

    # delete
    r = client.delete(f"/api/v2/posts/{pid}", headers=headers)
    assert r.status_code == 200
```

Run tests:

```bash
pytest
```

---

# 6) CI/CD (GitHub Actions)

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run tests
        env:
          APP_ENV: testing
          SECRET_KEY: ci-secret
          JWT_SECRET_KEY: ci-jwt
        run: pytest --cov=app

  build-docker:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: docker build -t flask-project:ci .
```

---

# 7) Production Docker

## `Dockerfile`

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    PORT=5000

WORKDIR /app

# System deps (optional minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Gunicorn command as default
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "wsgi:app"]
```

## `docker-compose.yml`

```yaml
version: "3.9"
services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      APP_ENV: production
      SECRET_KEY: ${SECRET_KEY:-prod-secret}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY:-prod-jwt}
      DATABASE_URL: postgresql+psycopg2://postgres:postgres@db:5432/postgres
      CACHE_TYPE: SimpleCache
    depends_on:
      - db

  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

### First boot & migrations in Docker

```bash
# Build & start
docker compose up -d --build

# Run migrations inside the container
docker compose exec web bash -lc "export FLASK_APP=wsgi:app && flask db upgrade"
```

> Gunicorn command is exactly as requested: `gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app`

---

# 8) Environment variables

Create `.env` for local Docker/compose:

```
SECRET_KEY=change-me
JWT_SECRET_KEY=change-me-too
```

---

# 9) Real-world notes

* **Config switching**: set `APP_ENV=development|testing|production`.
* **Caching strategy**: we cached the list endpoints and invalidate on mutations. For more complex cases, consider
  `cache.delete_memoized()` or versioned keys per tenant/user.
* **Structured logs**: emitted as JSON in hooks for better log aggregation.
* **Auth**: v2 shows `@jwt_required()` everywhere; add refresh tokens/roles later as needed.
* **DB**: SQLite for dev/tests, Postgres in production (already wired via `DATABASE_URL`).

---

# 10) Quick smoke run (no Docker)

```bash
# dev server
$env:APP_ENV="development"
$env:FLASK_APP="wsgi:app"
flask db upgrade
flask run
```

Hit:

* `GET  /api/v1/posts` (no auth)
* `POST /api/v2/auth/login` -> use token on
* `GET  /api/v2/posts` with `Authorization: Bearer <token>`

---