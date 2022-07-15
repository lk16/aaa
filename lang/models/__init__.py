from pydantic import BaseModel


class AaaModel(BaseModel):
    class Config:
        extra = "forbid"
