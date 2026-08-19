import uuid
from pathlib import Path
from fastapi.responses import FileResponse

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.manuscript import Manuscript
from app.models.user import User
from app.schemas.manuscript import (
    ManuscriptDetailResponse,
    ManuscriptResponse,
)
from app.services.document_service import extract_text


router = APIRouter(
    prefix="/api/manuscripts",
    tags=["Manuscripts"],
)


# --------------------------------------------------
# Upload directory
# --------------------------------------------------

UPLOAD_DIR = Path("uploads/manuscripts")

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# --------------------------------------------------
# Configuration
# --------------------------------------------------

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
}

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


# ==================================================
# 1. UPLOAD MANUSCRIPT
# ==================================================

@router.post(
    "/upload",
    response_model=ManuscriptResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_manuscript(
    title: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    # Validate title

    if not title.strip():

        raise HTTPException(
            status_code=400,
            detail="Title is required",
        )


    # Get original filename

    original_filename = (
        file.filename or ""
    )


    # Get extension

    extension = Path(
        original_filename
    ).suffix.lower()


    # Validate extension

    if extension not in ALLOWED_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail=(
                "Only PDF and DOCX files "
                "are supported"
            ),
        )


    # Read file

    file_content = await file.read()


    # Validate file size

    if len(file_content) > MAX_FILE_SIZE:

        raise HTTPException(
            status_code=400,
            detail="Maximum file size is 20 MB",
        )


    # Generate unique filename

    unique_filename = (
        f"{uuid.uuid4()}{extension}"
    )


    file_path = (
        UPLOAD_DIR /
        unique_filename
    )


    try:

        # Save file

        with open(
            file_path,
            "wb",
        ) as buffer:

            buffer.write(
                file_content
            )


        # Extract text

        extracted_text = extract_text(
            str(file_path),
            extension.replace(
                ".",
                "",
            ),
        )


    except Exception as error:

        # Delete file if processing fails

        if file_path.exists():

            file_path.unlink()


        raise HTTPException(
            status_code=400,
            detail=(
                f"Unable to process document: "
                f"{error}"
            ),
        )


    # Create database record

    manuscript = Manuscript(

        user_id=current_user.id,

        title=title.strip(),

        original_filename=original_filename,

        file_path=str(file_path),

        file_type=extension.replace(
            ".",
            "",
        ),

        file_size=len(file_content),

        extracted_text=extracted_text,

        status="uploaded",
    )


    db.add(manuscript)

    db.commit()

    db.refresh(manuscript)


    return manuscript


# ==================================================
# 2. LIST USER MANUSCRIPTS
# ==================================================

@router.get(
    "",
    response_model=list[ManuscriptResponse],
)
def get_manuscripts(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    manuscripts = (
        db.query(Manuscript)
        .filter(
            Manuscript.user_id
            == current_user.id
        )
        .order_by(
            Manuscript.created_at.desc()
        )
        .all()
    )

    return manuscripts


# ==================================================
# 3. GET SINGLE MANUSCRIPT
# ==================================================

@router.get(
    "/{manuscript_id}",
    response_model=ManuscriptDetailResponse,
)
def get_manuscript(
    manuscript_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    manuscript = (
        db.query(Manuscript)
        .filter(
            Manuscript.id
            == manuscript_id,

            Manuscript.user_id
            == current_user.id,
        )
        .first()
    )


    if not manuscript:

        raise HTTPException(
            status_code=404,
            detail="Manuscript not found",
        )


    return manuscript
# ==================================================
# 4. VIEW / DOWNLOAD MANUSCRIPT FILE
# ==================================================

@router.get(
    "/{manuscript_id}/file",
)
def view_manuscript_file(
    manuscript_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    manuscript = (
        db.query(Manuscript)
        .filter(
            Manuscript.id == manuscript_id,
            Manuscript.user_id == current_user.id,
        )
        .first()
    )

    if not manuscript:
        raise HTTPException(
            status_code=404,
            detail="Manuscript not found",
        )

    file_path = Path(
        manuscript.file_path
    )

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Manuscript file not found",
        )

    media_type = "application/octet-stream"

    if manuscript.file_type == "pdf":
        media_type = "application/pdf"

    elif manuscript.file_type == "docx":
        media_type = (
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        )

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=manuscript.original_filename,
        content_disposition_type="inline"
        if manuscript.file_type == "pdf"
        else "attachment",
    )

# ==================================================
# 5. DELETE MANUSCRIPT
# ==================================================

@router.delete(
    "/{manuscript_id}",
)
def delete_manuscript(
    manuscript_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    manuscript = (
        db.query(Manuscript)
        .filter(
            Manuscript.id
            == manuscript_id,

            Manuscript.user_id
            == current_user.id,
        )
        .first()
    )


    if not manuscript:

        raise HTTPException(
            status_code=404,
            detail="Manuscript not found",
        )


    # Delete physical file

    file_path = Path(
        manuscript.file_path
    )


    if file_path.exists():

        file_path.unlink()


    # Delete database record

    db.delete(manuscript)

    db.commit()


    return {
        "message": (
            "Manuscript deleted successfully"
        )
    }