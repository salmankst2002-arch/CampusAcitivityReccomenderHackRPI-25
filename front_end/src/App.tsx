// front_end/src/App.tsx
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Navigation from "./components/Navigation";
import Discover from "./pages/Discover";
import Matches from "./pages/Matches";
import Login from "./pages/Login";
import SignUp from "./pages/SignUp";
import { AuthProvider, useAuth } from "./auth/AuthContext";

const RequireAuth: React.FC<{ children: JSX.Element }> = ({ children }) => {
  const { userId } = useAuth();
  if (!userId) {
    // Not logged in -> send to login page
    return <Navigate to="/login" replace />;
  }
  return children;
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <div className="h-screen bg-base-300 flex flex-col">
          {/* Main Content Area */}
          <main className="flex-1 p-4 overflow-y-auto">
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<SignUp />} />

              <Route
                path="/"
                element={
                  <RequireAuth>
                    <Discover />
                  </RequireAuth>
                }
              />
              <Route
                path="/matches"
                element={
                  <RequireAuth>
                    <Matches />
                  </RequireAuth>
                }
              />

              {/* Fallback route: redirect unknown paths to / */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>

          {/* Fixed Bottom Navigation (hide on login page if you want later) */}
          <div className="flex justify-center items-center pb-4">
            <Navigation />
          </div>
        </div>
      </Router>
    </AuthProvider>
  );
};

export default App;
