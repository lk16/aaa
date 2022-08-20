from pydantic import BaseModel


class AaaModel(BaseModel):
    class Config:
        extra = "forbid"
        arbitrary_types_allowed = True  # TODO fix


class AaaTreeNode(AaaModel):
    class Config:
        frozen = True


class FunctionBodyItem(AaaTreeNode):
    ...
