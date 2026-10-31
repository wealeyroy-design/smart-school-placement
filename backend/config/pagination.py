from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Default page of 50, but lets the frontend ask for larger pages with
    ?page_size=N (capped), e.g. a school administrator's full school list."""

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 1000
