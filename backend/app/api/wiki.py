"""
Wiki API - 知识库
支持：图片、浏览量、评论、点赞
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func as sql_func
from typing import List, Optional
from ..database import get_db
from ..models.user import User
from ..models.wiki import WikiDirection, WikiPage, WikiRevision, WikiComment, WikiLike
from ..models.audit import AuditAction
from ..schemas.wiki import (
    WikiDirectionCreate, WikiDirectionUpdate, WikiDirectionResponse,
    WikiPageCreate, WikiPageUpdate, WikiPageResponse,
    WikiRevisionCreate, WikiRevisionResponse,
    WikiCommentCreate, WikiCommentResponse
)
from ..services.auth import get_current_user, get_current_admin
from ..services.audit import AuditService
from pydantic import BaseModel

router = APIRouter()


# ============ Directions ============

@router.get("/directions", response_model=List[WikiDirectionResponse])
def list_directions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    directions = db.query(WikiDirection).options(
        joinedload(WikiDirection.pages).joinedload(WikiPage.likes)
    ).order_by(WikiDirection.name).all()
    
    result = []
    for direction in directions:
        pages_data = []
        for page in direction.pages:
            pages_data.append({
                "id": page.id,
                "title": page.title,
                "direction_id": page.direction_id,
                "parent_id": page.parent_id,
                "current_revision_id": page.current_revision_id,
                "view_count": page.view_count or 0,
                "like_count": len(page.likes) if page.likes else 0,
                "user_liked": False,
                "comments": [],
                "created_at": page.created_at,
                "updated_at": page.updated_at,
                "current_revision": None
            })
        result.append({
            "id": direction.id,
            "name": direction.name,
            "description": direction.description,
            "icon": direction.icon,
            "pages": pages_data,
            "created_at": direction.created_at,
            "updated_at": direction.updated_at
        })
    return result


@router.get("/directions/{direction_id}", response_model=WikiDirectionResponse)
def get_direction(
    direction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    direction = db.query(WikiDirection).options(
        joinedload(WikiDirection.pages).joinedload(WikiPage.likes),
        joinedload(WikiDirection.pages).joinedload(WikiPage.revisions)
    ).filter(WikiDirection.id == direction_id).first()

    if not direction:
        raise HTTPException(status_code=404, detail="Direction not found")

    # 构建响应，包含 like_count
    pages_data = []
    for page in direction.pages:
        page_dict = {
            "id": page.id,
            "title": page.title,
            "direction_id": page.direction_id,
            "parent_id": page.parent_id,
            "current_revision_id": page.current_revision_id,
            "view_count": page.view_count or 0,
            "like_count": len(page.likes) if page.likes else 0,
            "user_liked": False,
            "comments": [],
            "created_at": page.created_at,
            "updated_at": page.updated_at,
            "current_revision": None
        }
        if page.current_revision_id:
            rev = db.query(WikiRevision).options(
                joinedload(WikiRevision.created_by)
            ).filter(WikiRevision.id == page.current_revision_id).first()
            if rev:
                page_dict["current_revision"] = rev
        pages_data.append(page_dict)

    return {
        "id": direction.id,
        "name": direction.name,
        "description": direction.description,
        "icon": direction.icon,
        "pages": pages_data,
        "created_at": direction.created_at,
        "updated_at": direction.updated_at
    }


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


# ============ Pages ============

@router.get("/pages/{page_id}", response_model=WikiPageResponse)
def get_page(
    page_id: int,
    increment_view: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    page = db.query(WikiPage).options(
        joinedload(WikiPage.comments).joinedload(WikiComment.created_by),
        joinedload(WikiPage.likes),
        joinedload(WikiPage.created_by)
    ).filter(WikiPage.id == page_id).first()

    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    # 增加浏览量
    if increment_view:
        page.view_count = (page.view_count or 0) + 1
        db.commit()

    if page.current_revision_id:
        page.current_revision = db.query(WikiRevision).options(
            joinedload(WikiRevision.created_by)
        ).filter(WikiRevision.id == page.current_revision_id).first()

    # 检查当前用户是否已点赞
    user_liked = db.query(WikiLike).filter(
        WikiLike.page_id == page_id,
        WikiLike.user_id == current_user.id
    ).first() is not None

    # 手动构建响应
    return {
        **page.__dict__,
        "current_revision": page.current_revision,
        "like_count": len(page.likes) if page.likes else 0,
        "user_liked": user_liked,
        "comments": page.comments or []
    }


@router.post("/pages", response_model=WikiPageResponse)
def create_page(
    page_data: WikiPageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    page = WikiPage(
        direction_id=page_data.direction_id,
        title=page_data.title,
        parent_id=page_data.parent_id,
        view_count=0,
        created_by_id=current_user.id  # 记录创建者
    )
    db.add(page)
    db.flush()

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

    return get_page(page.id, increment_view=False, db=db, current_user=current_user)


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
    return get_page(page.id, increment_view=False, db=db, current_user=current_user)


@router.delete("/pages/{page_id}")
def delete_page(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    page = db.query(WikiPage).filter(WikiPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    # 允许创建者或管理员删除
    from ..models.user import UserRole
    if page.created_by_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only creator or admin can delete this page")

    # 先删除关联数据（revisions, comments, likes）
    db.query(WikiRevision).filter(WikiRevision.page_id == page_id).delete(synchronize_session=False)
    db.query(WikiComment).filter(WikiComment.page_id == page_id).delete(synchronize_session=False)
    db.query(WikiLike).filter(WikiLike.page_id == page_id).delete(synchronize_session=False)

    db.delete(page)
    db.commit()
    return {"message": "Page deleted"}


# ============ Revisions ============

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

    max_version = db.query(WikiRevision).filter(WikiRevision.page_id == page_id).count()

    revision = WikiRevision(
        page_id=page_id,
        content=revision_data.content,
        version=max_version + 1,
        created_by_id=current_user.id
    )
    db.add(revision)
    db.flush()

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


# ============ Comments (评论) ============

@router.get("/pages/{page_id}/comments", response_model=List[WikiCommentResponse])
def list_comments(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    comments = db.query(WikiComment).options(
        joinedload(WikiComment.created_by),
        joinedload(WikiComment.replies).joinedload(WikiComment.created_by)
    ).filter(
        WikiComment.page_id == page_id,
        WikiComment.parent_id == None  # 只获取顶级评论
    ).order_by(WikiComment.created_at.desc()).all()
    return comments


@router.post("/pages/{page_id}/comments", response_model=WikiCommentResponse)
def create_comment(
    page_id: int,
    comment_data: WikiCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    page = db.query(WikiPage).filter(WikiPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    comment = WikiComment(
        page_id=page_id,
        content=comment_data.content,
        parent_id=comment_data.parent_id,
        created_by_id=current_user.id
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return db.query(WikiComment).options(
        joinedload(WikiComment.created_by)
    ).filter(WikiComment.id == comment.id).first()


@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    comment = db.query(WikiComment).filter(WikiComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # 只有作者或管理员可以删除
    if comment.created_by_id != current_user.id and current_user.role.value != "ADMIN":
        raise HTTPException(status_code=403, detail="Not authorized")

    db.delete(comment)
    db.commit()
    return {"message": "Comment deleted"}


# ============ Likes (点赞) ============

class LikeResponse(BaseModel):
    liked: bool
    like_count: int


@router.post("/pages/{page_id}/like", response_model=LikeResponse)
def toggle_like(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """切换点赞状态（点赞/取消点赞）"""
    page = db.query(WikiPage).filter(WikiPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    existing_like = db.query(WikiLike).filter(
        WikiLike.page_id == page_id,
        WikiLike.user_id == current_user.id
    ).first()

    if existing_like:
        # 取消点赞
        db.delete(existing_like)
        db.commit()
        like_count = db.query(WikiLike).filter(WikiLike.page_id == page_id).count()
        return LikeResponse(liked=False, like_count=like_count)
    else:
        # 点赞
        like = WikiLike(page_id=page_id, user_id=current_user.id)
        db.add(like)
        db.commit()
        like_count = db.query(WikiLike).filter(WikiLike.page_id == page_id).count()
        return LikeResponse(liked=True, like_count=like_count)


@router.get("/pages/{page_id}/like")
def get_like_status(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的点赞状态"""
    like_count = db.query(WikiLike).filter(WikiLike.page_id == page_id).count()
    user_liked = db.query(WikiLike).filter(
        WikiLike.page_id == page_id,
        WikiLike.user_id == current_user.id
    ).first() is not None

    return {"liked": user_liked, "like_count": like_count}
