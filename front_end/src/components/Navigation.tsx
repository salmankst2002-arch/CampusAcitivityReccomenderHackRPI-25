import React from "react";
import { Link, useLocation } from "react-router-dom";
import { FaCompass, FaHeart, FaUser } from "react-icons/fa"; // Icons for retro navigation

const Navigation: React.FC = () => {
  const location = useLocation();

  const navItems = [
    { path: "/", icon: FaCompass, label: "Discover" },
    { path: "/matches", icon: FaHeart, label: "Saved" },
    { path: "/profile", icon: FaUser, label: "Profile" },
  ];

  return (
    // Fixed bottom navigation using daisyUI's btm-nav
    <div className="btm-nav btm-nav-md bg-base-200">
      {navItems.map(({ path, icon: Icon, label }) => (
        <Link
          key={path}
          to={path}
          // Highlight the active link
          className={
            location.pathname === path
              ? "active bg-primary text-primary-content"
              : "text-base-content"
          }
        >
          {/* @ts-ignore */}
          <Icon className="h-5 w-5" />
          <span className="btm-nav-label text-xs">{label}</span>
        </Link>
      ))}
    </div>
  );
};

export default Navigation;
