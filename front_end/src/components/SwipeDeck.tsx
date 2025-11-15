import type { Club } from "../types/club";
import { Card } from "./Card";

export const SwipeDeck: React.FC<{
  activities: Club[];
  onSwipe: (id: number, v: "like" | "dislike") => void;
}> = ({ activities, onSwipe }) => {
  const top = activities.slice(0, 5).reverse();

  return (
    <div className="relative h-[540px] w-full max-w-xl mx-auto mt-6">
      {top.map((a, i) => (
        <div
          key={a.id}
          style={{ zIndex: 10 + i }}
          className="absolute inset-0 flex items-center justify-center"
        >
          <Card activity={a} onSwipe={onSwipe} />
        </div>
      ))}
    </div>
  );
};
