
from fastapi import Body, FastAPI, Form, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
import time,os, cachetool, aioredis
from enum import Enum
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from db import  retrieve_drops, init_db
from datetime import datetime

app = FastAPI(title="monKeytrains API",
        description="made with <3 by green",
        version="0.1.0")

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)

class OrderChoose(str, Enum):
    desc = "desc"
    asc = "asc"

@app.on_event("startup")
def on_startup():
    init_db()
    try:
        start_iso = cachetool.get_cache("db")["last_elec"]
    except Exception as e:
        print("init cache with current time")
        cachetool.set_cache("db",{"last_elec":datetime.utcnow().isoformat().split('Z')[0][:-3]})
    
    redis =  aioredis.from_url(os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379"), encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    print("redis cache success")

@app.get("/")
def home(request: Request):
    return {"Yes this service is running fine!"}


@app.get("/healthc")
def home(request: Request):
    return {"Yes this service is running fine!"}

@app.get("/status_db")
async def get_db_status():
    start = time.time()
    db_cache = cachetool.get_cache("db")
    
    return {"query_time":time.time()-start,"db_state":db_cache}

@app.get("/drops")
@cache(expire=5)
async def get_drops(
            before:str=None,
            after:str=None,
            limit:int=None,
            order:OrderChoose=OrderChoose.desc):

    start = time.time()
    qry = list(retrieve_drops(before,after,limit,order.value))
    
    return {"query_time":time.time()-start,"count":len(qry),"data":qry}

@app.get("/cmc_list")
async def get_cached_cmc_wallet_list():

    start = time.time()
    val = cachetool.get_cache("cmcs")    
    
    return {"query_time":time.time()-start,"data":val}

@app.get("/get_cooldown_raffle")
async def retrieve_cd_raffle_from_redis():

    start = time.time()
    resp = cachetool.get_cache("raffleCD")
    
    return {"query_time":time.time()-start,"data":resp}

@app.get("/get_personal")
async def retrieve_personal_info():

    start = time.time()
    resp = cachetool.get_cache("raffleCD")
    val = cachetool.get_cache("cmcs")
    db = cachetool.get_cache("db")
        
    return {"query_time":time.time()-start,"cds":resp,"db":db,"cmcs":val}
