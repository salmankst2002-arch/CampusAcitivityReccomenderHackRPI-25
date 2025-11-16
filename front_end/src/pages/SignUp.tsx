// front_end/src/pages/SignUp.tsx
import type { FormEvent } from "react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function SignUp() {
  const { setUserId } = useAuth();
  const navigate = useNavigate();
  const [signUpData, setSignUpData] = useState({
    email: "",
    name: "",
    year: "",
    major: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSignUpChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setSignUpData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSignUpSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    // Validate fields
    if (!signUpData.email || !signUpData.name) {
      setError("Email and name are required");
      setLoading(false);
      return;
    }

    try {
      const response = await fetch("http://localhost:5000/api/users", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: signUpData.email,
          name: signUpData.name,
          year: signUpData.year,
          major: signUpData.major,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to create user");
      }

      const userData = await response.json();
      
      // Auto-login the newly created user
      setUserId(userData.user_id);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#f7f0e6] to-[#fff1f8]">
      <div className="w-full max-w-md bg-white shadow-lg rounded-2xl p-8">
        <h1 className="text-2xl font-bold mb-4 text-center text-brown-800">
          Create Account
        </h1>

        <p className="text-sm text-gray-600 mb-6 text-center">
          Create your account to join RetroCampus
        </p>

        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSignUpSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              type="email"
              name="email"
              value={signUpData.email}
              onChange={handleSignUpChange}
              required
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
              placeholder="your.email@rpi.edu"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Full Name
            </label>
            <input
              type="text"
              name="name"
              value={signUpData.name}
              onChange={handleSignUpChange}
              required
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
              placeholder="John Doe"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Year
            </label>
            <select
              name="year"
              value={signUpData.year}
              onChange={handleSignUpChange}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
            >
              <option value="">Select year</option>
              <option value="freshman">Freshman</option>
              <option value="sophomore">Sophomore</option>
              <option value="junior">Junior</option>
              <option value="senior">Senior</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Major
            </label>
            <input
              type="text"
              name="major"
              value={signUpData.major}
              onChange={handleSignUpChange}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
              placeholder="Computer Science"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-4 rounded-lg bg-green-600 text-white font-semibold py-2 hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Creating Account..." : "Create Account"}
          </button>
        </form>

        <div className="mt-6 border-t pt-6">
          <p className="text-sm text-gray-600 text-center mb-3">
            Already have an account?
          </p>
          <button
            onClick={() => navigate("/login")}
            className="w-full text-sm text-amber-600 hover:text-amber-800 font-medium transition-colors"
          >
            Back to Login
          </button>
        </div>
      </div>
    </div>
  );
}
