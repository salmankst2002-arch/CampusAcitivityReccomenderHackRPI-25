# app/recommendation/linucb.py
from __future__ import annotations

from typing import List, Tuple, Optional
import os
import numpy as np

from app.models import User, Club, Event
from app.recommendation.features import (
    build_feature_vector,        # club feature: (user, club) -> R^38 (existing)
    build_event_feature_vector,  # event feature: (user, event) -> R^24
)

# -------------------------------------------------------------------
# State file paths (separate for clubs and events)
# -------------------------------------------------------------------
BASE_DIR = os.path.dirname(__file__)
INSTANCE_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "instance"))

STATE_PATH_CLUBS = os.path.join(INSTANCE_DIR, "linucb_clubs_state.npz")
STATE_PATH_EVENTS = os.path.join(INSTANCE_DIR, "linucb_events_state.npz")


class LinUCB:
    """
    Simple LinUCB agent.

    We maintain:
        A in R^{d x d}, b in R^d
    and use the standard update:
        A <- A + phi phi^T
        b <- b + r phi

    and scoring rule:
        score(phi) = phi^T theta_hat + alpha * sqrt(phi^T A^{-1} phi),
        where theta_hat = A^{-1} b.
    """

    def __init__(self, dim: int, alpha: float = 1.0, lambda_reg: float = 1.0) -> None:
        self.dim = dim
        self.alpha = alpha
        self.lambda_reg = lambda_reg

        # A is the design matrix (d x d), initialized as lambda * I.
        self.A = lambda_reg * np.eye(dim, dtype=float)
        # b is the response vector (d,)
        self.b = np.zeros(dim, dtype=float)

    # ------------------------------------------------------------------
    # Core linear algebra
    # ------------------------------------------------------------------
    def reset(self) -> None:
        """Reset A and b to the initial state."""
        self.A = self.lambda_reg * np.eye(self.dim, dtype=float)
        self.b = np.zeros(self.dim, dtype=float)

    def _theta_hat(self) -> np.ndarray:
        """Compute theta_hat = A^{-1} b using a linear solver."""
        return np.linalg.solve(self.A, self.b)

    def _ucb_score(self, phi: np.ndarray) -> float:
        """
        Compute the LinUCB score for a single feature vector phi.

        score = phi^T theta_hat + alpha * sqrt(phi^T A^{-1} phi)
        """
        phi = phi.astype(float)
        if phi.shape[0] != self.dim:
            raise ValueError(
                f"Feature dimension mismatch: expected {self.dim}, got {phi.shape[0]}"
            )

        theta_hat = self._theta_hat()

        # Predicted mean reward
        mean = float(phi @ theta_hat)

        # Compute A^{-1} phi using a linear solver (avoid explicit inverse)
        A_inv_phi = np.linalg.solve(self.A, phi)
        var = float(np.sqrt(phi @ A_inv_phi))

        return mean + self.alpha * var

    def score(self, phi: np.ndarray) -> float:
        """
        Public wrapper for UCB score, used by external ranking helpers.
        """
        return self._ucb_score(phi)

    def update_from_features(self, phi: np.ndarray, reward: float) -> None:
        """
        Generic update that takes a feature vector directly.

        Args:
            phi: feature vector in R^d (must match self.dim)
            reward: observed reward (e.g., 1.0 for like, 0.0 for dislike)
        """
        phi = phi.astype(float)
        if phi.shape[0] != self.dim:
            raise ValueError(
                f"Feature dimension mismatch in update: expected {self.dim}, got {phi.shape[0]}"
            )

        self.A += np.outer(phi, phi)
        self.b += reward * phi

    # ------------------------------------------------------------------
    # Convenience helpers for club-based updates
    # ------------------------------------------------------------------
    def update_from_club(self, user: User, club: Club, reward: float) -> None:
        """
        Convenience wrapper for the club setting:
            (user, club) -> feature vector -> update.
        """
        phi = build_feature_vector(user, club)
        self.update_from_features(phi, reward)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------
    def to_state(self) -> dict:
        """
        Serialize the internal parameters of LinUCB into a plain dict.
        """
        return {
            "A": self.A,                  # shape: (d, d)
            "b": self.b,                  # shape: (d,)
            "alpha": float(self.alpha),
            "dim": int(self.dim),
            "lambda_reg": float(self.lambda_reg),
        }

    def save_state(self, path: str) -> None:
        """
        Save the current LinUCB parameters to a .npz file.
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        state = self.to_state()
        np.savez(path, **state)
        print(f"[LinUCB] State saved to {path}")

    @classmethod
    def from_state(cls, path: str) -> "LinUCB | None":
        """
        Load LinUCB parameters from a .npz file and construct an instance.

        Returns None if the state file does not exist.
        """
        if not os.path.exists(path):
            print(f"[LinUCB] No state file found at {path}, using fresh LinUCB.")
            return None

        data = np.load(path, allow_pickle=True)
        dim = int(data["dim"])
        alpha = float(data["alpha"])
        lambda_reg = float(data.get("lambda_reg", 1.0))

        obj = cls(dim=dim, alpha=alpha, lambda_reg=lambda_reg)
        obj.A = data["A"]
        obj.b = data["b"]

        print(f"[LinUCB] State loaded from {path} (dim={dim}, alpha={alpha})")
        return obj


# -------------------------------------------------------------------
# Global agents: one for clubs, one for events
# -------------------------------------------------------------------

# Clubs: use the existing 38-dim feature vector (build_feature_vector).
_loaded_clubs = LinUCB.from_state(STATE_PATH_CLUBS)
if _loaded_clubs is not None:
    GLOBAL_LINUCB_CLUBS = _loaded_clubs
else:
    # NOTE: dim=38 is consistent with your current club feature design.
    GLOBAL_LINUCB_CLUBS = LinUCB(dim=38, alpha=1.0, lambda_reg=1.0)
    print("[LinUCB] Created fresh GLOBAL_LINUCB_CLUBS instance (dim=38)")

# Events: use the 24-dim event feature vector (user interests 10 + club tags 10 + time 4).
_loaded_events = LinUCB.from_state(STATE_PATH_EVENTS)
if _loaded_events is not None:
    GLOBAL_LINUCB_EVENTS = _loaded_events
else:
    GLOBAL_LINUCB_EVENTS = LinUCB(dim=24, alpha=1.0, lambda_reg=1.0)
    print("[LinUCB] Created fresh GLOBAL_LINUCB_EVENTS instance (dim=24)")


# -------------------------------------------------------------------
# Ranking helpers
# -------------------------------------------------------------------

def rank_clubs_with_linucb(
    user: User,
    clubs: List[Club],
    top_k: int = 5,
) -> List[Tuple[Club, float]]:
    """
    Rank candidate clubs for the given user using the club-level LinUCB agent.

    Returns:
        List of (club, score) pairs sorted by score in descending order.
    """
    scored: List[Tuple[Club, float]] = []
    if not clubs:
        return scored

    for club in clubs:
        phi = build_feature_vector(user, club)
        score = GLOBAL_LINUCB_CLUBS.score(phi)
        scored.append((club, float(score)))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


def rank_events_with_linucb(
    user: User,
    events: List[Event],
    top_k: int = 5,
) -> List[Tuple[Event, float]]:
    """
    Rank candidate events for the given user using the event-level LinUCB agent.

    Returns:
        List of (event, score) pairs sorted by score in descending order.
    """
    scored: List[Tuple[Event, float]] = []
    if not events:
        return scored

    for ev in events:
        x = build_event_feature_vector(user, ev)
        score = GLOBAL_LINUCB_EVENTS.score(x)
        scored.append((ev, float(score)))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


# -------------------------------------------------------------------
# Update helper for club swipes
# -------------------------------------------------------------------

def update_global_linucb_from_swipe(user: User, club: Club, liked: bool) -> None:
    """
    Update the club-level global LinUCB agent using a single swipe event.

    This function:
      1. Builds the club feature vector for (user, club).
      2. Uses a simple reward definition: 1.0 if liked, 0.0 if not.
      3. Updates GLOBAL_LINUCB_CLUBS.
      4. Saves the updated state to disk.
    """
    reward = 1.0 if liked else 0.0

    GLOBAL_LINUCB_CLUBS.update_from_club(user, club, reward)

    print(
        f"[LinUCB] Updated clubs agent from swipe: "
        f"user_id={user.id}, club_id={club.id}, liked={liked}"
    )
    GLOBAL_LINUCB_CLUBS.save_state(STATE_PATH_CLUBS)
