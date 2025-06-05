import React from "react";

function Card({ children, className = "", ...props }) {
  return (
    <div
      className={
        "rounded-xl border bg-card text-card-foreground shadow-sm p-6 " +
        className
      }
      {...props}
    >
      {children}
    </div>
  );
}

export default Card;
