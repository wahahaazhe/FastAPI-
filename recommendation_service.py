# app/services/recommendation_service.py
from typing import List, Optional  # <--- 确保 Optional 在这里被导入
from sqlmodel import Session, select, func  # func 用于 SQL 函数如 COUNT

from ..models.posts import Post, UserFavorite
from ..models.users import User  # 确保 User 也被导入了，如果 get_random_posts 的 current_user_id 类型提示需要


# ... (get_most_popular_posts 函数代码) ...
# ... (get_item_based_collaborative_filtering_recommendations 函数代码) ...

def get_most_popular_posts(session: Session, limit: int = 5) -> List[Post]:
    """
    获取最受欢迎（被收藏次数最多）的帖子列表。
    """
    statement = (
        select(Post, func.count(UserFavorite.post_id).label("favorites_count"))
        .join(UserFavorite, Post.id == UserFavorite.post_id, isouter=True)
        .group_by(Post.id)
        .order_by(func.count(UserFavorite.post_id).desc())
        .limit(limit)
    )
    results = session.exec(statement).all()
    popular_posts = [post for post, count in results if post is not None]
    return popular_posts


def get_item_based_collaborative_filtering_recommendations(
        session: Session, user_id: int, limit: int = 5
) -> List[Post]:
    """
    基于物品的协同过滤推荐 (简化版)。
    """
    user_favorites_statement = select(UserFavorite.post_id).where(UserFavorite.user_id == user_id)
    user_favorited_post_ids_list = session.exec(user_favorites_statement).all()  # 这是一个 post_id 的列表
    if not user_favorited_post_ids_list:
        return []

    candidate_posts_scores = {}

    for fav_post_id in user_favorited_post_ids_list:
        other_users_who_favorited_this_post_stmt = (
            select(UserFavorite.user_id)
            .where(UserFavorite.post_id == fav_post_id)
            .where(UserFavorite.user_id != user_id)
        )
        other_user_ids = session.exec(other_users_who_favorited_this_post_stmt).all()

        if not other_user_ids:
            continue

        for other_user_id in other_user_ids:
            other_user_favorites_stmt = (
                select(UserFavorite.post_id)
                .where(UserFavorite.user_id == other_user_id)
                .where(UserFavorite.post_id.notin_(user_favorited_post_ids_list))  # 确保这里是列表
            )
            recommended_for_other_user_post_ids = session.exec(other_user_favorites_stmt).all()

            for rec_post_id in recommended_for_other_user_post_ids:
                candidate_posts_scores[rec_post_id] = candidate_posts_scores.get(rec_post_id, 0) + 1

    if not candidate_posts_scores:
        return []

    sorted_candidate_post_ids = sorted(
        candidate_posts_scores.keys(),
        key=lambda post_id: candidate_posts_scores[post_id],
        reverse=True
    )
    top_n_post_ids = sorted_candidate_post_ids[:limit]

    if not top_n_post_ids:
        return []

    recommended_posts_stmt = select(Post).where(Post.id.in_(top_n_post_ids))
    posts_dict = {post.id: post for post in session.exec(recommended_posts_stmt).all()}
    final_recommendations = [posts_dict[pid] for pid in top_n_post_ids if pid in posts_dict]

    return final_recommendations


# 你定义的 get_random_posts 函数
def get_random_posts(session: Session, current_user_id: Optional[int] = None, limit: int = 5) -> List[Post]:
    """
    获取随机帖子，可选地排除当前用户已收藏的。
    注意：ORDER BY RAND() 在大型表上性能不佳，仅用于示例。
    """
    all_post_ids_stmt = select(Post.id)
    all_post_ids = session.exec(all_post_ids_stmt).all()

    if not all_post_ids:
        return []

    import random  # 确保 random 被导入
    sample_size = min(limit, len(all_post_ids))

    # 如果 all_post_ids 为空列表，random.sample 会报错，上面已处理
    if sample_size == 0:
        return []

    random_post_ids = random.sample(all_post_ids, sample_size)

    if not random_post_ids:  # 理论上如果 sample_size > 0，这里不会是空的
        return []

    random_posts_stmt = select(Post).where(Post.id.in_(random_post_ids))
    return session.exec(random_posts_stmt).all()