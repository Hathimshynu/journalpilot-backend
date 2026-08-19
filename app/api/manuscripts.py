import uuid
import json
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

from app.models.manuscript_analysis import (
    ManuscriptAnalysis,
)

from app.services.ai_service import (
    analyze_manuscript,
)

from app.schemas.analysis import (
    AnalysisResponse,
    ManuscriptAnalysisResult,
)


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
# ANALYZE MANUSCRIPT
# ==================================================

@router.post(
    "/{manuscript_id}/analyze",
    response_model=AnalysisResponse,
)
def analyze_manuscript_endpoint(
    manuscript_id: int,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(get_db),
):

    # -----------------------------------------
    # Find manuscript
    # -----------------------------------------

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


    # -----------------------------------------
    # Check extracted text
    # -----------------------------------------

    if not manuscript.extracted_text:

        raise HTTPException(
            status_code=400,
            detail=(
                "No extracted text is available "
                "for this manuscript."
            ),
        )


    # -----------------------------------------
    # Run AI analysis
    # -----------------------------------------

    try:

        result = analyze_manuscript(
            manuscript.extracted_text
        )

    except Exception as error:

        print(
            "AI analysis error:",
            error,
        )

        raise HTTPException(
            status_code=503,
            detail=f"AI service unavailable: {str(error)}",
        )


    # -----------------------------------------
    # Check existing analysis
    # -----------------------------------------

    analysis = (
        db.query(ManuscriptAnalysis)
        .filter(
            ManuscriptAnalysis.manuscript_id
            == manuscript.id
        )
        .first()
    )


    analysis_json = (
        result.model_dump_json()
    )


    # -----------------------------------------
    # Update existing analysis
    # -----------------------------------------

    if analysis:

        analysis.overall_score = (
            result.overall_score
        )

        analysis.analysis_json = (
            analysis_json
        )


    # -----------------------------------------
    # Create new analysis
    # -----------------------------------------

    else:

        analysis = ManuscriptAnalysis(

            manuscript_id=manuscript.id,

            overall_score=(
                result.overall_score
            ),

            analysis_json=analysis_json,
        )

        db.add(analysis)


    db.commit()

    db.refresh(analysis)


    return {
        "id": analysis.id,

        "manuscript_id": (
            analysis.manuscript_id
        ),

        "overall_score": (
            analysis.overall_score
        ),

        "analysis": result,

        "created_at": (
            analysis.created_at.isoformat()
        ),
    }
    # -----------------------------------------------
    
@router.get(
    "/{manuscript_id}/analysis",
)
def get_manuscript_analysis(
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


    analysis = (
        db.query(ManuscriptAnalysis)
        .filter(
            ManuscriptAnalysis.manuscript_id
            == manuscript.id
        )
        .first()
    )


    if not analysis:

        raise HTTPException(
            status_code=404,
            detail="Analysis not found",
        )


    return {
        "id": analysis.id,

        "manuscript_id": (
            analysis.manuscript_id
        ),

        "overall_score": (
            analysis.overall_score
        ),

        "analysis": json.loads(
            analysis.analysis_json
        ),

        "created_at": (
            analysis.created_at.isoformat()
        ),
    }    
# ==================================================
# 4. VIEW / DOWNLOAD MANUSCRIPT FILE
# ==================================================

@router.get("/{manuscript_id}/file")

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