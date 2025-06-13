import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Card from "./components/ui/Card";
import { useProfileCache } from './hooks/useProfileCache';
import ResultsDisplay from './components/ResultsDisplay';
import ProfileForm from './components/ProfileForm';
import ProfileSidebar from './components/ProfileSidebar';
import SidebarToggle from './components/SidebarToggle';
import './styles/custom.css';

const meshBgStyle = {
  backgroundImage: "radial-gradient(circle,rgb(190, 196, 205) 1px, transparent 1px)",
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
      result: (data) => {
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
  }, []); // No dependencies - we manage the connection lifecycle independently

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
  };

  const handleProfileSaved = () => {
    // Refresh sidebar if it's open
    if (sidebarOpen) {
      // The sidebar will refresh when it detects a save
    }
  };

  return (
    <div className="min-h-screen text-gray-800" style={meshBgStyle}>
      {/* Sidebar Toggle */}
      <SidebarToggle 
        isOpen={sidebarOpen} 
        onToggle={() => setSidebarOpen(!sidebarOpen)} 
      />
      
      {/* Sidebar */}
      <ProfileSidebar 
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        onProfileSelect={handleProfileSelect}
      />      {/* Main Content with sidebar offset */}
      <div className={`transition-all duration-300 ${sidebarOpen ? 'ml-80' : 'ml-0'} h-screen overflow-hidden`}>
        <div className="h-full px-4 py-3">        <motion.div 
          layout
          className={`
            h-full w-full transition-all duration-500 ease-in-out
            ${result 
              ? 'grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-6' // Responsive: single column on mobile, two columns on large screens
              : 'flex justify-center items-start pt-8'
            }
          `}
        >{/* Left column - Form and Progress */}          <motion.div
            layout
            className={`${result ? 'w-full h-full overflow-y-auto' : 'max-w-2xl w-full'} space-y-4`}
            initial={{ opacity: 1 }}
            animate={{ opacity: 1 }}
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
            </Card>            {/* Progress Section */}
            {loading && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-3"
              >
                <Card variant="compact">
                  <h2 className="text-lg font-semibold mb-3 flex items-center">
                    <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-primary" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Processing
                  </h2>
                  <div className="space-y-2">
                    {progress.map((p, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="text-sm text-gray-600"
                      >
                        {p}
                      </motion.div>
                    ))}
                  </div>
                </Card>
              </motion.div>
            )}            {error && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="bg-red-50 border-l-4 border-red-400 p-3 rounded"
              >
                <p className="text-red-700 text-sm">{error}</p>
              </motion.div>
            )}
          </motion.div>          {/* Right column - Results */}
          <AnimatePresence mode="wait">
            {result && (
              <motion.div
                layout
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 50 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                className="w-full h-full overflow-y-auto space-y-4"
              >
                <ResultsDisplay 
                  result={result} 
                  onProfileSaved={handleProfileSaved}
                />
              </motion.div>
            )}
          </AnimatePresence>        </motion.div>
        </div>
      </div>
    </div>
  );
}

export default App;
