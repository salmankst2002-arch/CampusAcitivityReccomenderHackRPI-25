# app/visibility.py

from .models import Event, Club, User  # 型ヒント用（実装スタイルに合わせて）

def get_email_domain(user_email: str) -> str | None:
    if not user_email or "@" not in user_email:
        return None
    return user_email.split("@", 1)[1].lower()

def user_is_member_of_club(user: User, club_id: int) -> bool:
    # まだ ClubMember テーブルが無ければ、仮実装で False にしておいてOK
    # 将来、ClubMember モデルを作ったらここでクエリする
    return False

def user_can_manage_club(user: User | None, club_id: int) -> bool:
    if not user:
        return False
    # まずは「クラブオーナーだけ管理可能」という単純版でもOK
    club = Club.query.get(club_id)
    if not club:
        return False
    # 例: Club に owner_user_id フィールドを追加している場合
    return getattr(club, "owner_user_id", None) == user.id

def event_is_visible_to_user(event: Event, user: User | None) -> bool:
    mode = event.visibility_mode or "public"
    domain = get_email_domain(user.email) if user else None

    if mode == "public":
        return True

    if mode == "members_only":
        if not user:
            return False
        return user_is_member_of_club(user, event.club_id)

    if mode in {"domain_allowlist", "domain_blocklist"}:
        if not user or not domain:
            return False

        if event.visible_email_domains:
            allowed = {
                d.strip().lower()
                for d in event.visible_email_domains.split(",")
                if d.strip()
            }
        else:
            allowed = set()

        if mode == "domain_allowlist":
            return domain in allowed

        if mode == "domain_blocklist":
            return domain not in allowed

    return False
