import os
import time, random, config
from datetime import datetime, timedelta
from celery import Celery
from models import Drop
from db import db_session, engine, commit_or_rollback, update_done, update_elected
from utils.eoswrap import transfer_wrap
from utils.nodes import Trains
from sqlalchemy import exists, func
from sqlmodel import select, Session
import cachetool, requests

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")



class SqlAlchemyTask(celery.Task):
    """An abstract Celery Task that ensures that the connection the the
    database is closed on task completion"""
    abstract = True

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        db_session.remove()


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(120.0, cmc_routine.s(), name='cmc routine')
    sender.add_periodic_task(3600.0, elect.s(), name='elect every hr')

@celery.task(base=SqlAlchemyTask)
def elect() -> str:
    start1=time.time()
    cur_time = datetime.utcnow()
    handle = f"{str(cur_time.date())}-{str(cur_time.hour)}"
    if not db_session.query(exists().where(Drop.handle==handle)).scalar():
        drop = Drop(handle=handle,
                        state="VERIFY",
                        type="roading",
                        issue_time = cur_time.isoformat()[:-3],
                        day=str(cur_time.date()), 
                        hour=str(cur_time.hour), 
                        winner="",
                        trx_id="")
        commit_or_rollback(drop)
    else:
        return "Election for this hr already existst"
    
    start = (datetime.utcnow()-timedelta(hours=1)).isoformat()[:-3]
    elected = draw(start)
    print(elected)
    update_elected(handle,elected)
    dropping = True
    while dropping:
        try:
            tx_id = transfer_wrap(elected,"roading")
            dropping = False
        except Exception as e:
            print(f"drop failed with error: {e}, waiting 60 seconds and verify again")
            time.sleep(60)
    suc = update_done(handle,tx_id)
    for winner in elected:
        cachetool.set_target_cooldown(winner,cur_time.isoformat()[:-3])
            
    return f"{(time.time()-start1)} elected {len(elected)}, tx: {tx_id}"

def draw(after):

    elig_cmcs = fetch_cmc_pub()
    filtered_eligible = get_eligs_and_filter(elig_cmcs, after)
    elected = [filtered_eligible.pop(random.randint(0,len(filtered_eligible)-1)) for l in range(config.drops_per_hr)]

    return elected

def fetch_runs(after):
    driver = Trains()
    elig_trains = []
    for station in config.mnky_stations:
        res = driver.logrun(arrive_station=station,after=after).json()
        elig_trains += [train['railroader'] for train in res["data"]]
    return elig_trains

def get_eligs_and_filter(eligs_cmc, after):
    
    elig_trains = set(fetch_runs(after))
    cooldowned = cachetool.get_cache("targetCD")
    final_elig = []
    for train in elig_trains:
        if train in eligs_cmc:
            if train in cooldowned.keys():
                if (datetime.utcnow()-timedelta(hours=config.raffle_cooldown)).isoformat()[:-3] > cooldowned[train]:
                    final_elig.append(train)
            else:
                final_elig.append(train)
    
    return final_elig

@celery.task()
def cmc_routine() -> str:
    start=time.time()
    try:
        cmcs = fetch_cmc_pub()
        cachetool.set_cache("cmcs",list(cmcs))
        cut = cachetool.get_cache("db")["last_elec"]
        eligs = get_eligs_and_filter(fetch_cmc_pub(),cut)
        db_state = retrieve_db_status(eligs)
        cachetool.set_cache("db",db_state)

    except Exception as e:
        print(e)
            
    return f"werke: jo.cmc routine done,took: {(time.time()-start)} "

def retrieve_db_status(eligs):
    query = select([func.count()])
    start = time.perf_counter()
    with Session(engine) as session:  
        lastelec = session.query(Drop).where(Drop.type=="roading").order_by(Drop.issue_time.desc()).first()
        
        drops_7d = session.query(Drop).where(Drop.issue_time>=(datetime.utcnow()-timedelta(days=7)).isoformat()[:-3]).all()
        drops_30d = session.query(Drop).where(Drop.issue_time>=(datetime.utcnow()-timedelta(days=30)).isoformat()[:-3]).all()
        drops_365d = session.query(Drop).where(Drop.issue_time>=(datetime.utcnow()-timedelta(days=365)).isoformat()[:-3]).all()

    count_7d = sum([len(r.winner.split(",")) for r in drops_7d])
    count_30d = sum([len(r.winner.split(",")) for r in drops_30d])
    count_365d = sum([len(r.winner.split(",")) for r in drops_365d])

    tclient = Trains()
    trains_status = tclient.status().json()
    hr = (datetime.utcnow()-timedelta(hours=1)).isoformat()[:-3]
    print(hr)
    count_60 = len(fetch_runs(hr))
    count_1440 = len(fetch_runs((datetime.utcnow()-timedelta(hours=24)).isoformat()[:-3]))
    count_all_1440 = len(Trains().logrun(after=(datetime.utcnow()-timedelta(hours=1)).isoformat()[:-3]).json()["data"])

    db_info={
        "trains_status": trains_status['data'],
        "count_runs": [count_60,count_1440, count_all_1440],
        "eligible": len(eligs),
        "last_elec": lastelec.issue_time if lastelec else "None",
        "mining_hist":[count_7d,count_30d,count_365d]
    }
    print(f"db_retrieve took {time.perf_counter()-start}")
    return db_info

def get_cmc():
    cmcs = requests.get(f"https://connect.cryptomonkeys.cc/accounts/api/v1/user_list/?code={config.cmc_key}").json()["data"]
    return cmcs

def fetch_cmc_pub():
    cmcs = get_cmc()
    cmc_full = []
    for cm in cmcs:
        cmc_full.append(cm["mainUser"])
        for wal in cm["wallets"]:
            cmc_full.append(wal)
    return set(cmc_full) 
