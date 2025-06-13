import React from "react";

function Card({ children, className = "", variant = "default", ...props }) {
  const baseClasses = "bg-white border border-gray-200 text-gray-900 transition-shadow duration-200";
  
  const variants = {
    default: "rounded-xl shadow-md p-6 hover:shadow-lg",
    compact: "rounded-lg shadow-sm p-4 hover:shadow-md",
    minimal: "rounded-lg border-gray-100 p-3 hover:shadow-sm",
    sidebar: "rounded-lg bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200 p-4 hover:shadow-md"
  };

  return (
    <div
      className={`${baseClasses} ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

export default Card;
