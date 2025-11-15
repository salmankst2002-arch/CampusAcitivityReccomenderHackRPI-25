import { useEffect, useState } from "react";
import type { Club, SwipeRecord } from "../types/club";
import { SwipeDeck } from "../components/SwipeDeck";

export default function Discover() {
  const [activities, setActivities] = useState<Club[]>([]);
  const [swipes, setSwipes] = useState<SwipeRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const USER_ID = 1;

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await fetch("/api/clubs");
        const raw = await res.json();
        setActivities(Array.isArray(raw) ? raw : []);
      } catch {
        setActivities([
          {
            id: 1,
            name: "Chess Club",
            description: "Casual games",
            meeting_time: "Thu 6pm",
            location: "Union 204",
          },
          {
            id: 2,
            name: "Robotics",
            description: "Beginner workshop",
            meeting_time: "Mon 4pm",
            location: "Lab 7",
          },
        ]);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleSwipe = (club_id: number, vote: "like" | "dislike") => {
    setActivities((prev) => prev.filter((c) => c.id !== club_id));

    const record: SwipeRecord = {
      id: Date.now(),
      user_id: USER_ID,
      club_id,
      liked: vote === "like",
      created_at: new Date(),
    };

    setSwipes((s) => [...s, record]);
  };

  return (
    <div className="min-h-screen bg-gradient-to-tr from-[#f7f0e6] to-[#fff1f8] pb-16">
      <header className="p-4 max-w-4xl mx-auto">RetroCampus</header>
      <main className="max-w-4xl mx-auto px-4 mt-6">
        {loading ? (
          <div>Loading...</div>
        ) : (
          <SwipeDeck activities={activities} onSwipe={handleSwipe} />
        )}
      </main>
    </div>
  );
}
