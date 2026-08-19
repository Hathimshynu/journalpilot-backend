from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ManuscriptResponse(BaseModel):

    id: int

    title: str

    original_filename: str

    file_type: str

    file_size: int

    status: str

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class ManuscriptDetailResponse(
    ManuscriptResponse
):

    extracted_text: str | None = None