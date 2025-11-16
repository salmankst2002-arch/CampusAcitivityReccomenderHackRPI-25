// front_end/src/pages/Discover.tsx
import { useEffect, useState } from "react";
import axios from "axios";
import type { Club } from "../types/backend";
import { SwipeDeck } from "../components/SwipeDeck";
import { BACKEND_URL } from "../config";
import { useAuth } from "../auth/AuthContext";

export default function Discover() {
  const { userId } = useAuth();
  const [clubs, setClubs] = useState<Club[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!userId) return; // should not happen because of RequireAuth

    const load = async () => {
      setLoading(true);
      try {
        const res = await axios.get(`${BACKEND_URL}/api/recommend`, {
          params: { user_id: userId },
        });
        console.log("Recommended clubs:", res.data);
        setClubs(res.data);
      } catch (error) {
        console.error("Failed to load clubs:", error);
        setClubs([]);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [userId]);

  const handleSwipe = async (club_id: number, vote: "like" | "dislike") => {
    setClubs((prev) => prev.filter((c) => c.club_id !== club_id));

    if (!userId) return;

    try {
      const payload = {
        user_id: userId,
        club_id,
        liked: vote === "like",
      };
      console.log("Sending swipe payload:", payload);
      const response = await axios.post(`${BACKEND_URL}/api/swipe`, payload, {
        headers: {
          "Content-Type": "application/json",
        },
      });
      console.log("Swipe response:", response.data);
    } catch (error) {
      console.error("Failed to send swipe:", error);
      if (axios.isAxiosError(error)) {
        console.error("Response data:", error.response?.data);
        console.error("Response status:", error.response?.status);
      }
    }
  };

  return (
    <div className="h-full bg-gradient-to-tr from-[#f7f0e6] to-[#fff1f8] flex flex-col">
      {title}
      <main className="flex-1 w-full px-4 mt-6 overflow-y-auto">
        {loading ? (
          <div className="mx-auto items-center">Loading...</div>
        ) : (
          <SwipeDeck clubs={clubs} onSwipe={handleSwipe} />
        )}
      </main>
    </div>
  );
}

const title = (
  <header className="p-4 max-w-4xl mx-auto">
    <h1>RetroCampus</h1>
    {/* TODO: add logo / subtitle */}
  </header>
);
