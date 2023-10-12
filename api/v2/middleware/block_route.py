from fastapi import HTTPException


def block_this_route(func):
    """
    use this function to block a route that is not in use yet and maybe will be in the future
    """

    def inner_func():

        raise HTTPException(
            status_code=403, detail={"message": "This route is not in use yet"}
        )

    return inner_func
