import os
from app import create_app

# APP_ENV accepts: development | testing | production
app = create_app(os.getenv("APP_ENV", "development"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
