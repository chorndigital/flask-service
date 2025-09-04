# 📂 Project Structure

```
flask-project/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── post.py
│   ├── v1/
│   │   ├── __init__.py
│   │   └── routes.py
│   └── v2/
│       ├── __init__.py
│       ├── auth.py
│       └── routes.py
│
├── migrations/             # Created after `flask db init`
│   └── ... auto-generated migration files ...
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_v1_posts.py
│   └── test_v2_posts.py
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── .gitignore
├── requirements.txt
├── pytest.ini
├── docker-compose.yml
├── Dockerfile
├── wsgi.py
└── README.md   # (optional, for project docs)

```