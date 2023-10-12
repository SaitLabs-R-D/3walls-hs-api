from fastapi import Request, Query


def pagintor(
    request: Request, page: int = Query(0, gt=-1), limit: int = Query(10, gt=0, lt=101)
):
    """
    pass this function to the dependencies parameter of a route to set the pagination parameters
    """
    request.state.page = page
    request.state.limit = limit
    request.state.offset = page * limit
