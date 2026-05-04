from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field


JsonPrimitive = Union[str, int, float, bool, None]


class TableData(BaseModel):
    headers: List[str]
    rows: List[List[JsonPrimitive]]


class ChartDataset(BaseModel):
    label: Optional[str] = None
    data: List[Union[int, float]]
    backgroundColor: Optional[List[str]] = None


class ChartPayload(BaseModel):
    labels: List[str]
    datasets: List[ChartDataset]


class ChartData(BaseModel):
    type: Literal["line", "bar", "pie"]
    data: ChartPayload


class TextPart(BaseModel):
    type: Literal["text"]
    data: str


class TablePart(BaseModel):
    type: Literal["table"]
    data: TableData


class ListPart(BaseModel):
    type: Literal["list"]
    data: List[str]


class ImagePart(BaseModel):
    type: Literal["image"]
    data: str


class VideoPart(BaseModel):
    type: Literal["video"]
    data: str


class ChartPart(BaseModel):
    type: Literal["chart"]
    data: ChartData


class HtmlPart(BaseModel):
    type: Literal["html"]
    data: str


class WcaxPart(BaseModel):
    type: Literal["wcax"]
    data: str


Part = Union[
    TextPart,
    TablePart,
    ListPart,
    ImagePart,
    VideoPart,
    ChartPart,
    HtmlPart,
    WcaxPart,
]

class Suggestion(BaseModel):
    title: str
    description: str

class ChatResponse(BaseModel):
    parts: List[Part]
    suggestions: List[Suggestion] = Field(default_factory=list)


class Thread_item(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    relevant: Optional[bool] = None
    content: ChatResponse
# class ChatResponse(BaseModel):
#     parts: List[Part]
#     suggestions: List[str] = Field(default_factory=list)


class ThreadCreateResponse(BaseModel):
    thread_id: str
    thread_data: List[Thread_item]

# class ThreadCreateResponse(BaseModel):
#     thread_id: str
#     thread_data: List[ChatResponse]

# class ThreadCreateResponse(BaseModel):
#     thread_id: str
