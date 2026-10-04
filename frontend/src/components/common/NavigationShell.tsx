import React from "react";
import { Briefcase, Users, Grid3X3, Layers } from "lucide-react";

export type NavTab = "workspace" | "jobs" | "candidates" | "evaluation";

interface NavigationShellProps {
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
}

export const NavigationShell: React.FC<NavigationShellProps> = ({
  activeTab,
  onTabChange,
}) => {
  const navItems = [
    {
      id: "workspace" as NavTab,
      label: "Recruitment Workspace",
      icon: <Layers className="h-4 w-4" />,
    },
    {
      id: "jobs" as NavTab,
      label: "Job Management",
      icon: <Briefcase className="h-4 w-4" />,
    },
    {
      id: "candidates" as NavTab,
      label: "Candidate Pool",
      icon: <Users className="h-4 w-4" />,
    },
    {
      id: "evaluation" as NavTab,
      label: "Multi-Role Evaluation & Matrix",
      icon: <Grid3X3 className="h-4 w-4" />,
    },
  ];

  return (
    <nav className="border-b border-border bg-white px-6 shadow-xs">
      <div className="mx-auto flex max-w-7xl space-x-2 overflow-x-auto">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onTabChange(item.id)}
            className={`flex items-center space-x-2 border-b-2 px-4 py-3 text-xs font-semibold transition-colors ${
              activeTab === item.id
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
            }`}
          >
            {item.icon}
            <span>{item.label}</span>
          </button>
        ))}
      </div>
    </nav>
  );
};
