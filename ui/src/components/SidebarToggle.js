import React from 'react';
import { motion } from 'framer-motion';
import { Bars3Icon } from '@heroicons/react/24/outline';

const SidebarToggle = ({ isOpen, onToggle }) => {
  // Only show when sidebar is collapsed
  if (isOpen) return null;
  
  return (
    <motion.button
      whileHover={{ scale: 1.05, boxShadow: "0 8px 16px rgba(0, 0, 0, 0.1)" }}
      whileTap={{ scale: 0.95 }}
      onClick={onToggle}
      className="fixed left-2 top-2 z-30 p-2 rounded-lg shadow-lg border border-gray-200 bg-white text-gray-700 hover:shadow-xl hover:bg-gray-50 transition-all duration-300"
      title="Open profile library"
    >
      <Bars3Icon className="w-5 h-5" />
    </motion.button>
  );
};

export default SidebarToggle;
