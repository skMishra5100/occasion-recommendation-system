"""Shared test setup.

The real embedding model (~90 MB) is downloaded from the internet, which we don't want in tests.
So the tests use FakeModel: a tiny stand-in that turns text into a vector by counting letter groups.
It is NOT smart (it only notices similar spelling), but it lets us test all the logic around it.
"""
import zlib
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from catalog import load_products
from main import create_app
from recommender import Recommender, load_occasions

DATA = Path(__file__).parent.parent / "data"


class FakeModel:
    def encode(self, texts, normalize_embeddings=True):
        vectors = np.zeros((len(texts), 1024))
        for row, text in enumerate(texts):
            for word in text.lower().split():
                padded = f"<{word}>"
                for size in (3, 4):
                    for i in range(len(padded) - size + 1):
                        vectors[row, zlib.crc32(padded[i:i + size].encode()) % 1024] += 1
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / np.where(norms == 0, 1, norms)


@pytest.fixture(scope="session")
def recommender():
    products = load_products(DATA / "products.json", DATA / "categories.json")
    return Recommender(products, load_occasions(DATA / "occasions.json"), model=FakeModel())


@pytest.fixture(scope="session")
def client():
    with TestClient(create_app(model=FakeModel())) as client:
        yield client
