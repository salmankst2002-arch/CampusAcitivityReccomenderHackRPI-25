import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navigation from "./components/Navigation";
// Placeholder components for pages
import Discover from "./pages/Discover";
import Matches from "./pages/Matches";

const App: React.FC = () => {
  return (
    // Router component
    <Router>
      <div className="h-screen bg-base-300 flex flex-col">
        {/* Main Content Area */}
        <main className="flex-1 p-4 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Discover />} />
            <Route path="/matches" element={<Matches />} />
          </Routes>
        </main>

        {/* Fixed Bottom Navigation */}
        <div className="flex justify-center items-center pb-4">
          <Navigation />
        </div>
      </div>
    </Router>
  );
};

export default App;
