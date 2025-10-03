import os, base64
from typing import List
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from PIL import Image, ImageDraw
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "Admin123!")

db_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
app = FastAPI()

class Result(BaseModel):
    date: str
    totalQty: int
    totalPrice: int


def generate_image(value: int, qty: int, date: str) -> str:
    static_dir = "/src/images"
    os.makedirs(static_dir, exist_ok=True)
    path = os.path.join(static_dir, f"result_{date}_{qty}_{value}.png")
    img = Image.new("RGB", (400, 200), color="white")
    d = ImageDraw.Draw(img)
    d.text((10, 90), f"{date} - {qty} - {value}", fill="black")
    img.save(path)
    return path


@app.post("/results")
def save_results(results: List[Result]):
    processed = []
    with db_driver.session() as session:
        for r in results:
            image_path = generate_image(r.totalPrice, r.totalQty, r.date)

            session.run(
                """
                MERGE (res:Result {date: $date})
                SET res.qty = $qty,
                    res.price = $price,
                    res.image_path = $image_path
                """,
                date=r.date, qty=r.totalQty, price=r.totalPrice, image_path=image_path
            )

            processed.append({
                "date": r.date,
                "qty": r.totalQty,
                "price": r.totalPrice,
                "image_path": image_path
            })
    return {"status": "ok", "processed": processed}


@app.get("/results/search_many")
def search_similar_many(qty: int, price: int, limit: int = 5):
    with db_driver.session() as session:
        query = """
        MATCH (r:Result)
        WITH r, sqrt((r.qty - $qty)^2 + (r.price - $price)^2) AS dist
        ORDER BY dist ASC
        LIMIT $limit
        RETURN r.date AS date, r.qty AS qty, r.price AS price, r.image_path AS image_path
        """
        results = session.run(query, qty=qty, price=price, limit=limit)
        payload = []
        for record in results:
            path = record["image_path"]
            if path and os.path.exists(path):
                with open(path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                    payload.append({
                        "date": record["date"],
                        "qty": record["qty"],
                        "price": record["price"],
                        "image_base64": b64
                    })
        return JSONResponse(content=payload)