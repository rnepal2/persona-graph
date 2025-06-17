import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

const StreamingProgress = ({ currentNode, completedNodes, startTime }) => {
  const [elapsedTime, setElapsedTime] = useState(0);
  const [localCurrentNode, setLocalCurrentNode] = useState(null);
  const [localCompletedNodes, setLocalCompletedNodes] = useState([]);
  
  // Use ref to store the display time to reduce re-renders
  const displayTimeRef = useRef(0);
  const timerRef = useRef(null);

  // Smoother timer effect with less frequent updates
  useEffect(() => {
    if (!startTime) {
      displayTimeRef.current = 0;
      setElapsedTime(0);
      return;
    }
    
    const updateTimer = () => {
      const now = Date.now();
      const elapsed = now - startTime;
      displayTimeRef.current = elapsed;
      
      // Only update state every 500ms to reduce flickering
      setElapsedTime(elapsed);
    };
    
    // Initial update
    updateTimer();
    
    // Update every 500ms for smoother experience
    timerRef.current = setInterval(updateTimer, 500);

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [startTime]);

  // Sync with parent but with slight delay to reduce lag
  useEffect(() => {
    const timeout = setTimeout(() => {
      setLocalCurrentNode(currentNode);
    }, 50);
    
    return () => clearTimeout(timeout);
  }, [currentNode]);

  useEffect(() => {
    const timeout = setTimeout(() => {
      setLocalCompletedNodes(completedNodes);
    }, 100);
    
    return () => clearTimeout(timeout);
  }, [completedNodes]);

  const formatTime = (ms) => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    if (minutes > 0) {
      return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
    return `${remainingSeconds}s`;
  };

  const steps = [
    { key: 'planner_supervisor_node', label: 'Planning Research', icon: '🎯', color: 'blue' },
    { key: 'background_agent_node', label: 'Background Research', icon: '🔍', color: 'green' },
    // Parallel execution group
    { key: 'parallel_group', label: 'Parallel Analysis', icon: '⚡', color: 'purple', isGroup: true },
    { key: 'leadership_agent_node', label: 'Leadership Analysis', icon: '👑', color: 'purple', isParallel: true },
    { key: 'reputation_agent_node', label: 'Reputation Assessment', icon: '⭐', color: 'yellow', isParallel: true },
    { key: 'strategy_agent_node', label: 'Strategic Analysis', icon: '🎯', color: 'red', isParallel: true },
    { key: 'profile_aggregator_node', label: 'Profile Compilation', icon: '📊', color: 'indigo' }
  ];

  // Enhanced parallel detection logic
  const parallelNodes = ['leadership_agent_node', 'reputation_agent_node', 'strategy_agent_node'];
  const backgroundCompleted = localCompletedNodes.includes('background_agent_node');
  const anyParallelNodeStarted = parallelNodes.some(node => 
    localCurrentNode === node || localCompletedNodes.includes(node)
  );
  
  // Show parallel phase if background is done OR parallel execution has started
  const isParallelPhase = 
    localCurrentNode === 'parallel_execution' || 
    backgroundCompleted ||
    anyParallelNodeStarted;
    
  const completedParallelNodes = parallelNodes.filter(node => localCompletedNodes.includes(node));

  return (
    <div className="space-y-4">
      {/* Timer Section - optimized for smooth rendering */}
      {startTime && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-3"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium text-blue-700">Processing Time</span>
            </div>
            <div className="flex items-center space-x-3">
              {/* Use a more stable animation approach */}
              <div className="text-lg font-bold text-blue-800 tabular-nums min-w-[60px] text-right">
                {formatTime(elapsedTime)}
              </div>
              <div className="flex space-x-1">
                <div className="w-1 h-4 bg-blue-300 rounded-full animate-pulse" style={{ animationDelay: '0ms' }}></div>
                <div className="w-1 h-4 bg-blue-400 rounded-full animate-pulse" style={{ animationDelay: '150ms' }}></div>
                <div className="w-1 h-4 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          </div>
          <div className="mt-2 w-full bg-blue-100 rounded-full h-1">
            <motion.div 
              className="bg-gradient-to-r from-blue-400 to-blue-600 h-1 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(100, (elapsedTime / 120000) * 100)}%` }}
              transition={{ duration: 0.5, ease: "easeOut" }}
            />
          </div>
        </motion.div>
      )}

      {/* Progress Steps */}
      <div className="space-y-3">
        {steps.map((step, index) => {
          if (step.isParallel && !isParallelPhase) {
            return null; // Hide parallel steps until we reach that phase
          }

          if (step.isGroup) {
            if (!isParallelPhase) return null;
            
            return (
              <motion.div
                key={step.key}
                className="bg-purple-50 border-2 border-purple-200 rounded-lg p-3"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <div className="flex items-center space-x-3 mb-3">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold bg-purple-100 text-purple-700 border-2 border-purple-300">
                    {step.icon}
                  </div>
                  <div className="flex-1">
                    <div className="font-medium text-sm text-purple-700">
                      {step.label}
                    </div>
                    <div className="text-xs text-purple-500">
                      {localCurrentNode === 'parallel_execution' 
                        ? 'Initializing parallel execution...' 
                        : `${completedParallelNodes.length}/3 components completed`
                      }
                    </div>
                  </div>
                  {/* Show spinner when parallel execution is active */}
                  {(localCurrentNode === 'parallel_execution' || anyParallelNodeStarted) && completedParallelNodes.length < 3 && (
                    <div className="w-4 h-4 border-2 border-purple-200 border-t-purple-600 rounded-full animate-spin"></div>
                  )}
                </div>
                
                {/* Progress bar for parallel execution */}
                <div className="w-full bg-purple-100 rounded-full h-2 mb-2">
                  <motion.div 
                    className="bg-purple-500 h-2 rounded-full transition-all duration-500"
                    animate={{ 
                      width: localCurrentNode === 'parallel_execution' 
                        ? '10%' // Small progress when just starting
                        : `${(completedParallelNodes.length / 3) * 100}%` 
                    }}
                  />
                </div>
                
                {/* Show parallel agents immediately when parallel execution starts */}
                {(localCurrentNode === 'parallel_execution' || completedParallelNodes.length > 0 || backgroundCompleted) && (
                  <div className="text-xs text-purple-600 bg-purple-50 rounded px-2 py-1 mt-2">
                    <div className="flex items-center space-x-1">
                      <svg className="w-3 h-3 animate-pulse" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M10 12L8 10l2-2 2 2-2 2zM10 4l6 6-6 6-6-6 6-6z"/>
                      </svg>
                      <span>Running: Leadership • Reputation • Strategy</span>
                    </div>
                  </div>
                )}
              </motion.div>
            );
          }

          if (step.isParallel) {
            const isCompleted = localCompletedNodes.includes(step.key);
            const isCurrent = localCurrentNode === step.key;
            // Show as active if background is completed and this parallel node hasn't finished
            const isParallelActive = backgroundCompleted && !isCompleted;
            
            return (
              <motion.div
                key={step.key}
                className="ml-6 flex items-center space-x-3 p-2 rounded-lg bg-white border border-gray-100"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 + (index * 0.05) }}
              >
                <div className={`
                  w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold
                  ${isCompleted 
                    ? 'bg-green-100 text-green-700 border border-green-300' 
                    : (isCurrent || isParallelActive)
                    ? 'bg-blue-100 text-blue-700 border border-blue-300' 
                    : 'bg-gray-100 text-gray-500 border border-gray-200'
                  }
                `}>
                  {isCompleted ? (
                    <svg className="w-3 h-3 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    step.icon
                  )}
                </div>
                
                <div className="flex-1">
                  <div className={`
                    font-medium text-xs
                    ${isCompleted 
                      ? 'text-green-700' 
                      : (isCurrent || isParallelActive) 
                      ? 'text-blue-700' 
                      : 'text-gray-500'
                    }
                  `}>
                    {step.label}
                  </div>
                  <div className="text-xs text-gray-400">
                    {isCompleted 
                      ? 'Completed' 
                      : (isCurrent || isParallelActive) 
                      ? 'In Progress...' 
                      : 'Pending'
                    }
                  </div>
                </div>
                
                {/* Show spinner only when this specific node is actually running */}
                {isCurrent && (
                  <div className="w-3 h-3 border border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
                )}
              </motion.div>
            );
          }

          // Regular sequential steps
          const isCompleted = localCompletedNodes.includes(step.key);
          const isCurrent = localCurrentNode === step.key;
          
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
                  ? 'bg-blue-100 text-blue-700 border-2 border-blue-300' 
                  : 'bg-gray-100 text-gray-500 border-2 border-gray-200'
                }
              `}>
                {isCompleted ? (
                  <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
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
              
              {/* Show spinner only when this specific node is actually running */}
              {isCurrent && (
                <div className="w-4 h-4 border-2 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};

export default StreamingProgress;
