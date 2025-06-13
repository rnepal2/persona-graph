import React from 'react';
import { motion } from 'framer-motion';

const SidebarToggle = ({ isOpen, onToggle }) => {
  return (    <motion.button
      whileHover={{ scale: 1.05, boxShadow: "0 10px 20px rgba(0, 0, 0, 0.1)" }}
      whileTap={{ scale: 0.95 }}
      onClick={onToggle}
      className={`
        fixed left-4 top-4 z-40 p-3 rounded-full shadow-lg border transition-all duration-300
        ${isOpen 
          ? 'bg-blue-600 border-blue-700 text-white hover:bg-blue-700' 
          : 'bg-white border-gray-200 text-gray-700 hover:shadow-xl hover:bg-gray-50'
        }
      `}
      title={isOpen ? "Close profile library" : "Open profile library"}
    >
      <motion.div
        animate={{ rotate: isOpen ? 180 : 0 }}
        transition={{ duration: 0.3 }}
        className="relative"
      >
        {isOpen ? (
          <svg 
            className="w-5 h-5" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M6 18L18 6M6 6l12 12" 
            />
          </svg>
        ) : (
          <svg 
            className="w-5 h-5" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" 
            />
          </svg>
        )}
      </motion.div>
    </motion.button>
  );
};

export default SidebarToggle;
