from db.models.common import DBModel
from typing import Type, Union, Literal


def lookup(
    from_: Type[DBModel],
    local_field: str,
    foreign_field: str,
    as_: str,
    pipeline: list = [],
    let: dict = {},
):
    """
    Description:
    ------------
        Define a lookup aggregation stage. (sql: join)

    Parameters:
    -----------
        `from_` Type[DBModel]
            The model to lookup from.
        `local_field` str
            The field in the current model to match.
        `foreign_field` str
            The field in the `from_` model to match.
        `as_` str
            The name of the field to store the result in.
        `pipeline` list
            An optional pipeline to apply to the lookup. (pipeline is a list of aggregation stages)
    Returns:
    --------
        `dict`
            The lookup aggregation stage.
    """
    return {
        "$lookup": {
            "from": from_.__get_collection_name__(),
            "localField": local_field,
            "foreignField": foreign_field,
            "as": as_,
            "let": let,
            "pipeline": pipeline,
        }
    }


def unwind(path: str, preserve: bool = False):
    """
    Description:
    ------------
        Define an unwind aggregation stage. (sql: unnest)
        Basically, it flattens an array field into a json object.

    Parameters:
    -----------
        `path` str
            The field to unwind.
        `preserve` bool
            Whether to preserve null and empty arrays documents.
    Returns:
    --------
        `dict`
            The unwind aggregation stage.
    """
    return {
        "$unwind": {
            "path": f"${path}",
            "preserveNullAndEmptyArrays": preserve,
        }
    }


def match_query(query: dict):
    """
    Description:
    ------------
        Define a match aggregation stage. (sql: where)

    Parameters:
    -----------
        `query` dict
            The query to match.
    Returns:
    --------
        `dict`
            The match aggregation stage.
    """
    return {
        "$match": query,
    }


def unset(*fields: str):
    """
    Description:
    ------------
        Define an unset aggregation stage - fields to remove from the result.

    Parameters:
    -----------
        `*fields` str
            Any number of fields to remove from the result.
    Returns:
    --------
        `dict`
            The unset aggregation stage.
    """
    return {
        "$unset": fields,
    }


def to_string(field: str):
    """
    Description:
    ------------
        Define a to_string aggregation stage - fields to convert to string.
        use the given field name as the new field name.

    Parameters:
    -----------
        `field` str
            The field to convert to string.
    Returns:
    --------
        `dict`
            The to_string aggregation stage.
    """
    return {field: {"$toString": f"${field}"}}


def project(
    keep: list[str], exclude_id: bool = False, **fields: dict[str, Union[dict, int]]
):
    """
    Description:
    ------------
        Define a project aggregation stage - fields to include in the result.
        To include a field, pass the field name as a string in the `keep` list.
        To exclude a field, use the field name as the key and the value 0.
        To rename a field, use the new field name as the key and $old_field_name as the value.
        To add a field, use the new field name as the key and the value as the field value.

    Parameters:
    -----------
        `keep` list[str]
            The fields to include in the result.
        `exclude_id` bool
            Whether to remove the _id field.
        `**fields` dict
            Any number of fields and valid project operators.
    Returns:
    --------
        `dict`
            The project aggregation stage.
    """
    return {
        "$project": {
            "_id": 0 if exclude_id else 1,
            **{field: 1 for field in keep},
            **fields,
        }
    }


def add_fields(**fields: dict):
    """
    Description:
    ------------
        Define an add_fields aggregation stage - fields to add to the result.
        To add a field, use the new field name as the key and the value as the field value.
        To use a value from another field, use $field_name as the value.

    Parameters:
    -----------
        `**fields` dict
            Any number of fields to add to the result.
    Returns:
    --------
        `dict`
            The add_fields aggregation stage.
    """
    return {
        "$addFields": fields,
    }


def skip(count: int):
    """
    Description:
    ------------
        Define a skip aggregation stage - how many documents to skip.

    Parameters:
    -----------
        `count` int
            The number of documents to skip.
    Returns:
    --------
        `dict`
            The skip aggregation stage.
    """
    return {
        "$skip": count,
    }


def limit(count: int):
    """
    Description:
    ------------
        Define a limit aggregation stage - how many documents to return.

    Parameters:
    -----------
        `count` int
            The number of documents to return.
    Returns:
    --------
        `dict`
            The limit aggregation stage.
    """
    return {
        "$limit": count,
    }


def sort(fields: dict[str, Literal[1, -1]]):
    """
    Description:
    ------------
        Define a sort aggregation stage - how to sort the documents.
        To sort ascending, use the field name as the dict key and the value 1.
        To sort descending, use the field name as the dict key and the value -1.

    Parameters:
    -----------
        `fields`
            Dict of fields to sort by and the sort order.
    Returns:
    --------
        `dict`
            The sort aggregation stage.
    """
    return {
        "$sort": fields,
    }


def count(key: str):
    """
    Description:
    ------------
        Define a count aggregation stage - to return the number of documents.
        After passing the count stage, the result will be a single document with the count in the given key.

    Parameters:
    -----------
        `key` str
            The key to store the count in.
    Returns:
    --------
        `dict`
            The count aggregation stage.
    """
    return {
        "$count": key,
    }


def group(fields: dict[str, Union[dict, str]]):
    """
    Description:
    ------------
        Define a group aggregation stage - to group documents by a field.
        To group by a field, use the field name as the dict key and the value as the group operator.

    Parameters:
    -----------
        `fields` dict
            Dict of fields to group by and the group operator.
    Returns:
    --------
        `dict`
            The group aggregation stage.
    """
    return {
        "$group": fields,
    }


def replace_root(new_root: str):
    """
    Description:
    ------------
        Define a replace_root aggregation stage - to replace the root document with the given field.

    Parameters:
    -----------
        `new_root` str
            The field to replace the root document with.
    Returns:
    --------
        `dict`
            The replace_root aggregation stage.
    """
    return {
        "$replaceRoot": {
            "newRoot": f"${new_root}",
        }
    }


def facet(**fields: list[dict]):
    """
    Description:
    ------------
        Define a facet aggregation stage - to run multiple aggregations in parallel.
        To run multiple aggregations in parallel, pass the aggregation stages as a list of dicts.

    Parameters:
    -----------
        `*stages` list[dict]
            Any number of aggregation stages.
    Returns:
    --------
        `dict`
            The facet aggregation stage.
    """
    return {
        "$facet": fields,
    }


def convert_to_string_safe(field: str) -> dict:
    return {
        "$convert": {
            "input": field,
            "to": "string",
            # onError: <expression>
            "onNull": "null",
        }
    }


def safe_array_size(field: str) -> dict:
    return {
        "$cond": [
            {"$isArray": field},
            {"$size": field},
            0,
        ]
    }


def get_week_diffrance_between_dates(field: str, field2: str = "$$NOW") -> dict:
    return {
        "$ceil": {
            "$divide": [
                {
                    "$subtract": [
                        field2,
                        field,
                    ]
                },
                # 604800000 is the number of milliseconds in a week
                604800000,
            ]
        }
    }


def add_to_date(date: Union[str, dict], unit: str, amont) -> dict:
    """
    date: Any valid mongodb expression that returns a date.
    unit: The unit to add to the date.
        Can be one of the following: year, quarter, month, week, day, hour, minute, second, millisecond.
    amount: The amount to add to the date, any valid mongodb expression that returns a number.
    """
    return {
        "$dateAdd": {
            "startDate": date,
            "unit": unit,
            "amount": amont,
        }
    }


def union_with(collection: Type[DBModel], pipeline: list[dict] = []) -> dict:
    """
    collection: The db model of the collection to union with.
    pipeline: The pipeline to run on the collection.
    """
    return {
        "$unionWith": {
            "coll": collection.__get_collection_name__(),
            "pipeline": pipeline,
        }
    }
