import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navigation from "./components/Navigation";
// Placeholder components for pages
import Discover from "./pages/Discover";

const App: React.FC = () => {
  return (
    // Router component
    <Router>
      <div className="min-h-screen bg-base-300 flex flex-col">
        {/* Main Content Area */}
        <main className="flex-grow p-4 pb-20">
          <Routes>
            <Route path="/" element={<Discover />} />
          </Routes>
        </main>

        {/* Fixed Bottom Navigation */}
        <Navigation />
      </div>
    </Router>
  );
};

export default App;
