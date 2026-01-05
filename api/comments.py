from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from models import Comment, Post, User
from schemas import CommentCreate, CommentOut
from db import get_async_db
from fastapi.responses import JSONResponse
from utils.dependencies import get_current_user
from typing import Optional, List

router = APIRouter()


def build_comment_tree(comments: List[Comment], parent_id: Optional[int] = None) -> List[dict]:
    """Build a hierarchical comment tree"""
    result = []
    for comment in comments:
        if comment.parent_id == parent_id:
            comment_dict = {
                "id": comment.id,
                "post_id": comment.post_id,
                "parent_id": comment.parent_id,
                "author_name": comment.author_name,
                "author_email": comment.author_email,
                "content": comment.content,
                "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M:%S") if comment.created_at else "",
                "replies": build_comment_tree(comments, comment.id)
            }
            result.append(comment_dict)
    return result


@router.get("/posts/{post_id}/comments")
async def get_post_comments(
    post_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Get all comments for a post with hierarchical structure"""
    try:
        # Check if post exists
        post_result = await db.execute(select(Post).where(Post.id == post_id))
        post = post_result.scalar_one_or_none()
        
        if not post:
            return JSONResponse(
                status_code=404,
                content={"code": 404, "data": {}, "msg": "post not found"}
            )
        
        # Get all comments for this post
        stmt = (
            select(Comment)
            .where(Comment.post_id == post_id)
            .order_by(Comment.created_at.asc())
        )
        result = await db.execute(stmt)
        comments = result.scalars().all()
        
        # Build hierarchical tree
        comment_tree = build_comment_tree(comments)
        
        return JSONResponse(content={
            "code": 200,
            "data": {"comments": comment_tree},
            "msg": "success"
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )


@router.post("/comments")
async def create_comment(
    comment_data: CommentCreate,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new comment"""
    try:
        # Check if post exists
        post_result = await db.execute(select(Post).where(Post.id == comment_data.post_id))
        post = post_result.scalar_one_or_none()
        
        if not post:
            return JSONResponse(
                status_code=404,
                content={"code": 404, "data": {}, "msg": "post not found"}
            )
        
        # If parent_id is provided, check if parent comment exists
        if comment_data.parent_id:
            parent_result = await db.execute(
                select(Comment).where(
                    Comment.id == comment_data.parent_id,
                    Comment.post_id == comment_data.post_id
                )
            )
            parent = parent_result.scalar_one_or_none()
            
            if not parent:
                return JSONResponse(
                    status_code=404,
                    content={"code": 404, "data": {}, "msg": "parent comment not found"}
                )
        
        # Create comment
        comment = Comment(
            post_id=comment_data.post_id,
            parent_id=comment_data.parent_id,
            author_name=comment_data.author_name,
            author_email=comment_data.author_email,
            content=comment_data.content,
            user_id=current_user.id if current_user else None
        )
        
        db.add(comment)
        await db.commit()
        await db.refresh(comment)
        
        return JSONResponse(
            status_code=201,
            content={
                "code": 201,
                "data": {
                    "id": comment.id,
                    "post_id": comment.post_id,
                    "parent_id": comment.parent_id,
                    "author_name": comment.author_name,
                    "author_email": comment.author_email,
                    "content": comment.content,
                    "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M:%S") if comment.created_at else "",
                    "replies": []
                },
                "msg": "comment created"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )


@router.delete("/comments/{id}")
async def delete_comment(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Delete a comment (only for comment author or admin)"""
    try:
        if not current_user:
            return JSONResponse(
                status_code=401,
                content={"code": 401, "data": {}, "msg": "not authenticated"}
            )
        
        result = await db.execute(select(Comment).where(Comment.id == id))
        comment = result.scalar_one_or_none()
        
        if not comment:
            return JSONResponse(
                status_code=404,
                content={"code": 404, "data": {}, "msg": "comment not found"}
            )
        
        # Check if user is the comment author
        if comment.user_id != current_user.id:
            return JSONResponse(
                status_code=403,
                content={"code": 403, "data": {}, "msg": "not authorized"}
            )
        
        # Delete comment and all its replies
        # First get all child comments
        stmt = select(Comment).where(Comment.parent_id == id)
        children_result = await db.execute(stmt)
        children = children_result.scalars().all()
        
        # Delete children recursively (or set parent_id to None to keep them)
        for child in children:
            child.parent_id = None  # Keep child comments but detach from parent
        
        await db.delete(comment)
        await db.commit()
        
        return JSONResponse(content={
            "code": 200,
            "data": {},
            "msg": "comment deleted"
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "data": {}, "msg": str(e)}
        )
