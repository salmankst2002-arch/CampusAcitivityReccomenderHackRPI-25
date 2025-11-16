import { useEffect, useState } from "react";
import axios from "axios";
import { BACKEND_URL } from "../config";
import type { Event, Club } from "../types/backend";

type MatchItem = {
  club_id: number;
  club_name: string;
  club_tags: string[];
  events: Event[];
};

const USER_ID = 1;

export default function Matches() {
  const [matches, setMatches] = useState<MatchItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMatches = async () => {
      setLoading(true);
      try {
        const res = await axios.get<MatchItem[]>(`${BACKEND_URL}/api/matches`, {
          params: { user_id: USER_ID },
        });
        console.log("Matches response:", res.data);
        setMatches(res.data);
      } catch (err) {
        console.error("Failed to load matches:", err);
        setMatches([]);
      } finally {
        setLoading(false);
      }
    };

    fetchMatches();
  }, []);

  if (loading) {
    return <div className="p-4">Loading your saved matches...</div>;
  }

  if (matches.length === 0) {
    return (
      <div className="p-4">
        <h1 className="text-2xl font-bold mb-2">Your Matches</h1>
        <p className="text-sm text-gray-600">
          You have no liked clubs yet. Swipe right on clubs in Discover to save them here.
        </p>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-6">
      <h1 className="text-2xl font-bold">Your Matches</h1>

      {matches.map((match) => (
        <section key={match.club_id} className="bg-white rounded-xl shadow p-4">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-xl font-semibold">{match.club_name}</h2>
            {match.club_tags && match.club_tags.length > 0 && (
              <div className="flex flex-wrap gap-1 text-xs text-gray-500">
                {match.club_tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-0.5 rounded-full bg-gray-100 border border-gray-200"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>

          {match.events.length === 0 ? (
            <p className="text-sm text-gray-600">
              No upcoming events for this club yet.
            </p>
          ) : (
            <ul className="space-y-2">
              {match.events.map((ev) => (
                <li key={ev.event_id} className="border-t pt-2 first:border-none first:pt-0">
                  <div className="font-medium">{ev.title}</div>
                  <div className="text-xs text-gray-600">
                    {ev.start_time && (
                      <span className="mr-2">
                        {new Date(ev.start_time).toLocaleString()}
                      </span>
                    )}
                    {ev.location && <span>@ {ev.location}</span>}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      ))}
    </div>
  );
}
