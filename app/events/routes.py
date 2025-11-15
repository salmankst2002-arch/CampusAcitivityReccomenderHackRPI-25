# app/events/routes.py

from datetime import datetime
from typing import List, Optional

from flask import request, jsonify
from flask_login import current_user, login_required

from . import events_bp
from app.extensions import db
from app.models import Event
from app.visibility import (
    event_is_visible_to_user,
    user_can_manage_club,
)


# ===== ヘルパー関数 =====

def parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    """
    ISO8601 形式の文字列を datetime に変換する簡単なヘルパー。
    例: "2025-09-15T18:00:00"
    タイムゾーンなどが必要なら、ここを拡張してください。
    """
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        # フロントから変な形式が来たときは None にして上位で 400 を返すなど
        return None


def event_to_dict(event: Event) -> dict:
    """
    管理用: visibility 情報も含めてフルの Event を JSON にする。
    manage API / デバッグ用。
    """
    return {
        "id": event.id,
        "club_id": event.club_id,
        "title": event.title,
        "description": event.description,
        "start_time": event.start_time.isoformat() if event.start_time else None,
        "end_time": event.end_time.isoformat() if event.end_time else None,
        "location": event.location,
        "is_online": event.is_online,
        "join_link": event.join_link,
        "capacity": event.capacity,
        "visibility_mode": event.visibility_mode,
        "visible_email_domains": (
            [d.strip() for d in event.visible_email_domains.split(",")]
            if event.visible_email_domains
            else []
        ),
        "created_at": event.created_at.isoformat() if event.created_at else None,
        "updated_at": event.updated_at.isoformat() if event.updated_at else None,
    }


def event_to_public_dict(event: Event) -> dict:
    """
    一般ユーザー向け: visibility の内部情報は含めない。
    """
    return {
        "id": event.id,
        "club_id": event.club_id,
        "title": event.title,
        "description": event.description,
        "start_time": event.start_time.isoformat() if event.start_time else None,
        "end_time": event.end_time.isoformat() if event.end_time else None,
        "location": event.location,
        "is_online": event.is_online,
        "join_link": event.join_link,
        "capacity": event.capacity,
    }


def _normalize_domains(domains: Optional[List[str]]) -> Optional[str]:
    """
    ["albany.edu", "kgu.ac.jp"] → "albany.edu,kgu.ac.jp"
    のように正規化して TEXT として保存する。
    """
    if domains is None:
        return None
    if not isinstance(domains, list):
        raise TypeError("visible_email_domains must be a list of strings")
    cleaned = {d.strip().lower() for d in domains if isinstance(d, str) and d.strip()}
    if not cleaned:
        return None
    # ソートしておくと diff がきれいになる
    return ",".join(sorted(cleaned))


# ===== ルート定義 =====


@events_bp.route("/clubs/<int:club_id>/events", methods=["POST"])
@login_required
def create_event(club_id: int):
    """
    新規イベント作成:
    POST /api/clubs/<club_id>/events

    Body(JSON):
    {
      "title": "...",               # required
      "description": "...",
      "start_time": "2025-09-15T18:00:00",  # required
      "end_time": "2025-09-15T20:00:00",
      "location": "Campus Center 305",
      "is_online": false,
      "join_link": null,
      "capacity": 40,
      "visibility_mode": "public | members_only | domain_allowlist | domain_blocklist",
      "visible_email_domains": ["albany.edu", "kgu.ac.jp"]
    }
    """
    user = current_user
    data = request.get_json() or {}

    # 権限チェック
    if not user_can_manage_club(user, club_id):
        return jsonify({"error": "Forbidden"}), 403

    title = data.get("title")
    start_time_raw = data.get("start_time")
    if not title or not start_time_raw:
        return jsonify({"error": "title and start_time are required"}), 400

    start_time = parse_iso_datetime(start_time_raw)
    if start_time is None:
        return jsonify({"error": "invalid start_time format"}), 400

    end_time_raw = data.get("end_time")
    end_time = parse_iso_datetime(end_time_raw) if end_time_raw else None
    if end_time_raw and end_time is None:
        return jsonify({"error": "invalid end_time format"}), 400

    visibility_mode = data.get("visibility_mode", "public")
    if visibility_mode not in {
        "public",
        "members_only",
        "domain_allowlist",
        "domain_blocklist",
    }:
        return jsonify({"error": "invalid visibility_mode"}), 400

    try:
        normalized_domains = _normalize_domains(
            data.get("visible_email_domains")
        )
    except TypeError as e:
        return jsonify({"error": str(e)}), 400

    event = Event(
        club_id=club_id,
        title=title,
        description=data.get("description"),
        start_time=start_time,
        end_time=end_time,
        location=data.get("location"),
        is_online=bool(data.get("is_online", False)),
        join_link=data.get("join_link"),
        capacity=data.get("capacity"),
        visibility_mode=visibility_mode,
        visible_email_domains=normalized_domains,
    )

    db.session.add(event)
    db.session.commit()

    return jsonify(event_to_dict(event)), 201


@events_bp.route("/events/<int:event_id>", methods=["PUT"])
@login_required
def update_event(event_id: int):
    """
    イベント更新:
    PUT /api/events/<event_id>

    Body は create_event と同様だが、部分更新として扱う。
    （フィールドが存在するものだけ上書き）
    """
    user = current_user
    data = request.get_json() or {}

    event = Event.query.get_or_404(event_id)

    # 権限チェック
    if not user_can_manage_club(user, event.club_id):
        return jsonify({"error": "Forbidden"}), 403

    # タイトル
    if "title" in data:
        if not data["title"]:
            return jsonify({"error": "title cannot be empty"}), 400
        event.title = data["title"]

    # 説明
    if "description" in data:
        event.description = data.get("description")

    # start_time
    if "start_time" in data:
        start_time_raw = data.get("start_time")
        if start_time_raw is None:
            return jsonify({"error": "start_time cannot be null"}), 400
        start_time = parse_iso_datetime(start_time_raw)
        if start_time is None:
            return jsonify({"error": "invalid start_time format"}), 400
        event.start_time = start_time

    # end_time
    if "end_time" in data:
        end_time_raw = data.get("end_time")
        if end_time_raw is None:
            event.end_time = None
        else:
            end_time = parse_iso_datetime(end_time_raw)
            if end_time is None:
                return jsonify({"error": "invalid end_time format"}), 400
            event.end_time = end_time

    # location
    if "location" in data:
        event.location = data.get("location")

    # is_online
    if "is_online" in data:
        event.is_online = bool(data.get("is_online"))

    # join_link
    if "join_link" in data:
        event.join_link = data.get("join_link")

    # capacity
    if "capacity" in data:
        event.capacity = data.get("capacity")

    # visibility_mode
    if "visibility_mode" in data:
        visibility_mode = data.get("visibility_mode")
        if visibility_mode not in {
            "public",
            "members_only",
            "domain_allowlist",
            "domain_blocklist",
        }:
            return jsonify({"error": "invalid visibility_mode"}), 400
        event.visibility_mode = visibility_mode

    # visible_email_domains
    if "visible_email_domains" in data:
        try:
            normalized_domains = _normalize_domains(
                data.get("visible_email_domains")
            )
        except TypeError as e:
            return jsonify({"error": str(e)}), 400
        event.visible_email_domains = normalized_domains

    db.session.commit()

    return jsonify(event_to_dict(event)), 200


@events_bp.route("/events/<int:event_id>", methods=["DELETE"])
@login_required
def delete_event(event_id: int):
    """
    イベント削除:
    DELETE /api/events/<event_id>
    """
    user = current_user
    event = Event.query.get_or_404(event_id)

    if not user_can_manage_club(user, event.club_id):
        return jsonify({"error": "Forbidden"}), 403

    db.session.delete(event)
    db.session.commit()

    return "", 204


@events_bp.route("/clubs/<int:club_id>/events", methods=["GET"])
def list_club_events(club_id: int):
    """
    一般ユーザー向けのクラブイベント一覧:
    GET /api/clubs/<club_id>/events

    クエリパラメータ:
      ?upcoming=true  で今後のイベントのみ
    """
    # ログインしていれば current_user、していなければ None として扱う
    user = current_user if getattr(current_user, "is_authenticated", False) else None

    q = Event.query.filter_by(club_id=club_id)

    if request.args.get("upcoming") == "true":
        q = q.filter(Event.start_time >= datetime.utcnow())

    events = q.order_by(Event.start_time.asc()).all()

    visible_events = [
        e
        for e in events
        if event_is_visible_to_user(e, user)
        or user_can_manage_club(user, club_id)
    ]

    return jsonify([event_to_public_dict(e) for e in visible_events])


@events_bp.route("/clubs/<int:club_id>/events/manage", methods=["GET"])
def manage_club_events(club_id: int):
    # NOTE: For now we skip authentication/authorization in development.
    events = (
        Event.query.filter_by(club_id=club_id)
        .order_by(Event.start_time.asc())
        .all()
    )
    return jsonify([event_to_dict(e) for e in events])
