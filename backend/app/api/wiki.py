from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from ..database import get_db
from ..models.user import User
from ..models.wiki import WikiDirection, WikiPage, WikiRevision
from ..models.audit import AuditAction
from ..schemas.wiki import (
    WikiDirectionCreate, WikiDirectionUpdate, WikiDirectionResponse,
    WikiPageCreate, WikiPageUpdate, WikiPageResponse,
    WikiRevisionCreate, WikiRevisionResponse
)
from ..services.auth import get_current_user, get_current_admin
from ..services.audit import AuditService

router = APIRouter()


# Directions
@router.get("/directions", response_model=List[WikiDirectionResponse])
def list_directions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    directions = db.query(WikiDirection).options(
        joinedload(WikiDirection.pages)
    ).order_by(WikiDirection.name).all()
    return directions


@router.get("/directions/{direction_id}", response_model=WikiDirectionResponse)
def get_direction(
    direction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    direction = db.query(WikiDirection).options(
        joinedload(WikiDirection.pages).joinedload(WikiPage.revisions)
    ).filter(WikiDirection.id == direction_id).first()

    if not direction:
        raise HTTPException(status_code=404, detail="Direction not found")

    # Load current revision for each page
    for page in direction.pages:
        if page.current_revision_id:
            page.current_revision = db.query(WikiRevision).options(
                joinedload(WikiRevision.created_by)
            ).filter(WikiRevision.id == page.current_revision_id).first()

    return direction


@router.post("/directions", response_model=WikiDirectionResponse)
def create_direction(
    direction_data: WikiDirectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    direction = WikiDirection(
        name=direction_data.name,
        description=direction_data.description,
        icon=direction_data.icon
    )
    db.add(direction)
    db.commit()
    db.refresh(direction)

    AuditService.log(db, AuditAction.WIKI_CREATE, "WikiDirection", direction.id, current_user,
                     new_value={"name": direction.name})

    return direction


@router.put("/directions/{direction_id}", response_model=WikiDirectionResponse)
def update_direction(
    direction_id: int,
    direction_data: WikiDirectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    direction = db.query(WikiDirection).filter(WikiDirection.id == direction_id).first()
    if not direction:
        raise HTTPException(status_code=404, detail="Direction not found")

    if direction_data.name is not None:
        direction.name = direction_data.name
    if direction_data.description is not None:
        direction.description = direction_data.description
    if direction_data.icon is not None:
        direction.icon = direction_data.icon

    db.commit()

    return get_direction(direction.id, db, current_user)


@router.delete("/directions/{direction_id}")
def delete_direction(
    direction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    direction = db.query(WikiDirection).filter(WikiDirection.id == direction_id).first()
    if not direction:
        raise HTTPException(status_code=404, detail="Direction not found")

    db.delete(direction)
    db.commit()

    return {"message": "Direction deleted"}


# Pages
@router.get("/pages/{page_id}", response_model=WikiPageResponse)
def get_page(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    page = db.query(WikiPage).filter(WikiPage.id == page_id).first()

    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    if page.current_revision_id:
        page.current_revision = db.query(WikiRevision).options(
            joinedload(WikiRevision.created_by)
        ).filter(WikiRevision.id == page.current_revision_id).first()

    return page


@router.post("/pages", response_model=WikiPageResponse)
def create_page(
    page_data: WikiPageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    page = WikiPage(
        direction_id=page_data.direction_id,
        title=page_data.title,
        parent_id=page_data.parent_id
    )
    db.add(page)
    db.flush()

    # Create initial revision if content provided
    if page_data.content:
        revision = WikiRevision(
            page_id=page.id,
            content=page_data.content,
            version=1,
            created_by_id=current_user.id
        )
        db.add(revision)
        db.flush()
        page.current_revision_id = revision.id

    db.commit()
    db.refresh(page)

    AuditService.log(db, AuditAction.WIKI_CREATE, "WikiPage", page.id, current_user,
                     new_value={"title": page.title})

    return get_page(page.id, db, current_user)


@router.put("/pages/{page_id}", response_model=WikiPageResponse)
def update_page(
    page_id: int,
    page_data: WikiPageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    page = db.query(WikiPage).filter(WikiPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    if page_data.title is not None:
        page.title = page_data.title
    if page_data.parent_id is not None:
        page.parent_id = page_data.parent_id

    db.commit()

    return get_page(page.id, db, current_user)


@router.delete("/pages/{page_id}")
def delete_page(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    page = db.query(WikiPage).filter(WikiPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    db.delete(page)
    db.commit()

    return {"message": "Page deleted"}


# Revisions
@router.get("/pages/{page_id}/revisions", response_model=List[WikiRevisionResponse])
def list_revisions(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    revisions = db.query(WikiRevision).options(
        joinedload(WikiRevision.created_by)
    ).filter(WikiRevision.page_id == page_id).order_by(WikiRevision.version.desc()).all()
    return revisions


@router.post("/pages/{page_id}/revisions", response_model=WikiRevisionResponse)
def create_revision(
    page_id: int,
    revision_data: WikiRevisionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    page = db.query(WikiPage).filter(WikiPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    # Get next version number
    max_version = db.query(WikiRevision).filter(
        WikiRevision.page_id == page_id
    ).count()

    # Revisions are append-only
    revision = WikiRevision(
        page_id=page_id,
        content=revision_data.content,
        version=max_version + 1,
        created_by_id=current_user.id
    )
    db.add(revision)
    db.flush()

    # Update page's current revision
    page.current_revision_id = revision.id

    db.commit()
    db.refresh(revision)

    AuditService.log(db, AuditAction.WIKI_UPDATE, "WikiPage", page.id, current_user,
                     new_value={"revision": revision.version})

    return db.query(WikiRevision).options(
        joinedload(WikiRevision.created_by)
    ).filter(WikiRevision.id == revision.id).first()


@router.get("/revisions/{revision_id}", response_model=WikiRevisionResponse)
def get_revision(
    revision_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    revision = db.query(WikiRevision).options(
        joinedload(WikiRevision.created_by)
    ).filter(WikiRevision.id == revision_id).first()

    if not revision:
        raise HTTPException(status_code=404, detail="Revision not found")
    return revision
