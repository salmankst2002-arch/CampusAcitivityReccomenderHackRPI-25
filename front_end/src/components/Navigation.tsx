import React from "react";
import { Link, useLocation } from "react-router-dom";
import { FaCompass, FaHeart, FaUser } from "react-icons/fa"; // Icons for retro navigation

const Navigation: React.FC = () => {
  const location = useLocation();

  const navItems = [
    { path: "/", icon: FaCompass, label: "Discover" },
    { path: "/matches", icon: FaHeart, label: "Saved" },
  ];

  return (
    // Fixed bottom navigation using daisyUI's btm-nav
    <div className="join bg-base-200 min-w-32 flex justify-center">
      {navItems.map(({ path, icon: Icon, label }) => (
        <Link
          key={path}
          to={path}
          // Highlight the active link
          className={
            "mx-5 " + location.pathname === path
              ? "active bg-primary text-primary-content"
              : "text-base-content"
          }
        >
          {/* @ts-ignore */}
          <Icon className="h-5 w-5 inline" />
          <span className="btm-nav-label text-xs mx-1">{label}</span>
        </Link>
      ))}
    </div>
  );
};

export default Navigation;
