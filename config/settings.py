from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = "dev-only-change-me"; DEBUG = True; ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = ["django.contrib.auth", "django.contrib.contenttypes", "django.contrib.staticfiles", "requests_app"]
MIDDLEWARE = ["django.middleware.common.CommonMiddleware"]
ROOT_URLCONF = "config.urls"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}  # PostgreSQL/MySQL by env in prod
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"; USE_TZ = True; STATIC_URL = "static/"
API_TOKEN = "demo-token"  # token auth for the demo; use OAuth/JWT in production
