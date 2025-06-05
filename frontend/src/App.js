import logo from './logo.svg';
import Button from "./components/ui/Button";
import Card from "./components/ui/Card";
import React, { useState } from "react";

function App() {
  const [form, setForm] = useState({
    name: "",
    title: "",
    company: "",
    summary: ""
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      // Placeholder: Replace with actual backend call
      // const response = await fetch("/api/run-profile-enrichment", { ... })
      // const data = await response.json();
      // setResult(data);
      setTimeout(() => {
        setResult({
          message: "[MVP] Backend call simulated. Results will appear here.",
          debug: form
        });
        setLoading(false);
      }, 1200);
    } catch (err) {
      setError("Failed to run profile enrichment.");
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="max-w-lg mx-auto mt-10 space-y-6">
        <Card>
          <h2 className="text-xl font-bold mb-2">Executive Profile Enrichment</h2>
          <form className="space-y-4" onSubmit={handleSubmit}>
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
              <label className="block text-sm font-medium mb-1">Profile Summary</label>
              <textarea name="summary" value={form.summary} onChange={handleChange} className="w-full border rounded px-3 py-2" rows={3} required />
            </div>
            <Button type="submit" disabled={loading}>
              {loading ? "Running..." : "Enrich Profile"}
            </Button>
          </form>
        </Card>
        <Card>
          <h3 className="text-lg font-semibold mb-2">Results</h3>
          {loading && <div className="text-blue-500">Processing...</div>}
          {error && <div className="text-red-500">{error}</div>}
          {result && (
            <div>
              <pre className="bg-gray-100 rounded p-2 text-xs overflow-x-auto">{JSON.stringify(result, null, 2)}</pre>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

export default App;
