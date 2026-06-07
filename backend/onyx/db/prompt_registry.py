import hashlib
import random
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select, and_, update
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from onyx.db.models import PromptTemplate
from onyx.db.models import PromptVersion
from onyx.db.models import PromptAssignment


def fetch_prompt_templates(db_session: Session) -> list[PromptTemplate]:
    return list(db_session.scalars(select(PromptTemplate)).all())


def fetch_prompt_template_by_id(template_id: int, db_session: Session) -> PromptTemplate:
    template = db_session.scalar(select(PromptTemplate).where(PromptTemplate.id == template_id))
    if not template:
        raise ValueError(f"No prompt template with id {template_id}")
    return template


def insert_prompt_template(
    name: str,
    description: str | None,
    owner_user_id: UUID | None,
    db_session: Session,
) -> PromptTemplate:
    template = PromptTemplate(
        name=name,
        description=description,
        owner_user_id=owner_user_id,
    )
    db_session.add(template)
    try:
        db_session.commit()
    except IntegrityError:
        db_session.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"A prompt template with the name '{name}' already exists.",
        )
    return template


def update_prompt_template(
    template_id: int,
    name: str,
    description: str | None,
    db_session: Session,
) -> PromptTemplate:
    template = fetch_prompt_template_by_id(template_id, db_session)
    template.name = name
    template.description = description
    try:
        db_session.commit()
    except IntegrityError:
        db_session.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"A prompt template with the name '{name}' already exists.",
        )
    return template


def delete_prompt_template(
    template_id: int,
    db_session: Session,
) -> None:
    template = fetch_prompt_template_by_id(template_id, db_session)
    db_session.delete(template)
    db_session.commit()


def fetch_prompt_versions(template_id: int, db_session: Session) -> list[PromptVersion]:
    return list(
        db_session.scalars(
            select(PromptVersion)
            .where(PromptVersion.prompt_template_id == template_id)
            .order_by(PromptVersion.version_number.desc())
        ).all()
    )


def insert_prompt_version(
    template_id: int,
    content: str,
    created_by_user_id: UUID | None,
    db_session: Session,
) -> PromptVersion:
    # Find max version number
    max_version = db_session.scalar(
        select(PromptVersion.version_number)
        .where(PromptVersion.prompt_template_id == template_id)
        .order_by(PromptVersion.version_number.desc())
        .limit(1)
    )
    next_version = (max_version or 0) + 1

    version = PromptVersion(
        prompt_template_id=template_id,
        version_number=next_version,
        content=content,
        created_by_user_id=created_by_user_id,
        is_active=False,
    )
    db_session.add(version)
    db_session.commit()
    return version


def set_prompt_versions_traffic(
    template_id: int,
    traffic_allocations: dict[int, float],
    db_session: Session,
) -> None:
    total_traffic = sum(traffic_allocations.values())
    if total_traffic > 0 and abs(total_traffic - 100.0) > 0.1:
        raise ValueError("Total traffic allocation must sum to 100%")

    stmt = (
        update(PromptVersion)
        .where(PromptVersion.prompt_template_id == template_id)
        .values(is_active=False, traffic_percentage=0.0)
    )
    db_session.execute(stmt)

    if total_traffic > 0:
        versions = db_session.scalars(
            select(PromptVersion).where(
                and_(
                    PromptVersion.prompt_template_id == template_id,
                    PromptVersion.id.in_(traffic_allocations.keys())
                )
            )
        ).all()
        
        found_ids = {v.id for v in versions}
        missing = set(traffic_allocations.keys()) - found_ids
        if missing:
            raise ValueError(f"Versions {missing} not found for template {template_id}")

        for version in versions:
            traffic = traffic_allocations[version.id]
            if traffic > 0:
                version.is_active = True
                version.traffic_percentage = traffic
            
    db_session.commit()


def fetch_prompt_assignments(template_id: int, db_session: Session) -> list[PromptAssignment]:
    return list(
        db_session.scalars(
            select(PromptAssignment).where(PromptAssignment.prompt_template_id == template_id)
        ).all()
    )


def upsert_prompt_assignment(
    template_id: int,
    target_type: str,
    target_id: str,
    db_session: Session,
) -> PromptAssignment:
    # Check if assignment for this target already exists
    assignment = db_session.scalar(
        select(PromptAssignment).where(
            and_(
                PromptAssignment.target_type == target_type,
                PromptAssignment.target_id == target_id,
            )
        )
    )
    if assignment:
        assignment.prompt_template_id = template_id
    else:
        assignment = PromptAssignment(
            prompt_template_id=template_id,
            target_type=target_type,
            target_id=target_id,
        )
        db_session.add(assignment)
    db_session.commit()
    return assignment


def fetch_effective_prompt(target_type: str, target_id: str, db_session: Session, chat_session_id: UUID | None = None) -> PromptVersion | None:
    """Finds the active PromptVersion for a given target, if an assignment exists."""
    assignment = db_session.scalar(
        select(PromptAssignment).where(
            and_(
                PromptAssignment.target_type == target_type,
                PromptAssignment.target_id == target_id,
            )
        )
    )
    if not assignment:
        return None

    active_versions = list(
        db_session.scalars(
            select(PromptVersion).where(
                and_(
                    PromptVersion.prompt_template_id == assignment.prompt_template_id,
                    PromptVersion.is_active == True,
                )
            ).order_by(PromptVersion.id)
        ).all()
    )
    
    if not active_versions:
        return None
        
    if len(active_versions) == 1:
        return active_versions[0]
        
    # A/B testing logic
    if chat_session_id:
        hash_val = int(hashlib.md5(str(chat_session_id).encode()).hexdigest(), 16)
        rand_val = (hash_val % 10000) / 100.0
    else:
        rand_val = random.uniform(0, 100)
        
    cumulative = 0.0
    for version in active_versions:
        cumulative += version.traffic_percentage
        if rand_val <= cumulative:
            return version
            
    return active_versions[-1]
