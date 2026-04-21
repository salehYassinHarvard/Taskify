import reflex as rx
import os
from reflex.plugins.sitemap import SitemapPlugin

config = rx.Config(
    app_name="taskify",
    db_url=os.getenv("DATABASE_URL", "sqlite:///reflex.db"),
    frontend_port=3000,
    backend_port=int(os.getenv("PORT", 8000)),
    api_url=os.getenv("API_URL", "http://localhost:8000"),
    plugins=[SitemapPlugin()],
)
