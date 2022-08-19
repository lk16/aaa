from pydantic import BaseModel


class AaaModel(BaseModel):
    class Config:
        extra = "forbid"


class AaaTreeNode(AaaModel):
    class Config:
        frozen = True


class FunctionBodyItem(AaaTreeNode):
    ...
