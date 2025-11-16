import { useEffect, useState } from "react";
import axios from "axios";
import type { Club, SwipeRecord } from "../types/backend";
import { SwipeDeck } from "../components/SwipeDeck";
import { BACKEND_URL } from "../config";

export default function Discover() {
  const [clubs, setClubs] = useState<Club[]>([]);
  const [loading, setLoading] = useState(true);
  const USER_ID = 1;

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await axios.get(`${BACKEND_URL}/api/recommend`, {
          params: { user_id: USER_ID },
        });
        setClubs(await res.data);
      } catch (error) {
        // todo: replace with error logging
        setClubs([
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
        console.error("Failed to load clubs:", error);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleSwipe = async (club_id: number, vote: "like" | "dislike") => {
    setClubs((prev) => prev.filter((c) => c.id !== club_id));

    const record: SwipeRecord = {
      id: Date.now(),
      user_id: USER_ID,
      club_id,
      liked: vote === "like",
      created_at: new Date(),
    };

    // Send swipe record to backend
    try {
      await axios.post(`${BACKEND_URL}/api/swipe`, record);
    } catch (error) {
      console.error("Failed to send swipe:", error);
    }
  };

  return (
    <div className="h-full bg-gradient-to-tr from-[#f7f0e6] to-[#fff1f8] flex flex-col">
      {title}
      <main className="flex-1 w-full px-4 mt-6 overflow-y-auto">
        {loading ? (
          <div className="mx-auto">Loading...</div>
        ) : (
          <SwipeDeck activities={clubs} onSwipe={handleSwipe} />
        )}
      </main>
    </div>
  );
}

const title = (
  <header className="p-4 max-w-4xl mx-auto">
    <h1>RetroCampus</h1>
    {/* todo: make aliased font */}
  </header>
);
