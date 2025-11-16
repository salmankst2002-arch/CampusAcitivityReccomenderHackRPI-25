import type { Club } from "../types/backend";
import { Card } from "./Card";

export const SwipeDeck: React.FC<{
  clubs: Club[];
  onSwipe: (id: number, v: "like" | "dislike") => void;
}> = ({ clubs: activities, onSwipe }) => {
  const top = activities.slice(0, 5).reverse();

  return (
    <div className="relative h-[540px] w-full max-w-xl mx-auto mt-6">
      {top.map((a, i) => (
        <div
          key={a.club_id}
          style={{ zIndex: 10 + i }}
          className="absolute inset-0 flex items-center justify-center"
        >
          <Card activity={a} onSwipe={onSwipe} />
        </div>
      )) ?? <div key={-1}>No more clubs</div>}
    </div>
  );
};
