from datetime import datetime, timedelta
import datetime as dt
import eospyabi.cleos
import eospyabi.keys
from eospyabi.types import Abi, Action
from eospyabi.utils import parse_key_file
import os
import pytz,time
import json, requests

from utils.nodes import AH,WAXMonitor
import random
from config import drop_account
from utils.disclog import postHook

drive=AH()
wax = WAXMonitor()

def scan_assets(account):
    scanning = True
    page=1
    out=[]
    while scanning:
        resp = drive.assets(owner=account,page=page).json()["data"]
        out += [res["asset_id"] for res in resp]
        if len(resp) == 0: scanning=False
        page+=1
        time.sleep(0.7)
    return out

def grab_winners(winners):
    asset_list = scan_assets(drop_account)
    if len(asset_list) < len(winners):
        print("NOT ENOUGH ASSETS IN THE DROP ACCOUNT! REFILL PLOX...SLEEPING THE TASK")
        time.sleep(7200)
    out={}
    for winner in winners:
        rnd = random.randint(0,len(asset_list)-1)
        asset = asset_list.pop(rnd)
        out[winner] = asset
    return out

def pick_best_waxnode(type,cutoff:int=8):
    
    resp = wax.endpoints(type=type).json()
    out=[]
    for node in resp:
        if node["weight"] > cutoff:
            out.append(node["node_url"])
    if len(out) < 1:
        out = ["https://api.waxsweden.org"]
    return out

def get_local_key():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    key_file = os.path.join(script_dir, f'{drop_account}_eosio.key')
    key = parse_key_file(key_file)
    return key

def build_memo(mode,n):
    memo = "Placeholder you lucky dude"
    if mode == "roading":
        memo = f"monKeytrains choo choo: You are a winner of the hourly election @hour {datetime.utcnow().hour} on the {datetime.utcnow().date()}"
    if mode == "mining":
        memo = f"monKeymining v2: You are a winner of the hourly election @hour {datetime.utcnow().hour} on the {datetime.utcnow().date()}"
    if mode == "targetmining":
        memo = f"monKeymining v2: You mined one of the active targets and received a cryptomonKey for your effort."
    if mode == "slots":
        memo = f"monKeyslots daily giveaway: You are a winner of the daily slots raffle on the {datetime.utcnow().date()}"
    return memo

def transfer_assets(node,targets,mode, memo=None):
    try:
        key = get_local_key()
        ce = eospyabi.cleos.Cleos(url=node)
        payloads = []
        for n,target in enumerate(targets):
            if memo is None:
                memo = build_memo(mode,n)
            payload = {
                "account": "atomicassets",
                "name": "transfer",
                "authorization": [{
                    "actor": drop_account,
                    "permission": "claimlink",
                }],
            }
            act_params = {
                "from": drop_account, 
                "to": f"{target}",  
                "asset_ids": [int(targets[target])],  
                "memo": memo,
            }
            data = ce.abi_json_to_bin(payload['account'], payload['name'], act_params)
            payload['data'] = data['binargs']
            payloads.append(payload)
        trx = {"actions": payloads}
        trx['expiration'] = str(
            (dt.datetime.utcnow() + dt.timedelta(seconds=60)).replace(tzinfo=pytz.UTC))
    
        resp = ce.push_transaction(trx, eospyabi.keys.EOSKey(key), broadcast=True)
        print(resp["transaction_id"])
        postHook(f"Congrats {' and '.join(targets)}! {memo}")
        return True,resp["transaction_id"]
    except Exception as e:
        print(e)
        return False,None

def transfer_wrap(winners,mode, memo=None):
    nodes_avail = pick_best_waxnode("api")
    winrs = grab_winners(winners)
    trying = True
    retry = 10
    round=0
    while trying and round < retry:
        node = nodes_avail.pop(random.randint(0,len(nodes_avail)-1))
        transfered,tx_id = transfer_assets(node,winrs,mode, memo)
        round +=1
        if transfered:
            trying = False
        else:
            time.sleep(10*(2**round))
        
    return tx_id

