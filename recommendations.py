# app/api/recommendations.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from sqlmodel import Session, select
from ..models.posts import UserFavorite # 确保 UserFavorite 模型也被导入
from ..database import get_session
from ..models.posts import PostRead  # 用于响应模型
from ..models.users import User
from ..services.auth_service import get_current_active_user  # 用于获取当前用户
from ..services.recommendation_service import (
    get_most_popular_posts,
    get_item_based_collaborative_filtering_recommendations,
    get_random_posts
)

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/popular-posts", response_model=List[PostRead], summary="获取热门帖子")
async def read_popular_posts(
        limit: int = Query(5, ge=1, le=20),  # 查询参数，默认5条，最小1，最大20
        session: Session = Depends(get_session)
):
    """
    获取被收藏次数最多的热门帖子。
    """
    popular_posts = get_most_popular_posts(session=session, limit=limit)
    if not popular_posts:
        # 如果没有热门帖子，可以返回空列表或特定消息
        # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No popular posts found")
        return []
    return popular_posts


@router.get("/for-you", response_model=List[PostRead], summary="为当前登录用户推荐帖子 (协同过滤)")
async def get_recommendations_for_current_user(
        limit: int = Query(5, ge=1, le=20),
        current_user: User = Depends(get_current_active_user),  # 需要用户登录
        session: Session = Depends(get_session)
):
    """
    基于用户收藏行为的协同过滤推荐。
    如果无法生成协同过滤推荐（例如新用户无收藏），可以考虑返回热门帖子或随机帖子。
    """
    recommendations = get_item_based_collaborative_filtering_recommendations(
        session=session, user_id=current_user.id, limit=limit
    )

    # 如果协同过滤结果不足或为空，可以用热门或随机帖子补充
    if not recommendations or len(recommendations) < limit:
        # print(f"CF recommendations count: {len(recommendations)}. Trying to supplement...") # For debugging
        needed_more = limit - len(recommendations)

        # 获取热门帖子作为补充，并排除已在推荐列表中的
        supplement_candidates = get_most_popular_posts(session=session, limit=limit + 5)  # 多取一些以备过滤

        # 过滤掉已在协同过滤推荐中的 和 用户已收藏的 (协同过滤算法本身应该处理了已收藏)
        existing_rec_ids = {rec.id for rec in recommendations}
        user_favorited_post_ids_stmt = select(UserFavorite.post_id).where(UserFavorite.user_id == current_user.id)
        user_favorited_post_ids = {pid for pid in session.exec(user_favorited_post_ids_stmt).all()}

        supplement_posts = []
        for post in supplement_candidates:
            if len(supplement_posts) >= needed_more:
                break
            if post.id not in existing_rec_ids and post.id not in user_favorited_post_ids:
                supplement_posts.append(post)

        recommendations.extend(supplement_posts)
        # print(f"Supplemented recommendations count: {len(recommendations)}") # For debugging

    if not recommendations:
        # 如果还是没有，最后尝试随机帖子
        # print("No recommendations from CF or Popular. Trying random.") # For debugging
        recommendations = get_random_posts(session=session, current_user_id=current_user.id, limit=limit)

    if not recommendations:
        return []  # 或者抛出 404

    return recommendations[:limit]  # 确保不超过limit


@router.get("/random-posts", response_model=List[PostRead], summary="获取随机帖子")
async def read_random_posts(
        limit: int = Query(5, ge=1, le=20),
        session: Session = Depends(get_session)
):
    """
    获取一些随机的帖子。
    """
    random_p = get_random_posts(session=session, limit=limit)
    if not random_p:
        return []
    return random_p