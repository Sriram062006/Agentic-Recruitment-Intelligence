import React from "react";
import {
  Briefcase,
  Users,
  Grid3X3,
  ListOrdered,
  Layers,
  PlayCircle,
} from "lucide-react";

interface NavItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  active?: boolean;
  disabled?: boolean;
}

export const NavigationShell: React.FC = () => {
  const navItems: NavItem[] = [
    {
      id: "workspace",
      label: "Recruitment Workspace",
      icon: <Layers className="h-4 w-4" />,
      active: true,
    },
    {
      id: "jobs",
      label: "Job Management",
      icon: <Briefcase className="h-4 w-4" />,
      disabled: true,
    },
    {
      id: "candidates",
      label: "Candidate Pool",
      icon: <Users className="h-4 w-4" />,
      disabled: true,
    },
    {
      id: "evaluation",
      label: "Create Evaluation",
      icon: <PlayCircle className="h-4 w-4" />,
      disabled: true,
    },
    {
      id: "matrix",
      label: "Evaluation Matrix",
      icon: <Grid3X3 className="h-4 w-4" />,
      disabled: true,
    },
    {
      id: "rankings",
      label: "Role Rankings",
      icon: <ListOrdered className="h-4 w-4" />,
      disabled: true,
    },
  ];

  return (
    <nav className="border-b border-border bg-white px-6">
      <div className="mx-auto flex max-w-7xl space-x-1 overflow-x-auto">
        {navItems.map((item) => (
          <button
            key={item.id}
            disabled={item.disabled}
            className={`flex items-center space-x-2 border-b-2 px-4 py-3 text-xs font-medium transition-colors ${
              item.active
                ? "border-blue-600 text-blue-600"
                : item.disabled
                ? "cursor-not-allowed border-transparent text-gray-400 opacity-60"
                : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
            }`}
          >
            {item.icon}
            <span>{item.label}</span>
            {item.disabled && (
              <span className="rounded bg-gray-100 px-1.5 py-0.2 text-[10px] text-gray-400">
                Phase {item.id === "jobs" ? "2-3" : item.id === "candidates" ? "2-4" : item.id === "evaluation" ? "7" : item.id === "matrix" ? "10" : "11"}
              </span>
            )}
          </button>
        ))}
      </div>
    </nav>
  );
};
