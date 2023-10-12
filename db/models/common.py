from pydantic import BaseModel, Field, Extra
from helpers.fields import ObjectIdField
from functools import cache
from datetime import datetime
from bson import ObjectId
from enum import Enum
from typing import Union, Literal
from pymongo.collation import Collation


class DBModel(BaseModel):
    """
    !IMPORTANT!
    -----------

    Every model fields need to be ordered in alphabetical order.
    """

    id: ObjectIdField = Field(None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @classmethod
    @cache
    def __get_collection_name__(cls):
        return "".join(
            ["_" + c.lower() if c.isupper() else c for c in cls.__name__]
        ).lstrip("_")

    def dict(self, to_db: bool = False, *args, **kwargs):
        if to_db:
            self.updated_at = datetime.utcnow()

        if self.id is None and to_db:
            if "exclude" in kwargs:
                kwargs["exclude"].add("id")
            else:
                kwargs["exclude"] = {"id"}

        kwargs["by_alias"] = True
        return super().dict(*args, **kwargs)

    @classmethod
    def get_indexes(cls) -> list["MongoIndex"]:
        return []

    def __getitem__(self, key):
        if key == "_id":
            return self.id
        return getattr(self, key)

    def set_updated_at(self):
        self.updated_at = datetime.utcnow()

    class Config:
        extra = Extra.forbid
        json_encoders = {
            ObjectId: str,
        }
        anystr_strip_whitespace = True
        allow_population_by_field_name = True
        arbitrary_types_allowed = True

    class Fields(str, Enum):
        id = "_id"
        created_at = "created_at"
        updated_at = "updated_at"


def add_update_at_to_update(update: Union[list[dict], dict]) -> Union[list[dict], dict]:
    if isinstance(update, list):
        update.append({"$set": {DBModel.Fields.updated_at.value: datetime.utcnow()}})
    else:
        update["$currentDate"] = update.get("$currentDate", {})
        update["$currentDate"][DBModel.Fields.updated_at.value] = {"$type": "date"}
    return update


class MongoIndex:
    def __init__(self, name) -> None:
        self.name = name
        self.fields = []
        self.unique = False
        self._blocked = False
        self.collation = None

    def add_field(self, field: str, order: Literal[1, -1, "text"]):
        if order not in [1, -1, "text"]:
            raise Exception("order must be 1, -1 or 'text'")
        if self._blocked:
            raise Exception("You can't add more fields to this index")
        self.fields.append((field, order))
        return self

    def set_unique(self):
        self.unique = True
        self._blocked = True
        return self

    def set_collation(
        self,
        locale: str,
        strength: Literal[1, 2, 3, 4, 5],
        caseLevel: bool = False,
        caseFirst: Literal["upper", "lower", "off"] = "off",
        numericOrdering: bool = False,
        alternate: Literal["shifted", "non-ignorable"] = "non-ignorable",
        maxVariable: Literal["punct", "space"] = "punct",
        # Fields can be in hebrew so we need to use normalization
        normalization: bool = True,
    ):

        self.collation = Collation(
            locale=locale,
            strength=strength,
            caseLevel=caseLevel,
            caseFirst=caseFirst,
            numericOrdering=numericOrdering,
            alternate=alternate,
            maxVariable=maxVariable,
            normalization=normalization,
        )

        return self
