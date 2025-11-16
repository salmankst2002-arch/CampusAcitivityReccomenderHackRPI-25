// front_end/src/pages/Login.tsx
import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

type DemoUser = {
  id: number;
  label: string;
};

// These labels correspond to seed.py users
const DEMO_USERS: DemoUser[] = [
  { id: 1, label: "Alice (freshman, CS)" },
  { id: 2, label: "Bob (sophomore, Economics)" },
  { id: 3, label: "Carol (junior, Environmental Science)" },
  { id: 4, label: "Dave (freshman, Undeclared)" },
  { id: 5, label: "Yusuke (freshman, CS, albany.edu)" },
];

export default function Login() {
  const { userId, setUserId } = useAuth();
  const navigate = useNavigate();
  const [selectedId, setSelectedId] = useState<number>(userId ?? 1);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setUserId(selectedId);
    // After "login", go to Discover page
    navigate("/", { replace: true });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#f7f0e6] to-[#fff1f8]">
      <div className="w-full max-w-md bg-white shadow-lg rounded-2xl p-8">
        <h1 className="text-2xl font-bold mb-4 text-center text-brown-800">
          RetroCampus Login
        </h1>
        <p className="text-sm text-gray-600 mb-6 text-center">
          For the hackathon demo, please choose a demo student profile to log in as.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block text-sm font-medium text-gray-700">
            Select your demo user
            <select
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
              value={selectedId}
              onChange={(e) => setSelectedId(Number(e.target.value))}
            >
              {DEMO_USERS.map((u) => (
                <option key={u.id} value={u.id}>
                  {`#${u.id} — ${u.label}`}
                </option>
              ))}
            </select>
          </label>

          <button
            type="submit"
            className="w-full mt-2 rounded-lg bg-amber-600 text-white font-semibold py-2 hover:bg-amber-700 transition-colors"
          >
            Enter RetroCampus
          </button>
        </form>
      </div>
    </div>
  );
}

