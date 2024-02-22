

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from sqlmodel import Session, SQLModel, create_engine
from models import Drop

from sqlalchemy import desc
import requests, ast, config

from sqlalchemy import update

engine = create_engine(
    'postgresql://postgres:postgres@db:5432/foo',
    pool_recycle=1800, pool_size=12)
db_session = scoped_session(sessionmaker(
    autocommit=False, autoflush=False, bind=engine))


def init_db():
    trying=True
    while trying:
        if engine:
            try:
                SQLModel.metadata.create_all(engine)

                trying=False
            except Exception as e:
                print(e)

def commit_or_rollback(new_obj):
    with Session(engine) as session:
        try:
            session.add(new_obj)
            session.commit()
            session.refresh(new_obj)
        except Exception as e:
            print(e, "rolling back")
            session.rollback()
            return None
        return new_obj

def update_done(handle,tx_id):
    with Session(engine) as session:
        try:
            stmt = update(Drop).where(Drop.handle == handle).values(trx_id=tx_id,state="DONE").execution_options(synchronize_session="fetch")
            result = session.execute(stmt)
            session.commit()
        except Exception as e:
            print(e, "rolling back")
            session.rollback()
            return None
        return True

def update_elected(handle,elected):
    with Session(engine) as session:
        try:
            stmt = update(Drop).where(Drop.handle == handle).values(winner=str(elected),state="ELECTED").execution_options(synchronize_session="fetch")
            result = session.execute(stmt)
            session.commit()
        except Exception as e:
            print(e, "rolling back")
            session.rollback()
            return None
        return True

def retrieve_drops(before:str=None,after:str=None,limit:int=100,sort:str='asc'):
    with Session(engine) as session:
        qry = session.query(
                        Drop.issue_time,
                        Drop.type,
                        Drop.winner,
                        Drop.trx_id,
                        Drop.state)

        qry = qry.filter(Drop.type=="roading")            
        if before:
            qry = qry.filter(Drop.issue_time<=before)
        if after:
            qry = qry.filter(Drop.issue_time>=after)
        
        if sort == 'desc':
            qry = qry.order_by(desc("issue_time"))
        else:
            qry = qry.order_by("issue_time")
        if limit:    
            qry = qry.limit(limit).distinct()
        else:
            qry = qry.limit(100).distinct()

        out=[
            {
                "issue_time" : q.issue_time,
                "type" : q.type,
                "winner" : [n.strip() for n in ast.literal_eval(q.winner)] if q.winner != "" else [],
                "trx_id" : q.trx_id,
                "state" : q.state
            }
            for q in qry
        ]
        return out
