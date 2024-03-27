from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from database import client
import pdb
import redis

app = FastAPI()

class UrlModel(BaseModel):
    url : str


@app.get("/")
async def root():
    return "This is the URl shortner api"


@app.post("/urlToShort")
async def generate_short_url(requestId:Request, payload:UrlModel):
    redis_client = await give_redis_client()
    counter = int(redis_client.get("counter"))
    db = client.urlShortner
    url_collection = db.get_collection("urls")
    encoded_value = await base10_to_base64(counter)
    model_to_dump = {"encoded_value":encoded_value, "long_url":payload.url}
    result = await url_collection.insert_one(model_to_dump)
    counter += 1
    redis_client.set("counter", counter)
    return f"http://127.0.0.1:8000/tiny_url/{encoded_value}"



@app.get("/tiny_url/{encoded_value}")
async def fetch_lon_url(request:Request, encoded_value:str):
    db = client.urlShortner
    url_collection = db.get_collection("urls")
    document = await url_collection.find_one({"encoded_value":encoded_value})
    if document:
        return RedirectResponse(url=document["long_url"])
    else:
        return f"No url ound for this encoded value {encoded_value}"
    



async def base10_to_base64(value):
    s = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    hash_str = ''
    while value > 0:
        hash_str = s[value % 62] + hash_str
        value = int(value / 62)
    return hash_str


async def give_redis_client():
    redis_host = "localhost"
    redis_port  = "6379"
    redis_conn = redis.Redis(host=redis_host, port=redis_port, db=0)
    return redis_conn