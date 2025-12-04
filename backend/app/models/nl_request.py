# app/models/nl_request.py
from pydantic import BaseModel

class NLRequest(BaseModel):
    text: str
