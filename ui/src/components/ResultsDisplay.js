import React, { useState, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  UserIcon, 
  DocumentTextIcon, 
  BookOpenIcon, 
  CloudArrowDownIcon, 
  CheckCircleIcon,
  ClockIcon,
  PencilIcon,
  XMarkIcon,
  PlusIcon,
  TrashIcon,
  LinkIcon as ExternalLinkIcon
} from '@heroicons/react/24/outline';
import Card from './ui/Card';
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from './ui/Accordion';
import CopyButton from './ui/CopyButton';

// Skeleton loader component
const SkeletonLoader = ({ lines = 3, height = "h-4" }) => (
  <div className="space-y-3 animate-pulse">
    {Array.from({ length: lines }, (_, i) => (
      <div key={i} className={`bg-gray-200 rounded ${height} ${i === lines - 1 ? 'w-3/4' : 'w-full'}`}></div>
    ))}
  </div>
);

// Enhanced streaming section component with consistent markdown rendering
const StreamingSection = ({ title, content, isLoading, icon }) => {
  const showLoading = isLoading && !content;
  
  return (
    <motion.div 
      layout
      className="bg-white rounded-lg p-4 border border-gray-100"
    >
      <h4 className="font-semibold text-gray-700 mb-3 flex items-center">
        {icon && <span className="mr-2">{icon}</span>}
        {title}
        {showLoading && <div className="ml-2 w-4 h-4 border-2 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>}
      </h4>
      <AnimatePresence mode="wait">
        {content ? (
          <motion.div
            key="content"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="prose prose-slate max-w-none prose-sm"
          >
            <ReactMarkdown>{content}</ReactMarkdown>
          </motion.div>
        ) : showLoading ? (
          <motion.div key="skeleton" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <SkeletonLoader lines={4} />
          </motion.div>
        ) : (
          <motion.div key="waiting" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-gray-400 text-sm italic">
            Waiting for results...
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

// Save button with different states
const SaveButton = ({ saving, saveSuccess, isStreaming, onClick, hasUnsavedChanges = false }) => {
  const getButtonContent = () => {
    if (saving) {
      return (
        <div className="flex items-center">
          <div className="animate-spin -ml-1 mr-2 h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
          Updating...
        </div>
      );
    }
    
    if (saveSuccess) {
      return (
        <div className="flex items-center">
          <CheckCircleIcon className="w-4 h-4 mr-1" />
          Updated!
        </div>
      );
    }
    
    if (isStreaming) {
      return (
        <div className="flex items-center">
          <ClockIcon className="w-4 h-4 mr-1 animate-pulse" />
          Processing...
        </div>
      );
    }
    
    return (
      <div className="flex items-center">
        <CloudArrowDownIcon className="w-4 h-4 mr-1" />
        {hasUnsavedChanges ? 'Save Changes' : 'Save Profile'}
        {hasUnsavedChanges && <span className="ml-1 w-2 h-2 bg-orange-400 rounded-full"></span>}
      </div>
    );
  };

  const buttonClass = `
    px-4 py-2 rounded-lg text-sm font-medium transition-all
    ${saving || isStreaming
      ? 'bg-gray-200 text-gray-500 cursor-not-allowed' 
      : saveSuccess
        ? 'bg-green-100 text-green-700 border border-green-200'
        : hasUnsavedChanges
          ? 'bg-orange-600 text-white hover:bg-orange-700'
          : 'bg-blue-600 text-white hover:bg-blue-700'
    }
  `;

  return (
    <motion.button
      whileHover={{ scale: isStreaming ? 1 : 1.05 }}
      whileTap={{ scale: isStreaming ? 1 : 0.95 }}
      onClick={onClick}
      disabled={saving || isStreaming}
      className={buttonClass}
    >
      {getButtonContent()}
    </motion.button>
  );
};

// EditableSection component for handling inline editing
const EditableSection = ({ title, content, onSave, isLoading, icon, placeholder = "Enter content..." }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(content || '');
  const [saving, setSaving] = useState(false);
  const textareaRef = useRef(null);

  const handleEdit = () => {
    setEditContent(content || '');
    setIsEditing(true);
    setTimeout(() => textareaRef.current?.focus(), 100);
  };

  const handleCancel = () => {
    setEditContent(content || '');
    setIsEditing(false);
  };

  const handleSave = async () => {
    if (editContent.trim() === (content || '').trim()) {
      setIsEditing(false);
      return;
    }

    setSaving(true);
    try {
      await onSave(editContent.trim());
      setIsEditing(false);
    } catch (error) {
      console.error('Error saving content:', error);
      alert('Failed to save changes. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      handleCancel();
    } else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSave();
    }
  };

  return (
    <motion.div 
      layout
      className="bg-white rounded-lg p-4 border border-gray-100 group hover:border-gray-200 transition-colors"
    >
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-semibold text-gray-700 flex items-center">
          {icon && <span className="mr-2">{icon}</span>}
          {title}
          {isLoading && !content && (
            <div className="ml-2 w-4 h-4 border-2 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
          )}
        </h4>
        
        {!isEditing && !isLoading && (
          <button
            onClick={handleEdit}
            className="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-md hover:bg-gray-100"
            title="Edit content"
          >
            <PencilIcon className="w-4 h-4 text-gray-500" />
          </button>
        )}
      </div>

      <AnimatePresence mode="wait">
        {isEditing ? (
          <motion.div
            key="editing"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-3"
          >
            <textarea
              ref={textareaRef}
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              onKeyDown={handleKeyDown}
              className="w-full min-h-[200px] p-3 border border-gray-300 rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder={placeholder}
            />
            <div className="flex items-center justify-between">
              <div className="text-xs text-gray-500">
                Press Ctrl+Enter to save, Escape to cancel
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleCancel}
                  className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800 transition-colors"
                  disabled={saving}
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving || editContent.trim() === (content || '').trim()}
                  className="px-4 py-1.5 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center space-x-1"
                >
                  {saving && <div className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin"></div>}
                  <span>{saving ? 'Saving...' : 'Save'}</span>
                </button>
              </div>
            </div>
          </motion.div>
        ) : content ? (
          <motion.div
            key="content"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="prose prose-slate max-w-none prose-sm"
          >
            <ReactMarkdown>{content}</ReactMarkdown>
          </motion.div>
        ) : isLoading ? (
          <SkeletonLoader lines={4} />
        ) : (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-gray-400 text-sm italic py-4 text-center border-2 border-dashed border-gray-200 rounded-md"
          >
            No content available. Click edit to add content.
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

// ReferenceManager component for handling references
const ReferenceManager = ({ references = [], onSave }) => {
  const [refs, setRefs] = useState(references);
  const [isAdding, setIsAdding] = useState(false);
  const [newRef, setNewRef] = useState({ title: '', link: '', snippet: '' });
  const [saving, setSaving] = useState(false);
  const [deletingIndex, setDeletingIndex] = useState(null);

  // Update local refs when references prop changes
  React.useEffect(() => {
    console.log('[ReferenceManager] References prop updated:', references);
    setRefs(references);
  }, [references]);

  const handleAddReference = () => {
    setNewRef({ title: '', link: '', snippet: '' });
    setIsAdding(true);
  };

  const handleSaveNewRef = async () => {
    if (!newRef.title.trim() || !newRef.link.trim()) {
      alert('Title and Link are required');
      return;
    }

    setSaving(true);
    try {
      const updatedRefs = [...refs, { ...newRef, id: Date.now() }];
      console.log('[ReferenceManager] Adding new reference:', newRef);
      console.log('[ReferenceManager] Updated refs:', updatedRefs);
      
      // Call onSave first to update the database
      await onSave(updatedRefs);
      
      // Only update local state after successful save
      setRefs(updatedRefs);
      setIsAdding(false);
      setNewRef({ title: '', link: '', snippet: '' });
      
      console.log('[ReferenceManager] Successfully added new reference');
    } catch (error) {
      console.error('Error adding reference:', error);
      alert('Failed to add reference. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteRef = async (index) => {
    if (!window.confirm('Are you sure you want to delete this reference?')) return;

    const refToDelete = refs[index];
    console.log('[ReferenceManager] Deleting reference at index:', index, refToDelete);

    setDeletingIndex(index);
    try {
      const updatedRefs = refs.filter((_, i) => i !== index);
      console.log('[ReferenceManager] Updated refs after delete:', updatedRefs);
      
      // Call onSave first to update the database
      await onSave(updatedRefs);
      
      // Only update local state after successful save
      setRefs(updatedRefs);
      
      console.log('[ReferenceManager] Successfully deleted reference');
    } catch (error) {
      console.error('Error deleting reference:', error);
      alert('Failed to delete reference. Please try again.');
      // Don't restore refs here - the database update failed, so keep local state as is
    } finally {
      setDeletingIndex(null);
    }
  };

  return (
    <div className="space-y-4">
      {/* Add Reference Button with top margin */}
      <div className="flex justify-between items-center mt-3">
        <h4 className="font-medium text-gray-700 ml-4">References ({refs.length})</h4>
        <button
          onClick={handleAddReference}
          className="flex items-center space-x-1 px-3 py-1.5 mt-2 mr-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
          disabled={isAdding || saving}
        >
          <PlusIcon className="w-5 h-5" />
          <span>Add Reference</span>
        </button>
      </div>

      {/* Add New Reference Form */}
      {isAdding && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-blue-50 border border-blue-200 rounded-lg p-4"
        >
          <h5 className="font-medium text-gray-800 mb-3">Add New Reference</h5>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Title *</label>
              <input
                type="text"
                value={newRef.title}
                onChange={(e) => setNewRef(prev => ({ ...prev, title: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Reference title"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Link *</label>
              <input
                type="url"
                value={newRef.link}
                onChange={(e) => setNewRef(prev => ({ ...prev, link: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="https://example.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description (Optional)</label>
              <textarea
                value={newRef.snippet}
                onChange={(e) => setNewRef(prev => ({ ...prev, snippet: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
                placeholder="Brief description of the reference"
              />
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setIsAdding(false)}
                className="px-3 py-1.5 text-gray-600 hover:text-gray-800 transition-colors"
                disabled={saving}
              >
                Cancel
              </button>
              <button
                onClick={handleSaveNewRef}
                disabled={saving || !newRef.title.trim() || !newRef.link.trim()}
                className="px-4 py-1.5 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center space-x-1"
              >
                {saving && <div className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin"></div>}
                <span>{saving ? 'Adding...' : 'Add Reference'}</span>
              </button>
            </div>
          </div>
        </motion.div>
      )}

      {/* References List */}
      {refs.length > 0 ? (
        <Accordion>
          {refs.map((ref, index) => (
            <AccordionItem key={index} value={`ref-${index}`}>
              <AccordionTrigger>
                <div className="flex items-center justify-between w-full mr-4">
                  <div className="text-left flex-1">
                    <h4 className="text-sm font-medium text-blue-600">{ref.title}</h4>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteRef(index);
                    }}
                    disabled={deletingIndex === index}
                    className="p-1 rounded-md hover:bg-red-100 transition-colors group disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Delete reference"
                  >
                    {deletingIndex === index ? (
                      <div className="w-4 h-4 border-2 border-red-200 border-t-red-500 rounded-full animate-spin"></div>
                    ) : (
                      <TrashIcon className="w-4 h-4 text-gray-400 group-hover:text-red-500 transition-colors" />
                    )}
                  </button>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-3">
                  {ref.snippet && (
                    <p className="text-sm text-gray-600 break-words">{ref.snippet}</p>
                  )}
                  <div className="flex items-center justify-between">
                    <a
                      href={ref.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800 gap-1"
                    >
                      View Source
                      <ExternalLinkIcon className="w-4 h-4 text-gray-400" />
                    </a>
                    <button
                      onClick={() => handleDeleteRef(index)}
                      disabled={deletingIndex === index}
                      className="flex items-center gap-1 px-2 py-1 text-xs text-red-500 hover:text-red-700 hover:bg-red-100 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {deletingIndex === index ? (
                        <>
                          <div className="w-3 h-3 border border-red-400 border-t-transparent rounded-full animate-spin"></div>
                          Deleting...
                        </>
                      ) : (
                        <>
                          <TrashIcon className="w-3 h-3" />
                          Delete
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      ) : (
        <div className="text-center py-8 text-gray-500 border-2 border-dashed border-gray-200 rounded-lg">
          <BookOpenIcon className="w-8 h-8 text-gray-400 mx-auto mb-2" />
          <p className="text-sm">No references available</p>
          <p className="text-xs text-gray-400">Add references to support the profile content</p>
        </div>
      )}
    </div>
  );
};

const ResultsDisplay = ({ result, isStreaming = false, onProfileSaved }) => {
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [profileData, setProfileData] = useState(result);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  
  // Update local state when result changes
  React.useEffect(() => {
    if (result) {
      setProfileData(result);
      console.log('[ResultsDisplay] Profile data updated:', {
        id: result.id,
        basic_info_id: result.basic_info?.id,
        name: result.basic_info?.name || result.name
      });
    }
  }, [result]);
  
  if (!profileData) return null;

  const handleSaveProfile = async () => {
    if (isStreaming) return;
    
    setSaving(true);
    setSaveSuccess(false);
    
    try {
      // Check if this is an existing profile (has basic_info with name) or a new one
      const basicInfo = profileData.basic_info;
      const isExistingProfile = basicInfo && basicInfo.name;
      
      let endpoint = 'http://localhost:5000/api/save-enriched-profile';
      
      if (isExistingProfile) {
        // For existing profiles, use update endpoint to replace the current version
        endpoint = 'http://localhost:5000/api/update-existing-profile';
      }
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profileData),
      });
      
      if (response.ok) {
        setSaveSuccess(true);
        setHasUnsavedChanges(false); // Reset unsaved changes flag
        setTimeout(() => setSaveSuccess(false), 3000);
        onProfileSaved?.();
      } else {
        throw new Error('Failed to save profile');
      }
    } catch (error) {
      console.error('Error saving profile:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateSection = async (section, content) => {
    try {
      console.log('[ResultsDisplay] Updating section:', section);
      console.log('[ResultsDisplay] Profile data for section update:', {
        id: profileData.id,
        basic_info_id: profileData.basic_info?.id,
        name: profileData.basic_info?.name || profileData.name,
        linkedin_url: profileData.basic_info?.linkedin_url || profileData.linkedin_url
      });
      
      // Ensure we're sending the correct profile identification
      const requestData = {
        profile_data: {
          ...profileData,
          // Include all possible ID fields to ensure backend can identify the profile
          id: profileData.id || profileData.basic_info?.id,
          name: profileData.basic_info?.name || profileData.name,
          linkedin_url: profileData.basic_info?.linkedin_url || profileData.linkedin_url
        },
        section,
        content
      };
      
      console.log('[ResultsDisplay] Sending section update request:', requestData);
      
      const response = await fetch('http://localhost:5000/api/update-profile-section', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData),
      });

      const responseData = await response.json();
      console.log('[ResultsDisplay] Section update response:', responseData);

      if (response.ok) {
        // Update local state
        setProfileData(prev => ({
          ...prev,
          [section]: content
        }));
        setHasUnsavedChanges(true); // Mark as having unsaved changes
        console.log('[ResultsDisplay] Successfully updated section locally:', section);
      } else {
        throw new Error(responseData.error || 'Failed to update section');
      }
    } catch (error) {
      console.error('Error updating section:', error);
      throw error;
    }
  };

  const handleUpdateReferences = async (references) => {
    try {
      console.log('[ResultsDisplay] Updating references:', references);
      console.log('[ResultsDisplay] Current profile data:', profileData);
      
      // Include the actual profile data being displayed to ensure we update the right version
      const requestData = {
        profile_data: {
          ...profileData,
          // Ensure we include any ID that might identify the specific version
          id: profileData.id || profileData.basic_info?.id,
          name: profileData.basic_info?.name || profileData.name,
          linkedin_url: profileData.basic_info?.linkedin_url || profileData.linkedin_url
        },
        references
      };
      
      console.log('[ResultsDisplay] Sending update request:', requestData);
      
      const response = await fetch('http://localhost:5000/api/update-profile-references', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData),
      });

      const responseData = await response.json();
      console.log('[ResultsDisplay] Update response:', responseData);

      if (response.ok) {
        // Update local state immediately
        setProfileData(prev => ({
          ...prev,
          metadata: [{ background_references: references }]
        }));
        setHasUnsavedChanges(true); // Mark as having unsaved changes
        console.log('[ResultsDisplay] Successfully updated references locally');
      } else {
        throw new Error(responseData.error || 'Failed to update references');
      }
    } catch (error) {
      console.error('Error updating references:', error);
      throw error;
    }
  };

  // Get current references
  const currentReferences = profileData.metadata
    ?.filter(meta => meta.background_references)
    ?.flatMap(meta => meta.background_references) || [];

  return (    
    <motion.div
      className="h-full flex flex-col space-y-4 overflow-hidden"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      {/* Executive Profile Summary */}
      <Card variant="compact" className="shadow border border-slate-200 flex-shrink-0">
        <div className="flex justify-between items-start mb-3">
          <h3 className="text-xl font-semibold text-gray-800 flex items-center">
            <span className="bg-primary/10 p-2 rounded-full mr-2">
              <UserIcon className="w-5 h-5" />
            </span>
            Executive Profile Summary
            {isStreaming && !profileData.aggregated_profile && (
              <div className="ml-2 w-4 h-4 border-2 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
            )}
          </h3>
          <div className="flex items-center gap-2">
            {profileData.aggregated_profile && <CopyButton text={profileData.aggregated_profile} />}
            <SaveButton 
              saving={saving}
              saveSuccess={saveSuccess}
              isStreaming={isStreaming}
              onClick={handleSaveProfile}
              hasUnsavedChanges={hasUnsavedChanges}
            />
          </div>
        </div>        
        
        {/* Executive Profile Content - Now Editable */}
        <div className="max-h-[600px] overflow-y-auto custom-scrollbar bg-white rounded-lg border border-gray-100">
          <div className="p-4">
            <EditableSection
              title="Executive Summary"
              content={profileData.aggregated_profile}
              onSave={(content) => handleUpdateSection('aggregated_profile', content)}
              isLoading={isStreaming && !profileData.aggregated_profile}
              placeholder="Enter executive summary..."
            />
          </div>
        </div>
      </Card>        

      {/* Streaming Insights Section - Now Editable */}
      <div className="flex-shrink-0">
        <Accordion>
          <AccordionItem value="insights">
            <AccordionTrigger>
              <div className="flex items-center">
                <span className="bg-primary/10 p-1 rounded-full mr-2">
                  <DocumentTextIcon className="w-5 h-5" />
                </span>
                <h3 className="text-lg font-semibold text-gray-800">Detailed Insights</h3>
                {isStreaming && <div className="ml-2 w-4 h-4 border-2 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>}
              </div>
            </AccordionTrigger>
            <AccordionContent>
              <div className="flex flex-col gap-4 mt-2">
                <EditableSection
                  title="Professional Background"
                  content={profileData.background_info}
                  onSave={(content) => handleUpdateSection('background_info', content)}
                  isLoading={isStreaming}
                  icon="🎓"
                  placeholder="Enter professional background information..."
                />
                
                <EditableSection
                  title="Leadership Profile"
                  content={profileData.leadership_info}
                  onSave={(content) => handleUpdateSection('leadership_info', content)}
                  isLoading={isStreaming}
                  icon="👑"
                  placeholder="Enter leadership information..."
                />
                
                <EditableSection
                  title="Market Reputation"
                  content={profileData.reputation_info}
                  onSave={(content) => handleUpdateSection('reputation_info', content)}
                  isLoading={isStreaming}
                  icon="⭐"
                  placeholder="Enter reputation information..."
                />
                
                <EditableSection
                  title="Strategic Approach"
                  content={profileData.strategy_info}
                  onSave={(content) => handleUpdateSection('strategy_info', content)}
                  isLoading={isStreaming}
                  icon="🎯"
                  placeholder="Enter strategic approach information..."
                />
              </div>
            </AccordionContent>
          </AccordionItem>

          {/* References Section - Now Manageable */}
          <AccordionItem value="references">
            <AccordionTrigger>
              <div className="flex items-center">
                <span className="bg-primary/10 p-1 rounded-full mr-2">
                  <BookOpenIcon className="w-5 h-5" />
                </span>
                <h3 className="text-lg font-semibold text-gray-800">References</h3>
              </div>
            </AccordionTrigger>
            <AccordionContent>
              <div className="bg-white rounded-lg mt-2">
                <ReferenceManager
                  references={currentReferences}
                  onSave={handleUpdateReferences}
                />
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </div>
    </motion.div>
  );
};

export default ResultsDisplay;