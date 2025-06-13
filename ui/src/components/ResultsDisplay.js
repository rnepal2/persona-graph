import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { motion } from 'framer-motion';
import Card from './ui/Card';
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from './ui/Accordion';
import CopyButton from './ui/CopyButton';

const ResultsDisplay = ({ result, onProfileSaved }) => {
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  
  if (!result) return null;
  const handleSaveProfile = async () => {
    setSaving(true);
    setSaveSuccess(false);
    
    try {
      const response = await fetch('http://localhost:5000/api/save-enriched-profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(result),
      });
      
      if (response.ok) {
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 3000);
        if (onProfileSaved) {
          onProfileSaved();
        }
      } else {
        throw new Error('Failed to save profile');
      }
    } catch (error) {
      console.error('Error saving profile:', error);
      // Could add error state here
    } finally {
      setSaving(false);
    }
  };
  return (    
    <motion.div
      className="h-full flex flex-col space-y-4 overflow-hidden"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >      {/* Executive Profile Summary */}
      <Card variant="compact" className="shadow border border-slate-200 flex-1 flex flex-col min-h-0 overflow-hidden">
        <div className="flex justify-between items-start mb-3 flex-shrink-0">
          <h3 className="text-xl font-semibold text-gray-800 flex items-center">
            <span className="bg-primary/10 p-2 rounded-full mr-2">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" />
              </svg>
            </span>
            Executive Profile Summary
          </h3>
          <div className="flex items-center gap-2">
            {result.aggregated_profile && (
              <CopyButton text={result.aggregated_profile} />
            )}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleSaveProfile}
              disabled={saving}
              className={`
                px-4 py-2 rounded-lg text-sm font-medium transition-all
                ${saving 
                  ? 'bg-gray-200 text-gray-500 cursor-not-allowed' 
                  : saveSuccess
                    ? 'bg-green-100 text-green-700 border border-green-200'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }
              `}
            >
              {saving ? (
                <div className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Saving...
                </div>
              ) : saveSuccess ? (
                <div className="flex items-center">
                  <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Saved!
                </div>
              ) : (
                <div className="flex items-center">
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                  </svg>
                  Save Profile
                </div>
              )}
            </motion.button>
          </div>
        </div>        <div className="prose prose-sm max-w-none flex-1 min-h-0">
          {result.aggregated_profile ? (
            <div className="bg-white rounded-lg h-full overflow-y-auto custom-scrollbar">
              <div className="p-6 prose prose-slate prose-headings:mb-3 prose-p:mb-2 prose-ul:mb-2">
                <ReactMarkdown
                  components={{
                    h1: ({node, children, ...props}) => 
                      children ? <h1 className="text-3xl font-bold mb-6 text-gray-900" {...props}>{children}</h1> : null,
                    h2: ({node, children, ...props}) => 
                      children ? <h2 className="text-2xl font-semibold mb-4 text-gray-800" {...props}>{children}</h2> : null,
                    h3: ({node, children, ...props}) => 
                      children ? <h3 className="text-xl font-semibold mb-3 text-gray-800" {...props}>{children}</h3> : null,
                    p: ({node, children, ...props}) => 
                      <p className="mb-4 text-gray-600 leading-relaxed" {...props}>{children}</p>,
                    ul: ({node, children, ...props}) => 
                      <ul className="list-disc pl-5 mb-4 space-y-2 text-gray-600" {...props}>{children}</ul>,
                    ol: ({node, children, ...props}) => 
                      <ol className="list-decimal pl-5 mb-4 space-y-2 text-gray-600" {...props}>{children}</ol>,
                    li: ({node, children, ...props}) => 
                      <li className="leading-relaxed" {...props}>{children}</li>,
                    a: ({node, children, href, ...props}) => 
                      children ? (
                        <a 
                          href={href}
                          className="text-blue-600 hover:text-blue-800 underline decoration-blue-200 hover:decoration-blue-600 transition-all" 
                          {...props}
                        >
                          {children}
                        </a>
                      ) : null,
                    em: ({node, children, ...props}) => 
                      <em className="italic text-gray-700" {...props}>{children}</em>,
                    strong: ({node, children, ...props}) => 
                      <strong className="font-semibold text-gray-900" {...props}>{children}</strong>,
                    blockquote: ({node, children, ...props}) => 
                      <blockquote className="border-l-4 border-gray-200 pl-4 my-4 italic text-gray-700" {...props}>
                        {children}
                      </blockquote>,
                  }}
                >
                  {result.aggregated_profile}
                </ReactMarkdown>
              </div>
            </div>
          ) : (
            <p className="text-gray-500">No profile summary available.</p>
          )}
        </div>
      </Card>        {/* Wrap Detailed Insights and References in a main Accordion */}
      <div className="flex-shrink-0 overflow-y-auto max-h-96">
        <Accordion>
        {/* Detailed Insights Section */}
        <AccordionItem value="insights">
          <AccordionTrigger>
            <div className="flex items-center">
              <span className="bg-primary/10 p-1 rounded-full mr-2">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                  <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
                </svg>
              </span>
              <h3 className="text-lg font-semibold text-gray-800">Detailed Insights</h3>
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <div className="flex flex-col gap-4 mt-2">
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
          </AccordionContent>
        </AccordionItem>

        {/* References Section */}
        {result.metadata && (
          <AccordionItem value="references">
            <AccordionTrigger>
              <div className="flex items-center">
                <span className="bg-primary/10 p-1 rounded-full mr-2">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 005.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z" />
                  </svg>
                </span>
                <h3 className="text-lg font-semibold text-gray-800">References</h3>
              </div>
            </AccordionTrigger>
            <AccordionContent>
              <div className="bg-white rounded-lg mt-2">
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
            </AccordionContent>
          </AccordionItem>        )}
      </Accordion>
      </div>
    </motion.div>
  );
};

export default ResultsDisplay;
