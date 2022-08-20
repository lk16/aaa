from pydantic import BaseModel


class AaaModel(BaseModel):
    class Config:
        extra = "forbid"
        frozen = True
        arbitrary_types_allowed = True  # TODO fix


class AaaTreeNode(AaaModel):
    ...


class FunctionBodyItem(AaaTreeNode):
    ...
