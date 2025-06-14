import React from 'react';
import { motion } from 'framer-motion';
import Button from './ui/Button';
import Card from './ui/Card';
import { FaSearch } from 'react-icons/fa';

const ProfileForm = ({ 
  form, 
  loading, 
  wsState,
  llmOptions, 
  searchOptions, 
  setForm,
  onSubmit 
}) => {
  const handleChange = (e) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  return (
    <motion.form 
      layout
      transition={{ duration: 0.9, ease: [0.32, 0.72, 0, 1], type: "tween" }}
      onSubmit={onSubmit} 
      className="ml-0"
    >
      {/* Input Section */}
      <span className='mb-3 text-sm font-semibold'>Basic Information</span>
      <motion.div layout transition={{ duration: 0.9, ease: [0.32, 0.72, 0, 1], type: "tween" }}>
        <Card variant="compact" className="shadow border border-slate-200 mb-4">
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Name</label>
                <input 
                  name="name" 
                  value={form.name} 
                  onChange={handleChange} 
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200" 
                  required 
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Title</label>
                <input 
                  name="title" 
                  value={form.title} 
                  onChange={handleChange} 
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200" 
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Company</label>
                <input 
                  name="company" 
                  value={form.company} 
                  onChange={handleChange} 
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200" 
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">LinkedIn Profile Link</label>
                <input 
                  name="linkedin" 
                  value={form.linkedin} 
                  onChange={handleChange} 
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200" 
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
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200" 
                rows={5} 
                placeholder="Enter basic available information..." 
                required 
              />
            </div>
          </div>
        </Card>
      </motion.div>
      
      {/* Settings & Search Button Section */}
      <span className='mb-3 text-sm font-semibold'>Settings</span>
      <motion.div layout transition={{ duration: 0.9, ease: [0.32, 0.72, 0, 1], type: "tween" }}>
        <Card variant="compact" className="shadow border border-slate-200">
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">AI Model</label>
                <select 
                  name="llm" 
                  value={form.llm} 
                  onChange={handleChange} 
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
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
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                >
                  {searchOptions.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex justify-center pt-2">
              <Button 
                type="submit" 
                disabled={loading} 
                className="w-full md:w-auto flex items-center justify-center gap-2 px-12 py-3 text-base font-medium"
              >
                <FaSearch className="inline-block mr-2" />
                {loading ? "Running..." : "Search Profile"}
              </Button>
            </div>
          </div>
        </Card>
      </motion.div>
    </motion.form>
  );
};

export default ProfileForm;
