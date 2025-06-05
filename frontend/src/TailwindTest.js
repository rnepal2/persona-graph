import React from "react";

function TailwindTest() {
  return (
    <div className="flex m-5 p-2 items-center justify-center">
      <div className="bg-white rounded-xl shadow-lg p-8 max-w-md w-full">
        <h1 className="text-3xl font-bold mb-4 text-center text-blue-700">Tailwind CSS + ShadCN UI Test</h1>
        <p className="mb-6 text-gray-700 text-center">
          If you see this card styled with a gradient background, rounded corners, and blue text, Tailwind CSS is working!
        </p>
        <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition">Test Button</button>
      </div>
    </div>
  );
}

export default TailwindTest;
