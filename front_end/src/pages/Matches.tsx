// Matches.tsx（イメージ）

import { useEffect, useState } from "react";
import axios from "axios";
import { BACKEND_URL } from "../config";

type Match = {
  club_id: number;
  club_name: string;
  club_tags: string[];
  events: {
    event_id: number;
    title: string;
    description: string | null;
    start_time: string | null;
    location: string | null;
  }[];
};

const USER_ID = 1; // まずは固定で 1 にして挙動確認

export default function Matches() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await axios.get(`${BACKEND_URL}/api/matches`, {
          params: { user_id: USER_ID },
        });
        console.log("Matches API response:", res.data);
        setMatches(res.data);
      } catch (err) {
        console.error("Failed to load matches:", err);
        setMatches([]);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return <div className="p-4">Loading matches...</div>;
  }

  if (!matches.length) {
    return (
      <div className="p-4">
        <h1 className="text-3xl font-bold mb-2">Your Matches</h1>
        <p>You have no liked clubs yet. Swipe right on clubs in Discover to save them here.</p>
      </div>
    );
  }

  return (
    <div className="p-4">
      <h1 className="text-3xl font-bold mb-4">Your Matches</h1>
      {matches.map((m) => (
        <div key={m.club_id} className="mb-4 rounded-lg shadow bg-white p-3">
          <h2 className="text-xl font-semibold">{m.club_name}</h2>
          <p className="text-sm text-gray-600">
            Tags: {m.club_tags.join(", ") || "—"}
          </p>
          {m.events.length ? (
            <ul className="mt-2 space-y-1">
              {m.events.map((ev) => (
                <li key={ev.event_id} className="text-sm">
                  <span className="font-medium">{ev.title}</span>
                  {ev.start_time && (
                    <span className="ml-2 text-gray-500">
                      ({new Date(ev.start_time).toLocaleString()})
                    </span>
                  )}
                  {ev.location && (
                    <span className="ml-2 text-gray-500">＠{ev.location}</span>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-sm text-gray-500">No upcoming events yet.</p>
          )}
        </div>
      ))}
    </div>
  );
}
