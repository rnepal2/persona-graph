import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Card from "./components/ui/Card";
import { useProfileCache } from './hooks/useProfileCache';
import ResultsDisplay from './components/ResultsDisplay';
import ProfileForm from './components/ProfileForm';
import ProfileSidebar from './components/ProfileSidebar';
import StreamingProgress from './components/StreamingProgress';
import './styles/custom.css';

const meshBgStyle = {
  backgroundImage: "radial-gradient(circle,rgb(143, 177, 229) 1px, transparent 1px)",
  backgroundSize: "24px 24px",
};

function App() {
  const [form, setForm] = useState({
    name: "",
    title: "",
    company: "",
    summary: "",
    linkedin: "",
    llm: "gemini",
    searchEngine: "duckduckgo"
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState([]);
  const [wsState, setWsState] = useState('disconnected');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  // New streaming states
  const [streamingResult, setStreamingResult] = useState({
    basic_info: null,
    background_info: null,
    leadership_info: null,
    reputation_info: null,
    strategy_info: null,
    aggregated_profile: null,
    metadata: [],
    isComplete: false
  });
  const [currentNode, setCurrentNode] = useState(null);
  const [completedNodes, setCompletedNodes] = useState([]);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const connectionTimeoutRef = useRef(null);
  const maxReconnectDelay = 5000;
  const baseReconnectDelay = 1000;
  const reconnectAttemptsRef = useRef(0);
  const WS_CONNECT_TIMEOUT = 5000;
  
  const { checkCache, updateCache } = useProfileCache();

  const llmOptions = [
    { value: "gemini", label: "Google Gemini" },
    { value: "openai", label: "OpenAI GPT" }
  ];
  const searchOptions = [
    { value: "duckduckgo", label: "DuckDuckGo" },
    { value: "serpapi", label: "SerpAPI" },
    { value: "tavily", label: "Tavily" }
  ];

  // WebSocket connection management
  useEffect(() => {
    let isSubscribed = true;
    const messageHandlers = {
      progress: (data) => {
        if (!isSubscribed) return;
        setProgress(prev => [...prev, data]);
        setError(null);
      },
      node_start: (data) => {
        if (!isSubscribed) return;
        setCurrentNode(data.node);
        setProgress(prev => [...prev, `Starting ${data.node}...`]);
      },
      node_error: (data) => {
        if (!isSubscribed) return;
        setProgress(prev => [...prev, `⚠️ ${data.node} failed: ${data.error}`]);
        // Don't set global error - let processing continue
      },
      partial_result: (data) => {
        if (!isSubscribed) return;
        setStreamingResult(prev => ({
          ...prev,
          ...data,
          isComplete: false
        }));
      },
      node_complete: (data) => {
        if (!isSubscribed) return;
        setCompletedNodes(prev => [...prev, data.node]);
        setProgress(prev => [...prev, `✅ Completed ${data.node}`]);
      },
      final_result: (data) => {
        if (!isSubscribed) return;
        
        // Handle enhanced final result with execution summary
        setResult(data);
        setStreamingResult(prev => ({ ...prev, ...data, isComplete: true }));
        updateCache(form, data);
        setLoading(false);
        setCurrentNode(null);
        
        // Show user-friendly message if there were issues
        if (data.execution_summary && data.execution_summary.failed_agents?.length > 0) {
          setError(`Profile generated with some limitations: ${data.user_message || 'Some components failed to complete.'}`);
        } else {
          setError(null);
        }
        
        // Log execution summary for debugging
        if (data.execution_summary) {
          console.log('Execution Summary:', data.execution_summary);
        }
      },
      result: (data) => {
        // Fallback for non-streaming result
        if (!isSubscribed) return;
        setResult(data);
        updateCache(form, data);
        setLoading(false);
        setError(null);
      },
      error: (data) => {
        if (!isSubscribed) return;
        setError(data);
        setLoading(false);
        setCurrentNode(null);
      }
    };
    
    const connectWebSocket = () => {
      // Don't create a new connection if we already have an open one
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        console.log('WebSocket already connected');
        return;
      }
      
      // If we have a connecting socket, don't create another one
      if (wsRef.current?.readyState === WebSocket.CONNECTING) {
        console.log('WebSocket already connecting');
        return;
      }
      
      try {
        setWsState('connecting');
        const ws = new WebSocket('ws://localhost:5000/ws/enrich-profile');
        
        connectionTimeoutRef.current = setTimeout(() => {
          if (ws.readyState !== WebSocket.OPEN) {
            ws.close();
            if (isSubscribed) {
              setError('Cannot connect to server - please check if the backend is running');
              setWsState('disconnected');
            }
          }
        }, WS_CONNECT_TIMEOUT);
        
        ws.onopen = () => {
          console.log('WebSocket Connected');
          if (isSubscribed) {
            setWsState('connected');
            setError(null);
            reconnectAttemptsRef.current = 0;
          }
          if (connectionTimeoutRef.current) {
            clearTimeout(connectionTimeoutRef.current);
          }
        };
        
        ws.onmessage = (event) => {
          try {
            const { type, data } = JSON.parse(event.data);
            const handler = messageHandlers[type];
            if (handler) {
              handler(data);
            }
          } catch (error) {
            console.error('Error handling WebSocket message:', error);
          }
        };
        
        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          if (isSubscribed) {
            setError('Connection error - please check if the backend is running on port 5000');
            setLoading(false);
          }
        };
        
        ws.onclose = () => {
          console.log('WebSocket Disconnected');
          if (isSubscribed) {
            setWsState('disconnected');
            wsRef.current = null;
            
            // Only attempt reconnect if we're not deliberately closing
            const delay = Math.min(
              maxReconnectDelay,
              baseReconnectDelay * Math.pow(2, reconnectAttemptsRef.current)
            );
            
            reconnectTimeoutRef.current = setTimeout(() => {
              reconnectAttemptsRef.current++;
              if (isSubscribed) {
                connectWebSocket();
              }
            }, delay);
          }
          
          if (connectionTimeoutRef.current) {
            clearTimeout(connectionTimeoutRef.current);
          }
        };
        
        wsRef.current = ws;
      } catch (error) {
        console.error('Failed to create WebSocket connection:', error);
        if (isSubscribed) {
          setError('Cannot connect to server - please check if the backend is running on port 5000');
          setWsState('disconnected');
        }
      }
    };

    // Initial connection
    connectWebSocket();
    
    return () => {
      isSubscribed = false;
      if (wsRef.current) {
        // Prevent reconnection attempts when unmounting
        const ws = wsRef.current;
        wsRef.current = null;
        ws.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (connectionTimeoutRef.current) {
        clearTimeout(connectionTimeoutRef.current);
      }
    };
  }, []); 
  // No dependencies - we manage the connection lifecycle independently
  // Function to ensure WebSocket is connected before sending
  const ensureWebSocketConnection = () => {
    return new Promise((resolve, reject) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      const checkConnection = () => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          resolve();
        } else if (wsState === 'disconnected') {
          reject(new Error('Cannot connect to server - please check if the backend is running'));
        } else {
          setTimeout(checkConnection, 100);
        }
      };

      // Only timeout the connection check, not the entire operation
      const timeoutId = setTimeout(() => {
        reject(new Error('Connection attempt timed out - please check if the backend is running'));
      }, WS_CONNECT_TIMEOUT);

      checkConnection();

      return () => clearTimeout(timeoutId);
    });
  };

  // Send enrichment request via WebSocket
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setProgress([]);
    setResult(null);
    
    // Reset streaming state
    setStreamingResult({
      basic_info: { name: form.name, company: form.company, title: form.title, linkedin_url: form.linkedin },
      background_info: null,
      leadership_info: null,
      reputation_info: null,
      strategy_info: null,
      aggregated_profile: null,
      metadata: [],
      isComplete: false
    });
    setCurrentNode(null);
    setCompletedNodes([]);

    // Check cache before making the request
    const cachedResult = checkCache(form);
    if (cachedResult) {
      console.log('Using cached result');
      setResult(cachedResult);
      setLoading(false);
      return;
    }

    try {
      await ensureWebSocketConnection();
      wsRef.current.send(JSON.stringify({
        type: "enrich",
        data: form
      }));
    } catch (error) {
      console.error('Connection error:', error);
      setError(error.message || 'Failed to connect to server. Please try again.');
      setLoading(false);
    }
  };
  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleProfileSelect = (profile) => {
    setResult(profile);
    // Also update streaming result for consistency
    if (profile) {
      setStreamingResult({ ...profile, isComplete: true });
    } else {
      setStreamingResult({
        basic_info: null,
        background_info: null,
        leadership_info: null,
        reputation_info: null,
        strategy_info: null,
        aggregated_profile: null,
        metadata: [],
        isComplete: false
      });
    }
    
    if (profile === null) {
      setError(null);
    }
  };

  const handleProfileSaved = () => {
    // Refresh sidebar if it's open
    if (sidebarOpen) {
      // The sidebar will refresh when it detects a save
    }
  };

  return (
    <div className="min-h-screen text-gray-800" style={meshBgStyle}>
      {/* Sidebar */}
      <ProfileSidebar 
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        onProfileSelect={handleProfileSelect}
      />      
      {/* Main Content with sidebar offset */}
      <div className={`transition-all duration-300 ${sidebarOpen ? 'ml-80' : 'ml-20'} h-screen overflow-hidden`}>
        <div className="h-full px-4 py-3 overflow-y-auto">
          <motion.div 
            layout
            transition={{ 
              duration: 0.9, 
              ease: [0.32, 0.72, 0, 1], 
              type: "tween",
              layout: { duration: 0.9, ease: [0.32, 0.72, 0, 1] }
            }}
            className="w-full flex items-start pt-4 gap-6 min-h-full"
          >
            {/* Left column - Form and Progress */}
            <motion.div
              layout
              transition={{ 
                duration: 0.9, 
                ease: [0.32, 0.72, 0, 1], 
                type: "tween" 
              }}
              className={`space-y-4 transition-all duration-900 ease-out ${result ? 'w-1/2 min-w-96' : 'w-full max-w-4xl mx-auto'}`}
              initial={{ opacity: 1 }}
              animate={{ opacity: 1 }}
            >
              <motion.div
                layout
                transition={{ duration: 0.8, ease: [0.4, 0.0, 0.2, 1], type: "tween" }}
              >
                <Card className="shadow-lg">
                  <h1 className="text-3xl text-red-700 font-bold mb-2">Persona-Graph: Executive Profile Generator</h1>
                  <p className="text-gray-600 font-semibold mb-4">
                    Generate an in-depth Executive Profile with Web Search and AI
                  </p>
                  <ProfileForm
                    form={form}
                    setForm={setForm}
                    loading={loading}
                    wsState={wsState}
                    llmOptions={llmOptions}
                    searchOptions={searchOptions}
                    onSubmit={handleSubmit}
                  />
                </Card>
              </motion.div>

              {/* Progress Section - Enhanced for streaming */}
              {loading && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.6, ease: "easeOut" }}
                  className="space-y-3"
                >
                  <Card variant="compact">
                    <h2 className="text-lg font-semibold mb-3 flex items-center">
                      <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-primary" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Processing Profile
                    </h2>
                    
                    {/* Enhanced Streaming Progress */}
                    <StreamingProgress 
                      currentNode={currentNode}
                      completedNodes={completedNodes}
                    />
                    
                    {/* Progress Messages */}
                    <div className="mt-4 space-y-1 max-h-32 overflow-y-auto border-t pt-3">
                      <h3 className="text-sm font-medium text-gray-700 mb-2">Activity Log:</h3>
                      {progress.slice(-8).map((p, i) => (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          className="text-xs text-gray-600 pl-2 border-l-2 border-gray-200"
                        >
                          {p}
                        </motion.div>
                      ))}
                    </div>
                  </Card>
                </motion.div>
              )}

              {error && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.5 }}
                  className="bg-red-50 border-l-4 border-red-400 p-3 rounded"
                >
                  <p className="text-red-700 text-sm">{error}</p>
                </motion.div>
              )}
            </motion.div>

            {/* Right column - Results with streaming support */}
            <AnimatePresence mode="wait">
              {(result || (streamingResult.basic_info && !streamingResult.isComplete)) && (
                <motion.div
                  key="results"
                  initial={{ opacity: 0, width: 0, scale: 0.95 }}
                  animate={{ 
                    opacity: 1, 
                    width: "50%",
                    scale: 1,
                    transition: { 
                      width: { duration: 0.9, ease: [0.32, 0.72, 0, 1] },
                      opacity: { duration: 0.5, delay: 0.3, ease: "easeOut" },
                      scale: { duration: 0.6, delay: 0.25, ease: "easeOut" }
                    }
                  }}
                  exit={{ 
                    opacity: 0,
                    width: 0,
                    scale: 0.95,
                    transition: { 
                      opacity: { duration: 0.25, ease: "easeIn" },
                      scale: { duration: 0.3, ease: "easeIn" },
                      width: { duration: 0.7, delay: 0.1, ease: [0.32, 0.72, 0, 1] }
                    }
                  }}
                  className="min-w-96 overflow-hidden flex flex-col min-h-0"
                  style={{ willChange: 'width, opacity, transform' }}
                >
                  <div className="flex-1 min-h-0">
                    <ResultsDisplay 
                      result={result || streamingResult} 
                      isStreaming={loading && !streamingResult.isComplete}
                      onProfileSaved={handleProfileSaved}
                    />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

export default App;