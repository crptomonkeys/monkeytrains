from sqlmodel import SQLModel, Field

class DropBase(SQLModel):
    handle: str
    type: str
    state: str
    issue_time: str
    day: str
    hour: int
    winner: str
    trx_id: str

class Drop(DropBase, table=True):
    id: int = Field(default=None, primary_key=True)


class DropCreate(DropBase):
    pass

