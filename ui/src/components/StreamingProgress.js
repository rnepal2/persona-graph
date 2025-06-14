import React from 'react';
import { motion } from 'framer-motion';

const StreamingProgress = ({ currentNode, completedNodes }) => {
  const steps = [
    { key: 'planner_supervisor_node', label: 'Planning Research', icon: '🎯', color: 'blue' },
    { key: 'background_agent_node', label: 'Background Research', icon: '🔍', color: 'green' },
    { key: 'leadership_agent_node', label: 'Leadership Analysis', icon: '👑', color: 'purple' },
    { key: 'reputation_agent_node', label: 'Reputation Assessment', icon: '⭐', color: 'yellow' },
    { key: 'strategy_agent_node', label: 'Strategic Analysis', icon: '🎯', color: 'red' },
    { key: 'profile_aggregator_node', label: 'Profile Compilation', icon: '📊', color: 'indigo' }
  ];

  return (
    <div className="space-y-3">
      {steps.map((step, index) => {
        const isCompleted = completedNodes.includes(step.key);
        const isCurrent = currentNode === step.key;
        const isPending = !isCompleted && !isCurrent;
        
        return (
          <motion.div
            key={step.key}
            className="flex items-center space-x-3 p-3 rounded-lg bg-white border"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <div className={`
              w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold
              ${isCompleted 
                ? 'bg-green-100 text-green-700 border-2 border-green-300' 
                : isCurrent 
                ? 'bg-blue-100 text-blue-700 border-2 border-blue-300 animate-pulse' 
                : 'bg-gray-100 text-gray-500 border-2 border-gray-200'
              }
            `}>
              {isCompleted ? (
                <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              ) : isCurrent ? (
                step.icon
              ) : (
                step.icon
              )}
            </div>
            
            <div className="flex-1">
              <div className={`
                font-medium text-sm
                ${isCompleted ? 'text-green-700' : isCurrent ? 'text-blue-700' : 'text-gray-500'}
              `}>
                {step.label}
              </div>
              <div className="text-xs text-gray-400">
                {isCompleted ? 'Completed' : isCurrent ? 'In Progress...' : 'Pending'}
              </div>
            </div>
            
            {isCurrent && (
              <div className="w-4 h-4 border-2 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
            )}
          </motion.div>
        );
      })}
    </div>
  );
};

export default StreamingProgress;
