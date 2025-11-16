import { useEffect, useState } from "react";
import type { Club, Event } from "../types/backend";
import axios from "axios";
import { BACKEND_URL } from "../config";

export default function Matches() {
  // @ts-ignore
  // prettier-ignore
  const [clubEvents, setClubEvents] = useState<{club_id: number; events: Event[];}>({});

  useEffect(() => {
    // Fetch events for recommended clubs
    const fetchEvents = async () => {
      const recommendedClubs: Club[] = (
        await axios.get(`${BACKEND_URL}/api/recommend`, {
          params: { user_id: 1 },
        })
      ).data;

      for (const club of recommendedClubs) {
        const events: Event[] = (
          await axios.get(`${BACKEND_URL}/api/clubs/${club.club_id}/events`)
        ).data;
        setClubEvents({ ...clubEvents, [club.club_id]: events });
      }
    };
    fetchEvents();
  }, []);

  return (
    <>
      <h1 className="text-2xl font-bold">Your Matches</h1>
      <h2>Events</h2>
      {/* E1, E2, ... */}
    </>
  );
}
