# 📘 README.md

```markdown
# Flask Project 🚀

**Flask REST API** project using:

- **Application Factory Pattern** create_app function (and the project layout around it) is the core of the Application
  Factory Pattern.
- **Blueprints** with versioning (`/api/v1` and `/api/v2`)
- **Flask-SQLAlchemy** + **Flask-Migrate** (DB migrations)
- **JWT Authentication** for `/api/v2`
- **Request/Response logging hooks**
- **Custom error handlers**
- **Flask-Caching**
- **Pytest** with CI/CD (GitHub Actions)
- **Docker + Gunicorn** for production

---

## 🔧 Setup & Run (Local)

```bash
# Create and activate virtual environment
py -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Set environment
set APP_ENV=development  # Windows PowerShell
# export APP_ENV=development  # macOS/Linux

# Initialize database
flask db init
flask db migrate -m "init"
flask db upgrade

# Run Flask (dev server)
flask run
````

---

## 🐳 Run with Docker

Build and start services:

```bash
docker compose up -d --build
```

Apply migrations inside the container:

```bash
docker compose exec web flask db upgrade
```

The app runs at **[http://localhost:5000](http://localhost:5000)**

Gunicorn is used in production mode:

```
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

---

## 🧪 Run Tests

```bash
pytest
```

Or with coverage:

```bash
pytest --cov=app
```

---

## 🔑 API Endpoints

### `/api/v1` (no authentication)

* `GET    /api/v1/posts` → List all posts
* `GET    /api/v1/posts/<id>` → Get one post
* `POST   /api/v1/posts` → Create a post
* `PUT    /api/v1/posts/<id>` → Update a post
* `DELETE /api/v1/posts/<id>` → Delete a post

### `/api/v2` (JWT protected)

1. Get a token:

   ```bash
   POST /api/v2/auth/login
   {"user_id": 1}
   ```

   Response:

   ```json
   {"access_token": "<JWT_TOKEN>"}
   ```

2. Use the token:

   ```
   Authorization: Bearer <JWT_TOKEN>
   ```

   Endpoints (same as v1):

    * `GET    /api/v2/posts`
    * `POST   /api/v2/posts`
    * `GET    /api/v2/posts/<id>`
    * `PUT    /api/v2/posts/<id>`
    * `DELETE /api/v2/posts/<id>`

---

## ⚙️ Environment Variables

* `APP_ENV` → `development` | `testing` | `production`
* `SECRET_KEY` → Flask secret
* `JWT_SECRET_KEY` → Secret for JWT tokens
* `DATABASE_URL` → DB connection string (SQLite/PG)
* `CACHE_TYPE` → Default: `SimpleCache`

Example `.env`:

```
SECRET_KEY=change-me
JWT_SECRET_KEY=change-me-too
DATABASE_URL=sqlite:///dev.db
CACHE_TYPE=SimpleCache
```

---

## ✅ CI/CD

* **GitHub Actions** runs `pytest` and builds Docker image on each push/PR.
* Config file: `.github/workflows/ci.yml`