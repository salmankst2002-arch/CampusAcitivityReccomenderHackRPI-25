# app/recommendation/features.py
from __future__ import annotations

from app.models import User, Club, Event
from typing import Tuple, Set
import numpy as np

from app.recommendation.vocab import TAG_VOCAB
from app.recommendation.utils import parse_tags

YEAR_CATEGORIES = ["freshman", "sophomore", "junior", "senior"]

DAY_ORDER = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def _encode_year(year: str) -> np.ndarray:
    """Encode user.year into a 5-dim one-hot vector."""
    vec = np.zeros(5, dtype=float)
    if not year:
        vec[-1] = 1.0  # "other"
        return vec

    y = year.strip().lower()
    if y in YEAR_CATEGORIES:
        idx = YEAR_CATEGORIES.index(y)
        vec[idx] = 1.0
    else:
        # everything else is mapped to "other"
        vec[-1] = 1.0

    return vec


def _encode_tags_as_multihot(tag_set: Set[str]) -> np.ndarray:
    """Encode a set of tags into a 10-dim multi-hot vector following TAG_VOCAB."""
    vec = np.zeros(len(TAG_VOCAB), dtype=float)
    for i, tag in enumerate(TAG_VOCAB):
        if tag in tag_set:
            vec[i] = 1.0
    return vec


def _encode_meeting_time(meeting_time: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Encode meeting_time into:
    - day_one_hot: 7-dim one-hot (Mon-Sun)
    - time_bucket: 3-dim one-hot (morning / afternoon / evening)
    """
    day_vec = np.zeros(len(DAY_ORDER), dtype=float)
    bucket_vec = np.zeros(3, dtype=float)

    if not meeting_time:
        return day_vec, bucket_vec

    parts = meeting_time.split()
    if len(parts) >= 2:
        # Parse day
        raw_day = parts[0].strip().lower()[:3]  # "Mon" -> "mon"
        if raw_day in DAY_ORDER:
            day_idx = DAY_ORDER.index(raw_day)
            day_vec[day_idx] = 1.0

        # Parse time
        time_part = parts[1]
        try:
            hour_str = time_part.split(":")[0]
            hour = int(hour_str)
            # Time bucket
            if 0 <= hour < 12:
                bucket_vec[0] = 1.0  # morning
            elif 12 <= hour < 17:
                bucket_vec[1] = 1.0  # afternoon
            elif 17 <= hour <= 23:
                bucket_vec[2] = 1.0  # evening
        except (ValueError, IndexError):
            # leave bucket_vec as zeros if parsing fails
            pass

    return day_vec, bucket_vec


def _compute_tag_interactions(user_tags: Set[str], club_tags: Set[str]) -> Tuple[float, float]:
    """Compute overlap count and Jaccard similarity between user_tags and club_tags."""
    overlap = user_tags & club_tags
    union = user_tags | club_tags

    overlap_count = float(len(overlap))
    if len(union) > 0:
        jaccard = float(len(overlap) / len(union))
    else:
        jaccard = 0.0

    return overlap_count, jaccard


def build_feature_vector(user, club) -> np.ndarray:
    """
    Build a 38-dimensional feature vector phi(x, y) for LinUCB.

    Layout:
      [ 0:  5)  user year one-hot (5)
      [ 5: 15)  user interests tags multi-hot (10)
      [15: 25)  club tags multi-hot (10)
      [25: 32)  meeting day one-hot (7)
      [32: 35)  meeting time bucket one-hot (3)
      [35]      tag overlap count (1)
      [36]      tag Jaccard similarity (1)
      [37]      bias term (1, always 1.0)
    """
    # --- User-side features ---
    year_vec = _encode_year(user.year)
    user_tags = parse_tags(getattr(user, "interests", ""))
    user_tag_vec = _encode_tags_as_multihot(user_tags)

    # --- Club-side features ---
    club_tags = parse_tags(getattr(club, "tags", ""))
    club_tag_vec = _encode_tags_as_multihot(club_tags)
    day_vec, bucket_vec = _encode_meeting_time(getattr(club, "meeting_time", ""))

    # --- Interaction features ---
    overlap_count, jaccard = _compute_tag_interactions(user_tags, club_tags)
    interaction_vec = np.array([overlap_count, jaccard], dtype=float)

    # --- Bias term ---
    bias_vec = np.array([1.0], dtype=float)

    # Concatenate everything into a single 38-dim vector
    phi = np.concatenate(
        [
            year_vec,        # 5
            user_tag_vec,    # 10
            club_tag_vec,    # 10
            day_vec,         # 7
            bucket_vec,      # 3
            interaction_vec, # 2
            bias_vec,        # 1
        ],
        axis=0,
    )

    # Sanity check (optional)
    # assert phi.shape == (38,)

    return phi

# Shared tag vocabulary used both for clubs and events.
TAG_VOCAB = [
    "academic_stem_tech",
    "business_career",
    "creative_arts",
    "sports",
    "gaming",
    "service",
    "activism_environment",
    "politics",
    "cultural",
    "faith",
]


def encode_tags_to_vector(tags_str: str) -> np.ndarray:
    """
    Convert a comma-separated tag string into a |TAG_VOCAB|-dimensional
    binary vector. Unknown tags are ignored.

    Example:
      tags_str = "academic_stem_tech,gaming"
      -> [1, 0, 0, 0, 1, 0, 0, 0, 0, 0]
    """
    vec = np.zeros(len(TAG_VOCAB), dtype=float)
    if not tags_str:
        return vec

    tags = [t.strip() for t in tags_str.split(",") if t.strip()]
    for i, tag in enumerate(TAG_VOCAB):
        if tag in tags:
            vec[i] = 1.0
    return vec


def encode_user_interests(user: User) -> np.ndarray:
    """
    Encode the user's `interests` (comma-separated TAG_VOCAB entries)
    into the same |TAG_VOCAB|-dimensional binary vector.
    """
    return encode_tags_to_vector(user.interests or "")


def build_club_feature_vector(user: User, club: Club) -> np.ndarray:
    """
    Build the feature vector used by LinUCB when ranking clubs.

    Here we use a simple concatenation:
      [user_interest_vector, club_tag_vector]

    Both are |TAG_VOCAB|-dimensional, so the final dimension is 2 * |TAG_VOCAB|.
    """
    user_vec = encode_user_interests(user)
    club_vec = encode_tags_to_vector(club.tags or "")

    return np.concatenate([user_vec, club_vec], axis=0)


def build_event_feature_vector(user: User, event: Event) -> np.ndarray:
    """
    Build the feature vector used by LinUCB when ranking events.

    Design choice:
      - We treat the event as inheriting its tags from the parent Club.
      - So we encode:
            [user_interest_vector, club_tag_vector, time_features]

        where:
          - user_interest_vector: |TAG_VOCAB|
          - club_tag_vector:     |TAG_VOCAB|
          - time_features:       e.g., a small one-hot or numeric encoding
                                 for weekday/weekend + time-of-day.

    This keeps the dimensionality small but still allows LinUCB to learn
    that a user who likes "academic_stem_tech" tends to prefer events
    from clubs with the same tags, especially on certain days/times.
    """

    # 1) User interest vector (same as for clubs)
    user_vec = encode_user_interests(user)

    # 2) Club tag vector: use the tags of the associated club.
    #    IMPORTANT: Event does not have a 'tags' column; tags live on Club.
    club = event.club
    if club is not None:
        club_tag_vec = encode_tags_to_vector(club.tags or "")
    else:
        # Safety fallback; should not usually happen if foreign keys are set properly.
        club_tag_vec = np.zeros(len(TAG_VOCAB), dtype=float)

    # 3) Time features (very simple example)
    #    - weekday vs weekend (2 dims, one-hot)
    #    - evening vs non-evening (2 dims, one-hot)
    #
    #    You can refine this later if you want finer time resolution.
    if event.start_time is not None:
        weekday = event.start_time.weekday()  # Monday=0, Sunday=6
        is_weekend = int(weekday >= 5)

        hour = event.start_time.hour
        # Example: treat 17:00-22:00 as "evening"
        is_evening = int(17 <= hour <= 22)
    else:
        # Unknown time -> encode as zeros
        is_weekend = 0
        is_evening = 0

    # One-hot style: [weekday_flag, weekend_flag, non_evening_flag, evening_flag]
    weekday_flag = 1 - is_weekend
    weekend_flag = is_weekend
    evening_flag = is_evening
    non_evening_flag = 1 - is_evening

    time_vec = np.array(
        [weekday_flag, weekend_flag, non_evening_flag, evening_flag],
        dtype=float,
    )

    # Final feature vector for events: concatenation of all blocks.
    feat = np.concatenate([user_vec, club_tag_vec, time_vec], axis=0)

    return feat
