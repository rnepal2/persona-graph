import Button from "./components/ui/Button";
import Card from "./components/ui/Card";
import React, { useState, useEffect, useRef } from "react";
import { FaSearch } from "react-icons/fa";

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
  const handleSubmit = (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    setError(null);
    setProgress([]);
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
        {/* Input Section */}
        <Card className="shadow border border-slate-200">
          <form className="space-y-5" onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Name</label>
                <input name="name" value={form.name} onChange={handleChange} className="w-full border rounded px-3 py-2" required />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Title</label>
                <input name="title" value={form.title} onChange={handleChange} className="w-full border rounded px-3 py-2" required />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Company</label>
                <input name="company" value={form.company} onChange={handleChange} className="w-full border rounded px-3 py-2" required />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">LinkedIn Profile Link</label>
                <input name="linkedin" value={form.linkedin} onChange={handleChange} className="w-full border rounded px-3 py-2" placeholder="https://linkedin.com/in/..." />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Profile Summary</label>
              <textarea name="summary" value={form.summary} onChange={handleChange} className="w-full border rounded px-3 py-2" rows={3} required />
            </div>
          </form>
        </Card>
        {/* Settings & Search Button Section */}
        <Card className="shadow border border-slate-200">
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
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
            <div className="flex justify-center mt-4">
              <Button type="submit" disabled={loading} className="w-full md:w-auto flex items-center justify-center gap-2 px-8 py-2 text-base">
                <FaSearch className="inline-block mr-2" />
                {loading ? "Running..." : "Search Profile"}
              </Button>
            </div>
          </form>
        </Card>
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
          <Card className="shadow border border-slate-200 p-5">
            <h3 className="text-xl font-semibold mb-3">Enrichment Result</h3>
            <pre className="whitespace-pre-wrap text-sm">{JSON.stringify(result, null, 2)}</pre>
          </Card>
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
