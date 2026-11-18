from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from catalog import load_products
from recommender import Recommender, load_occasions

DATA = Path(__file__).parent / "data"


def create_app(model=None):
    """Build the app. (`model` is only used by the tests to avoid downloading the real one.)"""

    @asynccontextmanager
    async def lifespan(app):
        # Runs once when the server starts: load products, build the search index.
        products = load_products(DATA / "products.json", DATA / "categories.json")
        occasions = load_occasions(DATA / "occasions.json")
        app.state.recommender = Recommender(products, occasions, model)
        print(f"Ready: {len(products)} products indexed")
        yield

    app = FastAPI(title="Occasion-Based Product Recommender", lifespan=lifespan)

    # Allow the React dev server to call this API directly .
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                       allow_methods=["GET"], allow_headers=["*"])

    @app.get("/api/health")
    def health(request: Request):
        """Quick check that the server is up."""
        return {"status": "ok", "products_indexed": len(request.app.state.recommender.products)}

    @app.get("/api/occasions")
    def occasions(request: Request):
        """Known occasions; the ones marked `featured` become the suggestion chips in the UI."""
        known = request.app.state.recommender.occasions
        return {"occasions": [{"name": o["name"], "featured": o.get("featured", False)} for o in known]}

    @app.get("/api/recommendations")
    def recommendations(
        request: Request,
        occasion: str = Query(..., min_length=1, max_length=200, description='e.g. "Diwali" or "birthday"'),
        limit: int = Query(10, ge=1, le=60, description="how many products to return"),
    ):
        """Ranked products for an occasion."""
        return request.app.state.recommender.recommend(occasion, limit)

    return app


app = create_app()
