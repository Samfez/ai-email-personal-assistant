from pydantic import BaseModel, Field


class Sender(BaseModel):
    email: str
    name: str


class Attachment(BaseModel):
    content_disposition: str | None = None
    content_id: str | None = None
    content_type: str
    filename: str
    grant_id: str
    id: str
    is_inline: bool = False
    size: int


class EmailObject(BaseModel):
    attachments: list[Attachment] = []
    bcc: list = []
    body: str
    cc: list = []
    date: int
    folders: list = []
    from_: list[Sender] = Field(..., alias="from")
    grant_id: str
    id: str
    object: str
    reply_to: list = []
    snippet: str
    starred: bool
    subject: str
    thread_id: str
    to: list
    unread: bool