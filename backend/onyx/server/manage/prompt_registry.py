from datetime import datetime
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from onyx.auth.users import current_curator_or_admin_user
from onyx.db.engine.sql_engine import get_session
from onyx.db.models import User
from onyx.db.prompt_registry import fetch_prompt_assignments
from onyx.db.prompt_registry import fetch_prompt_template_by_id
from onyx.db.prompt_registry import fetch_prompt_templates
from onyx.db.prompt_registry import fetch_prompt_versions
from onyx.db.prompt_registry import insert_prompt_template
from onyx.db.prompt_registry import insert_prompt_version
from onyx.db.prompt_registry import set_prompt_versions_traffic
from onyx.db.prompt_registry import update_prompt_template
from onyx.db.prompt_registry import upsert_prompt_assignment
from onyx.server.models import StatusResponse

router = APIRouter(prefix="/manage/prompt-registry")


class PromptTemplateCreate(BaseModel):
    name: str
    description: str | None = None


class PromptTemplateUpdate(BaseModel):
    name: str
    description: str | None = None


class PromptTemplateResponse(BaseModel):
    id: int
    name: str
    description: str | None
    owner_user_id: UUID | None
    created_at: datetime
    updated_at: datetime


class PromptVersionCreate(BaseModel):
    content: str


class PromptVersionResponse(BaseModel):
    id: int
    prompt_template_id: int
    version_number: int
    content: str
    created_by_user_id: UUID | None
    created_at: datetime
    is_active: bool
    traffic_percentage: float

class PromptTrafficAllocation(BaseModel):
    version_id: int
    traffic_percentage: float

class PromptTrafficAllocationsRequest(BaseModel):
    allocations: list[PromptTrafficAllocation]


class PromptAssignmentCreate(BaseModel):
    target_type: str
    target_id: str


class PromptAssignmentResponse(BaseModel):
    id: int
    prompt_template_id: int
    target_type: str
    target_id: str
    created_at: datetime


@router.get("/templates")
def get_templates(
    _: User = Depends(current_curator_or_admin_user),
    db_session: Session = Depends(get_session),
) -> list[PromptTemplateResponse]:
    return [
        PromptTemplateResponse(
            id=t.id,
            name=t.name,
            description=t.description,
            owner_user_id=t.owner_user_id,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in fetch_prompt_templates(db_session)
    ]


@router.post("/templates")
def create_template(
    template_req: PromptTemplateCreate,
    user: User = Depends(current_curator_or_admin_user),
    db_session: Session = Depends(get_session),
) -> PromptTemplateResponse:
    t = insert_prompt_template(
        name=template_req.name,
        description=template_req.description,
        owner_user_id=user.id,
        db_session=db_session,
    )
    return PromptTemplateResponse(
        id=t.id,
        name=t.name,
        description=t.description,
        owner_user_id=t.owner_user_id,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


@router.patch("/templates/{template_id}")
def update_template_endpoint(
    template_id: int,
    template_req: PromptTemplateUpdate,
    _: User = Depends(current_curator_or_admin_user),
    db_session: Session = Depends(get_session),
) -> PromptTemplateResponse:
    t = update_prompt_template(
        template_id=template_id,
        name=template_req.name,
        description=template_req.description,
        db_session=db_session,
    )
    return PromptTemplateResponse(
        id=t.id,
        name=t.name,
        description=t.description,
        owner_user_id=t.owner_user_id,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


@router.delete("/templates/{template_id}")
def delete_template_endpoint(
    template_id: int,
    _: User = Depends(current_curator_or_admin_user),
    db_session: Session = Depends(get_session),
) -> StatusResponse:
    from onyx.db.prompt_registry import delete_prompt_template
    delete_prompt_template(template_id, db_session)
    return StatusResponse(success=True, message="Prompt template deleted.")


@router.get("/templates/{template_id}/versions")
def get_template_versions(
    template_id: int,
    _: User = Depends(current_curator_or_admin_user),
    db_session: Session = Depends(get_session),
) -> list[PromptVersionResponse]:
    return [
        PromptVersionResponse(
            id=v.id,
            prompt_template_id=v.prompt_template_id,
            version_number=v.version_number,
            content=v.content,
            created_by_user_id=v.created_by_user_id,
            created_at=v.created_at,
            is_active=v.is_active,
            traffic_percentage=v.traffic_percentage,
        )
        for v in fetch_prompt_versions(template_id, db_session)
    ]


@router.post("/templates/{template_id}/versions")
def create_template_version(
    template_id: int,
    version_req: PromptVersionCreate,
    user: User = Depends(current_curator_or_admin_user),
    db_session: Session = Depends(get_session),
) -> PromptVersionResponse:
    v = insert_prompt_version(
        template_id=template_id,
        content=version_req.content,
        created_by_user_id=user.id,
        db_session=db_session,
    )
    return PromptVersionResponse(
        id=v.id,
        prompt_template_id=v.prompt_template_id,
        version_number=v.version_number,
        content=v.content,
        created_by_user_id=v.created_by_user_id,
        created_at=v.created_at,
        is_active=v.is_active,
        traffic_percentage=v.traffic_percentage,
    )

@router.post("/templates/{template_id}/traffic")
def update_traffic(
    template_id: int,
    req: PromptTrafficAllocationsRequest,
    _: User = Depends(current_curator_or_admin_user),
    db_session: Session = Depends(get_session),
) -> StatusResponse:
    alloc_dict = {a.version_id: a.traffic_percentage for a in req.allocations}
    set_prompt_versions_traffic(template_id, alloc_dict, db_session)
    return StatusResponse(success=True, message="Traffic allocations updated.")


@router.get("/templates/{template_id}/assignments")
def get_template_assignments(
    template_id: int,
    _: User = Depends(current_curator_or_admin_user),
    db_session: Session = Depends(get_session),
) -> list[PromptAssignmentResponse]:
    return [
        PromptAssignmentResponse(
            id=a.id,
            prompt_template_id=a.prompt_template_id,
            target_type=a.target_type,
            target_id=a.target_id,
            created_at=a.created_at,
        )
        for a in fetch_prompt_assignments(template_id, db_session)
    ]


@router.post("/templates/{template_id}/assignments")
def create_template_assignment(
    template_id: int,
    assignment_req: PromptAssignmentCreate,
    _: User = Depends(current_curator_or_admin_user),
    db_session: Session = Depends(get_session),
) -> PromptAssignmentResponse:
    a = upsert_prompt_assignment(
        template_id=template_id,
        target_type=assignment_req.target_type,
        target_id=assignment_req.target_id,
        db_session=db_session,
    )
    return PromptAssignmentResponse(
        id=a.id,
        prompt_template_id=a.prompt_template_id,
        target_type=a.target_type,
        target_id=a.target_id,
        created_at=a.created_at,
    )
