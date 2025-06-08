import React from 'react';
import Button from './ui/Button';
import Card from './ui/Card';
import { FaSearch } from 'react-icons/fa';

const ProfileForm = ({ 
  form, 
  loading, 
  llmOptions, 
  searchOptions, 
  handleChange, 
  handleSubmit 
}) => {
  return (
    <form onSubmit={handleSubmit}>
      {/* Input Section */}
      <Card className="shadow border border-slate-200 mb-5">
        <div className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Name</label>
              <input 
                name="name" 
                value={form.name} 
                onChange={handleChange} 
                className="w-full border rounded px-3 py-2" 
                required 
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Title</label>
              <input 
                name="title" 
                value={form.title} 
                onChange={handleChange} 
                className="w-full border rounded px-3 py-2" 
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Company</label>
              <input 
                name="company" 
                value={form.company} 
                onChange={handleChange} 
                className="w-full border rounded px-3 py-2" 
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">LinkedIn Profile Link</label>
              <input 
                name="linkedin" 
                value={form.linkedin} 
                onChange={handleChange} 
                className="w-full border rounded px-3 py-2" 
                placeholder="https://linkedin.com/in/..." 
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Known Information</label>
            <textarea 
              name="summary" 
              value={form.summary} 
              onChange={handleChange} 
              className="w-full border rounded px-3 py-2" 
              rows={4} 
              placeholder="Enter basic available information..." 
              required 
            />
          </div>
        </div>
      </Card>

      {/* Settings & Search Button Section */}
      <Card className="shadow border border-slate-200">
        <div className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">AI Model</label>
              <select 
                name="llm" 
                value={form.llm} 
                onChange={handleChange} 
                className="w-full border rounded px-3 py-2"
              >
                {llmOptions.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Search Engine</label>
              <select 
                name="searchEngine" 
                value={form.searchEngine} 
                onChange={handleChange} 
                className="w-full border rounded px-3 py-2"
              >
                {searchOptions.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="flex justify-center">
            <Button 
              type="submit" 
              disabled={loading} 
              className="w-full md:w-auto flex items-center justify-center gap-2 px-8 py-2 text-base"
            >
              <FaSearch className="inline-block mr-2" />
              {loading ? "Running..." : "Search Profile"}
            </Button>
          </div>
        </div>
      </Card>
    </form>
  );
};

export default ProfileForm;
