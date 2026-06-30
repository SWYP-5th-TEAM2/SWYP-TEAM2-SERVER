from app.schemas.common import CamelModel


class PlaceSearchResult(CamelModel):
    provider: str
    place_name: str
    address: str
    latitude: float
    longitude: float


class PlaceSearchPageInfo(CamelModel):
    page: int
    size: int
    total_count: int


class PlaceSearchResponse(CamelModel):
    provider: str
    keyword: str
    search_results: list[PlaceSearchResult]
    page_info: PlaceSearchPageInfo
