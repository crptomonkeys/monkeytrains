import concurrent.futures,inspect, requests

class apiException(Exception):
    pass

def get_resp(url: str) -> requests.models.Response:
    
    resp = requests.get(url,timeout=5)
    resp.raise_for_status()
    if resp.json().get("error"):
        raise apiException(resp.json().get("error"))
    return resp

def build_query(args: dict) -> str:
        args.pop("endpoint")
        args.pop("url")
        args.pop("self")
        query = None
        for arg in args:
            if args.get(arg) is not None:
                if query is None:
                    query = f"{arg}={args.get(arg)}"
                else:
                    query += f"&{arg}={args.get(arg)}"
        return query

class Trains:
    def __init__(
        self,
        server="history.api.trains.cards",
    ):
        self.limit = 100
        self.server = server
        self.url_base = f"https://{self.server}"
        
        self.session = requests.Session()

    def status(
        self,
    ) -> requests.models.Response:
        endpoint = inspect.currentframe().f_code.co_name
        url = f"{self.url_base}/{endpoint}"
        return self.session.get(f"{url}")
    
    def logrun(
        self,
        arrive_station: str = None,
        offset: int = 0,
        limit: int = 5000,
        simple: str = 'true',
        order: str = 'desc',
        type: int = None,
        after_timestamp: str = None,
        before_timestamp: str = None,
        after: str = None,
        before: str = None,
    ) -> requests.models.Response:
        endpoint = inspect.currentframe().f_code.co_name
        url = f"{self.url_base}/{endpoint}"
        args = locals()
        query = build_query(args)
        if query is None:
            raise Exception("Must provide at least one query parameter")
        return self.session.get(f"{url}?{query}")

    def stations(
        self,
        timeframe: int,
        limit: int = 500,
    ) -> requests.models.Response:
        endpoint = inspect.currentframe().f_code.co_name
        url = f"{self.url_base}/{endpoint}"
        args = locals()
        query = build_query(args)
        if query is None:
            raise Exception("Must provide at least one query parameter")
        return self.session.get(f"{url}?{query}")

    

class Hyperion:
    def __init__(
        self,
        api_version="v2",
        server="api.waxsweden.org",
    ):
        self.limit = 100
        self.api_version = api_version 
        self.server = server
        self.url_base = f"https://{self.server}/{self.api_version}/history"

    def get_mines(
        self,
        skip: int = None,
        after: int = None,
        serv: str = 'https://api.waxsweden.org',
    ) -> requests.models.Response:
        url = f"{serv}/v2/history/"
        
        return get_resp(f'{url}get_actions?account=m.federation&act.name=logmine&limit=100&sort=asc&after={after}&skip={skip}')
        

class WAXMonitor:
    def __init__(
        self,
        server="waxmonitor.cmstats.net",
    ):
        self.limit = 100
        self.server = server
        self.url_base = f"http://{self.server}/api"
        
        self.session = requests.Session()
    
    def endpoints(
        self,
        type: int = None,
    ) -> requests.models.Response:
        endpoint = "endpoints"
        url = f"{self.url_base}/{endpoint}"
        args = locals()
        query = build_query(args)
        if query is None:
            raise Exception("Must provide at least one query parameter")
        return self.session.get(f"{url}?{query}")


class AH:
    def __init__(
        self,
        api_version="v1",
        server="wax.api.atomicassets.io",
    ):
        self.limit = 100
        self.api_version = api_version  # use v2 apis unless explicitely overriden
        self.server = server
        self.url_base = f"https://{self.server}/atomicassets/{self.api_version}"
        self.session = requests.Session()
    
    def get_resp_ah(self,url: str) -> requests.models.Response:
    
        resp = self.session.get(url,timeout=15)
        resp.raise_for_status()
        return resp

    
    def templates(
        self,
        collection_name: str = None,
        schema_name: str = "crptomonkeys",
        page: int = None,
        limit: str = None,
    ) -> requests.models.Response:
        endpoint = inspect.currentframe().f_code.co_name
        url = f"{self.url_base}/{endpoint}"
        args = locals()
        query = build_query(args)
        if query is None:
            raise Exception("Must provide at least one query parameter")
        return self.get_resp_ah(f"{url}?{query}")

    def assets(
        self,
        collection_name: str = "crptomonkeys",
        schema_name: str = None,
        owner: str = None,
        page: int = 1,
        ids: str = None,
        limit: int = 1000,
        sort: str = "minted",
        order: str = "desc",
    ) -> requests.models.Response:
        endpoint = inspect.currentframe().f_code.co_name
        url = f"{self.url_base}/{endpoint}"
        args = locals()
        query = build_query(args)
        if query is None:
            raise Exception("Must provide at least one query parameter")
        return self.get_resp_ah(f"{url}?{query}")