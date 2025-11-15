import React, { useEffect, useRef, useState } from "react";
import { FiHeart, FiX, FiCalendar } from "react-icons/fi";
import type { Club } from "../types/club";

export interface CardProps {
  activity: Club;
  onSwipe: (id: number, vote: "like" | "dislike") => void;
}

// Retro Card Component
export const Card: React.FC<CardProps> = ({ activity, onSwipe }) => {
  const cardRef = useRef<HTMLDivElement | null>(null);
  const startX = useRef(0);
  const startY = useRef(0);
  const offsetX = useRef(0);
  const offsetY = useRef(0);

  const [isDragging, setIsDragging] = useState(false);
  const [style, setStyle] = useState({ transform: "", transition: "" });

  const SWIPE_THRESHOLD = 140;

  useEffect(() => {
    setStyle({ transform: "", transition: "" });
    offsetX.current = 0;
    offsetY.current = 0;
  }, [activity.id]);

  const applyTransform = (x: number, y: number, rot: number) => {
    setStyle({
      transform: `translate(${x}px, ${y}px) rotate(${rot}deg)`,
      transition: "",
    });
  };

  const handlePointerDown = (e: React.PointerEvent) => {
    try {
      (e.target as Element).setPointerCapture(e.pointerId);
    } catch {}
    startX.current = e.clientX;
    startY.current = e.clientY;
    setIsDragging(true);
    setStyle((s) => ({ transform: s.transform, transition: "" }));
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isDragging) return;
    const dx = e.clientX - startX.current;
    const dy = e.clientY - startY.current;
    offsetX.current = dx;
    offsetY.current = dy;
    const rot = Math.max(-20, Math.min(20, dx / 20));
    applyTransform(dx, dy, rot);
  };

  const finishSwipe = () => {
    const x = offsetX.current;
    if (x > SWIPE_THRESHOLD) {
      setStyle({
        transform: `translate(1000px, ${offsetY.current}px) rotate(30deg)`,
        transition: "transform 300ms ease-out",
      });
      setTimeout(() => onSwipe(activity.id, "like"), 300);
    } else if (x < -SWIPE_THRESHOLD) {
      setStyle({
        transform: `translate(-1000px, ${offsetY.current}px) rotate(-30deg)`,
        transition: "transform 300ms ease-out",
      });
      setTimeout(() => onSwipe(activity.id, "dislike"), 300);
    } else {
      setStyle({
        transform: "",
        transition: "transform 200ms cubic-bezier(.2,.8,.2,1)",
      });
    }
    setIsDragging(false);
  };

  const handlePointerUp = (e: React.PointerEvent) => {
    try {
      (e.target as Element).releasePointerCapture(e.pointerId);
    } catch {}
    finishSwipe();
  };

  const buttonSwipe = (v: "like" | "dislike") => {
    const dir = v === "like" ? 1000 : -1000;
    setStyle({
      transform: `translate(${dir}px, 0px) rotate(${
        v === "like" ? 30 : -30
      }deg)`,
      transition: "transform 300ms ease-out",
    });
    setTimeout(() => onSwipe(activity.id, v), 300);
  };

  return (
    <div
      ref={cardRef}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
      style={style}
      className="w-80 md:w-96 bg-gradient-to-br from-yellow-50 via-pink-50 to-purple-50 rounded-2xl shadow-2xl p-4 border-4 border-zinc-900/10 retro-glow select-none absolute left-1/2 -translate-x-1/2"
    >
      <div className="flex justify-between items-start mb-3">
        <div className="text-xs opacity-80 flex items-center gap-2">
          <span className="px-2 py-1 rounded bg-zinc-900 text-white text-[10px]">
            retro
          </span>
          <span className="font-mono text-[11px]">
            {activity.tags ?? "general"}
          </span>
        </div>
        <div className="text-right">
          <div className="text-sm font-semibold">{activity.name}</div>
          <div className="text-[11px] opacity-70">
            {activity.location ?? "TBD"}
          </div>
        </div>
      </div>

      <div className="h-44 md:h-48 bg-zinc-900/5 rounded-lg mb-3 overflow-hidden flex items-center justify-center">
        <div className="text-[12px] opacity-70 text-center px-3">
          {activity.description ?? "No description."}
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => buttonSwipe("dislike")}
            className="btn btn-ghost btn-square btn-sm"
          >
            <FiX size={18} />
          </button>
          <button
            onClick={() => buttonSwipe("like")}
            className="btn btn-ghost btn-square btn-sm"
          >
            <FiHeart size={18} />
          </button>
        </div>
        <div className="text-xs opacity-80 flex items-center gap-2">
          <FiCalendar />
          <span className="font-mono text-[12px]">
            {activity.meeting_time ?? "TBD"}
          </span>
        </div>
      </div>
    </div>
  );
};
