import Button from "./components/ui/Button";
import Card from "./components/ui/Card";
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "./components/ui/Accordion";
import React, { useState, useEffect, useRef } from "react";
import { FaSearch } from "react-icons/fa";
import ReactMarkdown from 'react-markdown';
import { useProfileCache } from './hooks/useProfileCache';

/*
Rabindra Nepal is a Principal Data Scientist at Johnson & Johnson and he previously 
completed his PhD in Physics from University of Nebraska-Lincoln.
*/
// Copy button component
const CopyButton = ({ text }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(text)
      .then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000); // Reset after 2 seconds
      })
      .catch(err => {
        console.error('Failed to copy:', err);
      });
  };

  return (
    <button
      onClick={handleCopy}
      className="flex items-center gap-1 px-2 py-1 text-sm text-gray-500 hover:text-gray-700 rounded-md hover:bg-gray-100 transition-colors"
      title={copied ? "Copied!" : "Copy to clipboard"}
    >
      {copied ? (
        <>
          <svg 
            className="w-5 h-5 text-green-500" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M5 13l4 4L19 7"
            />
          </svg>
          <span className="text-green-500">Copied!</span>
        </>
      ) : (
        <>
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
              d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"
            />
          </svg>
          <span>Copy</span>
        </>
      )}
    </button>
  );
};

// Add mesh background style
const meshBgStyle = {
  backgroundImage:
    "radial-gradient(circle,rgb(190, 196, 205) 1px, transparent 1px)",
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
  const wsRef = useRef(null);

  const llmOptions = [
    { value: "gemini", label: "Google Gemini" },
    { value: "openai", label: "OpenAI GPT" }
  ];
  const searchOptions = [
    { value: "duckduckgo", label: "DuckDuckGo" },
    { value: "serpapi", label: "SerpAPI" },
    { value: "tavily", label: "Tavily" }
  ];

  // Connect to WebSocket on mount
  useEffect(() => {
    const ws = new window.WebSocket("ws://localhost:5000/ws/enrich-profile");
    wsRef.current = ws;
    ws.onopen = () => {
      // No debug message
    };
    ws.onmessage = (event) => {
      // Expect JSON messages: { type: 'progress'|'result'|'error', data: ... }
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'progress') {
          setProgress((prev) => [...prev, msg.data]);
        } else if (msg.type === 'result') {
          // Cache the successful result
          updateCache(form, msg.data);
          
          setResult(msg.data);
          setLoading(false);
        } else if (msg.type === 'error') {
          setError(msg.data);
          setLoading(false);
        }
      } catch {
        // Ignore malformed messages
      }
    };
    ws.onerror = () => {
      setError("WebSocket error");
      setLoading(false);
    };
    ws.onclose = () => {
      // No debug message
    };
    return () => {
      ws.close();
    };
  }, []);

  // Send enrichment request via WebSocket
  const { checkCache, updateCache, isCacheHit } = useProfileCache();

  const handleSubmit = (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    setError(null);
    setProgress([]);

    // Check cache first
    const cachedResult = checkCache(form);
    
    if (cachedResult) {
      // Use cached result
      setResult(cachedResult);
      setLoading(false);
      setProgress(['Retrieved from cache']);
      return;
    }

    // If not in cache, proceed with WebSocket request
    if (wsRef.current && wsRef.current.readyState === 1) {
      wsRef.current.send(JSON.stringify({ type: "enrich", data: form }));
    } else {
      setError("WebSocket not connected");
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
        <form onSubmit={handleSubmit}>
          {/* Input Section */}
          <Card className="shadow border border-slate-200 mb-5">
            <div className="space-y-5">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Name</label>
                  <input name="name" value={form.name} onChange={handleChange} className="w-full border rounded px-3 py-2" required />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Title</label>
                  <input name="title" value={form.title} onChange={handleChange} className="w-full border rounded px-3 py-2"  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Company</label>
                  <input name="company" value={form.company} onChange={handleChange} className="w-full border rounded px-3 py-2"  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">LinkedIn Profile Link</label>
                  <input name="linkedin" value={form.linkedin} onChange={handleChange} className="w-full border rounded px-3 py-2" placeholder="https://linkedin.com/in/..." />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Known Information</label>
                <textarea name="summary" value={form.summary} onChange={handleChange} className="w-full border rounded px-3 py-2" rows={4} placeholder="Enter basic available information..." required />
              </div>
            </div>
          </Card>
          {/* Settings & Search Button Section */}
          <Card className="shadow border border-slate-200">
            <div className="space-y-5">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">AI Model</label>
                  <select name="llm" value={form.llm} onChange={handleChange} className="w-full border rounded px-3 py-2">
                    {llmOptions.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Search Engine</label>
                  <select name="searchEngine" value={form.searchEngine} onChange={handleChange} className="w-full border rounded px-3 py-2">
                    {searchOptions.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="flex justify-center">
                <Button type="submit" disabled={loading} className="w-full md:w-auto flex items-center justify-center gap-2 px-8 py-2 text-base">
                  <FaSearch className="inline-block mr-2" />
                  {loading ? "Running..." : "Search Profile"}
                </Button>
              </div>
            </div>
          </Card>
        </form>
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
        {result && (
          <div className="space-y-5">
            {/* Main Profile Section */}
            <Card className="shadow border border-slate-200 p-5">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-xl font-semibold text-gray-800 flex items-center">
                  <span className="bg-primary/10 p-2 rounded-full mr-2">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" />
                    </svg>
                  </span>
                  Executive Profile Summary
                </h3>
                {result.aggregated_profile && (
                  <CopyButton text={result.aggregated_profile} />
                )}
              </div>
              <div className="prose prose-sm max-w-none">
                {result.aggregated_profile ? (
                  <div className="bg-white rounded-lg max-h-[500px] overflow-y-auto custom-scrollbar">
                    <div className="p-6 prose prose-slate prose-headings:mb-3 prose-p:mb-2 prose-ul:mb-2">
                      <ReactMarkdown
                        components={{
                          h1: ({node, ...props}) => <h1 className="text-3xl font-bold mb-6 text-gray-900" {...props} />,
                          h2: ({node, ...props}) => <h2 className="text-2xl font-semibold mb-4 text-gray-800" {...props} />,
                          h3: ({node, ...props}) => <h3 className="text-xl font-semibold mb-3 text-gray-800" {...props} />,
                          p: ({node, ...props}) => <p className="mb-4 text-gray-600 leading-relaxed" {...props} />,
                          ul: ({node, ...props}) => <ul className="list-disc pl-5 mb-4 space-y-2 text-gray-600" {...props} />,
                          ol: ({node, ...props}) => <ol className="list-decimal pl-5 mb-4 space-y-2 text-gray-600" {...props} />,
                          li: ({node, ...props}) => <li className="leading-relaxed" {...props} />,
                          a: ({node, ...props}) => (
                            <a 
                              className="text-blue-600 hover:text-blue-800 underline decoration-blue-200 hover:decoration-blue-600 transition-all" 
                              {...props}
                            />
                          ),
                          em: ({node, ...props}) => <em className="italic text-gray-700" {...props} />,
                          strong: ({node, ...props}) => <strong className="font-semibold text-gray-900" {...props} />,
                          blockquote: ({node, ...props}) => (
                            <blockquote className="border-l-4 border-gray-200 pl-4 my-4 italic text-gray-700" {...props} />
                          ),
                        }}
                      >
                        {result.aggregated_profile}
                      </ReactMarkdown>
                    </div>
                  </div>
                ) : (
                  <p className="text-gray-500 italic">Profile aggregation in progress...</p>
                )}
              </div>
            </Card>

            {/* Agent Reports Section */}
            <Card className="shadow border border-slate-200 p-5">
              <h3 className="text-xl font-semibold mb-4 text-gray-800 flex items-center">
                <span className="bg-primary/10 p-2 rounded-full mr-2">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                    <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
                  </svg>
                </span>
                Detailed Insights
              </h3>
              <div className="flex flex-col gap-4">
                {result.background_info && (
                  <div className="bg-white rounded-lg p-4 border border-gray-100">
                    <h4 className="font-semibold text-gray-700 mb-2">Professional Background</h4>
                    <div className="text-sm text-gray-600">
                      {typeof result.background_info === 'object' 
                        ? Object.entries(result.background_info).map(([key, value]) => (
                            <div key={key} className="mb-2">
                              <span className="font-medium">{key.replace(/_/g, ' ').toLowerCase()}: </span>
                              <span>{value}</span>
                            </div>
                          ))
                        : <p>{result.background_info}</p>
                      }
                    </div>
                  </div>
                )}
                {result.leadership_info && (
                  <div className="bg-white rounded-lg p-4 border border-gray-100">
                    <h4 className="font-semibold text-gray-700 mb-2">Leadership Profile</h4>
                    <div className="text-sm text-gray-600">
                      {Array.isArray(result.leadership_info) 
                        ? result.leadership_info.map((info, i) => <p key={i} className="mb-2">{info}</p>)
                        : <p>{result.leadership_info}</p>
                      }
                    </div>
                  </div>
                )}
                {result.strategy_info && (
                  <div className="bg-white rounded-lg p-4 border border-gray-100">
                    <h4 className="font-semibold text-gray-700 mb-2">Strategic Approach</h4>
                    <div className="text-sm text-gray-600">
                      {Array.isArray(result.strategy_info) 
                        ? result.strategy_info.map((info, i) => <p key={i} className="mb-2">{info}</p>)
                        : <p>{result.strategy_info}</p>
                      }
                    </div>
                  </div>
                )}
                {result.reputation_info && (
                  <div className="bg-white rounded-lg p-4 border border-gray-100">
                    <h4 className="font-semibold text-gray-700 mb-2">Market Reputation</h4>
                    <div className="text-sm text-gray-600">
                      {Array.isArray(result.reputation_info) 
                        ? result.reputation_info.map((info, i) => <p key={i} className="mb-2">{info}</p>)
                        : <p>{result.reputation_info}</p>
                      }
                    </div>
                  </div>
                )}
              </div>
            </Card>

            {/* References Section */}
            {result.metadata && (
              <Card className="shadow border border-slate-200 p-5">
                <h3 className="text-xl font-semibold mb-4 text-gray-800 flex items-center">
                  <span className="bg-primary/10 p-2 rounded-full mr-2">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 005.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z" />
                    </svg>
                  </span>
                  References
                </h3>
                <div className="bg-white rounded-lg">
                  <Accordion>
                    {result.metadata
                      .filter(meta => meta.background_references)
                      .flatMap(meta => meta.background_references)
                      .map((ref, index) => (
                        <AccordionItem key={index} value={`ref-${index}`}>
                          <AccordionTrigger>
                            <div className="text-left">
                              <h4 className="text-sm font-medium text-blue-600">
                                {ref.title}
                              </h4>
                            </div>
                          </AccordionTrigger>
                          <AccordionContent>
                            <div className="space-y-3">
                              {ref.snippet && (
                                <p className="text-sm text-gray-600 break-words">
                                  {ref.snippet}
                                </p>
                              )}
                              <a
                                href={ref.link}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800 gap-1"
                              >
                                View Source
                                <svg 
                                  className="w-4 h-4 text-gray-400" 
                                  fill="none" 
                                  stroke="currentColor" 
                                  viewBox="0 0 24 24"
                                >
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                </svg>
                              </a>
                            </div>
                          </AccordionContent>
                        </AccordionItem>
                    ))}
                  </Accordion>
                </div>
              </Card>
            )}
          </div>
        )}
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
