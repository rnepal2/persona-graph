import React from 'react';
import ReactMarkdown from 'react-markdown';
import Card from './ui/Card';
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from './ui/Accordion';
import CopyButton from './ui/CopyButton';

const ResultsDisplay = ({ result }) => {
  if (!result) return null;

  return (
    <div className="space-y-5">
      {/* Executive Profile Summary */}
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
            <p className="text-gray-500 italic">Profile aggregation in progress...</p>
          )}
        </div>
      </Card>

      {/* Detailed Insights */}
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

      {/* References */}
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
  );
};

export default ResultsDisplay;
