import React, { useState, useEffect, useRef } from "react";
import Card from "./components/ui/Card";
import { useProfileCache } from './hooks/useProfileCache';
import ResultsDisplay from './components/ResultsDisplay';
import ProfileForm from './components/ProfileForm';

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

  return (
    <div className="min-h-screen py-5" style={meshBgStyle}>
      <div className="max-w-4xl mx-auto space-y-5">
        {/* Top Section: Title & Banner */}
        <Card className="shadow-lg border border-slate-200 text-center py-8">
          <h2 className="text-3xl font-bold mb-2 text-primary">Executive Profile Generator</h2>
          <div className="text-base text-muted-foreground">
            Conduct in-depth executive profile enrichment powered by AI and Web Search
          </div>
        </Card>
        {/* Form Section */}
        <ProfileForm 
          form={form}
          loading={loading}
          llmOptions={llmOptions}
          searchOptions={searchOptions}
          handleChange={handleChange}
          handleSubmit={handleSubmit}
        />
        {/* Progress Section */}
        {progress.length > 0 && (
          <Card className="shadow border border-slate-200 p-5">
            <h3 className="text-lg font-semibold mb-2">Progress</h3>
            <ul className="text-sm list-disc pl-5">
              {progress.map((msg, i) => (
                <li key={i}>{msg}</li>
              ))}
            </ul>
          </Card>
        )}
        {/* Result Section */}
        {result && <ResultsDisplay result={result} />}
        {/* Error Section */}
        {error && (
          <Card className="shadow border border-slate-200 p-5 bg-red-50">
            <h3 className="text-xl font-semibold mb-3 text-red-600">Error</h3>
            <p className="text-red-800 text-sm">{error}</p>
          </Card>
        )}
      </div>
    </div>
  );
}

export default App;
