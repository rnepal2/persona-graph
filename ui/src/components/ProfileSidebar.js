import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Card from './ui/Card';
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from './ui/Accordion';
import { 
  XMarkIcon, 
  ArrowPathIcon, 
  DocumentIcon, 
  DocumentTextIcon,
  InboxStackIcon,
  ExclamationTriangleIcon,
  BriefcaseIcon,
  ClockIcon,
  TrashIcon,
  UserIcon,
  UserCircleIcon,
  InformationCircleIcon,
  ChevronDoubleLeftIcon,
} from '@heroicons/react/24/outline';

const ProfileSidebar = ({ isOpen, onToggle, onProfileSelect }) => {  
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedProfile, setSelectedProfile] = useState(null);
  const [selectedVersions, setSelectedVersions] = useState({}); // Track selected version for each profile
  const [showVersions, setShowVersions] = useState({}); // Track which profiles are showing versions
  const [deleting, setDeleting] = useState(null); // Track which profile is being deleted
  const [loadedProfileId, setLoadedProfileId] = useState(null); // Track which profile is currently loaded
  
  // Fetch saved profiles
  const fetchProfiles = async () => {
    setLoading(true);
    setError(null);
    try {
      const url = 'http://localhost:5000/api/profiles';
      console.log('Fetching profiles from:', url);
      const response = await fetch(url);
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
      }
        
      const data = await response.json();
      console.log('Profiles data:', data);
      console.log('Individual profiles:', data.profiles);
      if (data.profiles && data.profiles.length > 0) {
        console.log('First profile structure:', data.profiles[0]);
      }
      setProfiles(data.profiles || []);
    } catch (err) {
      console.error('Error fetching profiles:', err);
      setError(`Failed to load saved profiles: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };
  
  // Fetch profile versions and set up version selection
  const fetchProfileVersions = async (profileId) => {
    try {
      const response = await fetch(`http://localhost:5000/api/profile/${profileId}/versions`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.versions || [];
    } catch (err) {
      console.error('Error fetching profile versions:', err);
      return [];
    }
  };

  // Group profiles by name with error handling
  const groupedProfiles = profiles.reduce((acc, profile) => {
    // Add safety checks for profile data
    if (!profile || typeof profile !== 'object') {
      console.warn('Invalid profile object:', profile);
      return acc;
    }
    
    // Use profile name or fallback for empty names
    let key = profile.name;
    if (!key || typeof key !== 'string' || key.trim() === '') {
      // Instead of skipping, use a fallback name based on other info
      key = profile.title || profile.company || `Profile #${profile.id}` || 'Unnamed Profile';
      console.log('Using fallback name for profile:', profile.id, 'Name:', key);
    }
    
    // Group by name AND linkedin_url to ensure we group the right profiles
    const groupKey = `${key}_${profile.linkedin_url || 'no-linkedin'}`;
    
    if (!acc[groupKey]) {
      acc[groupKey] = {
        name: key,
        profiles: []
      };
    }
    acc[groupKey].profiles.push(profile);
    return acc;
  }, {});

  // Sort profiles within each group by version (latest first)
  Object.values(groupedProfiles).forEach(group => {
    group.profiles.sort((a, b) => {
      // Sort by version number descending (latest first)
      return (b.version || 0) - (a.version || 0);
    });
  });

  // Count valid profiles (those that will be displayed)
  const validProfileCount = Object.values(groupedProfiles).reduce((total, group) => total + group.profiles.length, 0);

  // Initialize selected versions when profiles are loaded
  useEffect(() => {
    if (profiles.length > 0) {
      const initialSelectedVersions = {};
      Object.entries(groupedProfiles).forEach(([groupKey, group]) => {
        const latestProfile = getLatestProfile(group.profiles);
        if (latestProfile) {
          initialSelectedVersions[group.name] = latestProfile.id;
        }
      });
      setSelectedVersions(initialSelectedVersions);
    }
  }, [profiles]);
  
  // Load profiles on component mount
  useEffect(() => {
    if (isOpen) {
      fetchProfiles();
    }
  }, [isOpen]);

  // Handle profile click - now works as a toggle
  const handleProfileClick = async (profile) => {
    console.log('=== Profile Click Handler ===');
    console.log('Profile clicked:', profile);
    
    if (!profile || !profile.id) {
      console.error('Invalid profile object:', profile);
      return;
    }
    
    // Get the version ID to use - ensure it's a number
    const versionId = Number(selectedVersions[profile.name] || profile.id);
    const currentLoadedId = Number(loadedProfileId);
    
    console.log('Version ID to use:', versionId);
    console.log('Currently loaded ID:', currentLoadedId);
    console.log('Are they equal?:', currentLoadedId === versionId);
    console.log('Is loadedProfileId null?:', loadedProfileId === null);
    
    // Check if this profile is already loaded - if so, unload it
    if (currentLoadedId === versionId && loadedProfileId !== null) {
      console.log('UNLOADING: Profile is currently loaded, unloading it');
      setSelectedProfile(null);
      setLoadedProfileId(null);
      onProfileSelect(null); // Clear the profile from the main UI
      return;
    }
    
    console.log('LOADING: Loading new profile');
    setSelectedProfile(profile);
    setLoadedProfileId(versionId);
    
    // Fetch and display the full profile data
    try {
      const response = await fetch(`http://localhost:5000/api/profile/${versionId}`);
      if (response.ok) {
        const data = await response.json();
        console.log('Full profile data received:', data.success);
        
        if (data.success && data.profile) {
          const fullProfile = data.profile;
          
          // Convert database profile to ResultsDisplay format
          const resultFormat = {
            basic_info: {
              name: fullProfile.name || profile.name || 'Unknown',
              company: fullProfile.company || '',
              title: fullProfile.title || '',
              linkedin_url: fullProfile.linkedin_url || ''
            },
            aggregated_profile: fullProfile.executive_profile || '',
            background_info: fullProfile.professional_background || '',
            leadership_info: fullProfile.leadership_summary || '',
            reputation_info: fullProfile.reputation_summary || '',
            strategy_info: fullProfile.strategy_summary || '',
            metadata: (() => {
              try {
                let references = [];
                if (fullProfile.references_data) {
                  if (typeof fullProfile.references_data === 'string') {
                    references = JSON.parse(fullProfile.references_data);
                  } else if (Array.isArray(fullProfile.references_data)) {
                    references = fullProfile.references_data;
                  }
                }
                
                if (Array.isArray(references) && references.length > 0) {
                  if (references[0] && (references[0].title || references[0].link)) {
                    return [{ background_references: references }];
                  }
                  return references;
                }
                
                return [];
              } catch (e) {
                console.warn('Error parsing references_data:', e);
                return [];
              }
            })()
          };
          
          console.log('Calling onProfileSelect with converted data');
          onProfileSelect(resultFormat);
        }
      } else {
        console.error('Failed to fetch profile:', response.status);
        setLoadedProfileId(null);
        setSelectedProfile(null);
      }
    } catch (err) {
      console.error('Error fetching full profile:', err);
      setLoadedProfileId(null);
      setSelectedProfile(null);
    }
  };

  // Toggle versions display
  const toggleVersions = async (profileId, profileName) => {
    const key = `${profileId}_${profileName}`;
    
    if (showVersions[key]) {
      setShowVersions(prev => ({ ...prev, [key]: null }));
    } else {
      const versions = await fetchProfileVersions(profileId);
      setShowVersions(prev => ({ ...prev, [key]: versions }));
    }
  };

  // Handle version selection
  const handleVersionSelect = (profileName, versionId) => {
    console.log('Version selected:', profileName, versionId, 'Current loaded:', loadedProfileId);
    
    // Update the selected version for this profile name
    setSelectedVersions(prev => ({
      ...prev,
      [profileName]: Number(versionId) // Ensure it's stored as a number
    }));
    
    // If this profile is currently loaded, we need to clear the loaded state
    // so that the new version can be loaded when clicked
    const currentLoaded = Number(loadedProfileId);
    const newVersion = Number(versionId);
    const oldVersion = Number(selectedVersions[profileName]);
    
    if (loadedProfileId && (currentLoaded === oldVersion || currentLoaded === newVersion)) {
      console.log('Clearing loaded state due to version change');
      setLoadedProfileId(null);
      setSelectedProfile(null);
      onProfileSelect(null);
    }
  };

  // Handle profile deletion
  const handleDeleteProfile = async (profile, event) => {
    event.stopPropagation(); // Prevent triggering the profile click
    
    // Only delete the selected version, not all versions
    const profileId = selectedVersions[profile.name] || profile.id;
    
    const confirmDelete = window.confirm(
      `Are you sure you want to delete this version of "${profile.name}"?\n\nThis action cannot be undone.`
    );
    
    if (!confirmDelete) return;
    
    setDeleting(profileId);
    
    try {
      const response = await fetch(`http://localhost:5000/api/profile/${profileId}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        // Refresh profiles to update the list after deletion
        fetchProfiles();
        
        // Clear selected profile if it was the deleted one
        if (selectedProfile?.id === profileId || loadedProfileId === profileId) {
          setSelectedProfile(null);
          setLoadedProfileId(null);
          onProfileSelect(null);
        }
        
        // Show success message (optional)
        console.log('Profile version deleted successfully');
      } else {
        const errorData = await response.json();
        alert(`Failed to delete profile: ${errorData.error || 'Unknown error'}`);
      }
    } catch (err) {
      console.error('Error deleting profile:', err);
      alert('Failed to delete profile. Please try again.');
    } finally {
      setDeleting(null);
    }
  };

  // Helper function to get the latest profile or fallback to first profile
  const getLatestProfile = (profileVersions) => {
    if (!profileVersions || profileVersions.length === 0) {
      console.warn('getLatestProfile: No profile versions provided');
      return null;
    }
    
    // Try to find the latest profile
    const latestProfile = profileVersions.find(p => p && (p.is_latest === true || p.is_latest === 1));
    
    // If no latest profile found, use the first one that has an id
    const fallbackProfile = profileVersions.find(p => p && p.id);
    
    const result = latestProfile || fallbackProfile || profileVersions[0];
    
    if (!result || typeof result.id === 'undefined') {
      console.error('getLatestProfile: Unable to find a valid profile with id:', {
        profileVersions,
        latestProfile,
        fallbackProfile,
        result
      });
      return null;
    }
    
    return result;
  };

  return (
    <motion.div
      initial={{ width: isOpen ? 320 : 72 }}
      animate={{ width: isOpen ? 320 : 72 }}
      transition={{ duration: 0.3, ease: "easeInOut" }}
      className="fixed left-0 top-0 h-full bg-gradient-to-b from-slate-50 to-white shadow-2xl z-50 overflow-hidden border-r border-gray-200"
    >
      <div className="h-full flex flex-col">
        {/* Header */}
        <div className={`p-4 border-b border-gray-200 bg-gradient-to-r from-blue-100 to-indigo-100 ${!isOpen ? 'px-2' : ''}`}>
          {isOpen ? (
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <InboxStackIcon className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-gray-800">Profile Library</h2>
                  <p className="text-xs text-gray-600">Your saved executive profiles</p>
                </div>
              </div>
              <button
                onClick={onToggle}
                className="p-2 rounded-full hover:bg-gray-200 transition-colors group"
                title="Collapse sidebar"
              >
                <ChevronDoubleLeftIcon className="w-4 h-4 text-gray-600 group-hover:text-gray-800" />
              </button>
            </div>
          ) : (
            <div className="flex flex-col items-center space-y-2">
              <motion.button
                onClick={onToggle}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center text-white hover:bg-blue-700 transition-colors shadow-md"
                title="Expand profile library"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </motion.button>
              <div className="text-center">
                <p className="text-xs font-bold text-gray-600 writing-mode-vertical transform -rotate-90" style={{ writingMode: 'vertical-rl' }}>
                  Library
                </p>
              </div>
            </div>
          )}
          
          {/* Actions - only show in expanded mode */}
          {isOpen && (
            <div className="flex items-center justify-between">
              <button
                onClick={fetchProfiles}
                disabled={loading}
                className="flex items-center space-x-2 px-3 py-1.5 bg-white border border-gray-200 rounded-md hover:bg-gray-50 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                title="Refresh profiles"
              >
                <ArrowPathIcon className={`w-3 h-3 text-gray-600 ${loading ? 'animate-spin' : ''}`} />
                <span className="text-xs font-medium text-gray-700">
                  {loading ? 'Refreshing...' : 'Refresh'}
                </span>
              </button>
              <div className="flex items-center space-x-1 text-xs text-gray-500">
                <DocumentTextIcon className="w-4 h-4" />
                <span>{validProfileCount} profile{validProfileCount !== 1 ? 's' : ''}</span>
              </div>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {isOpen ? (
            // Expanded view - existing content
            <div className="p-4">
              <div className="space-y-2 max-h-[calc(100vh-280px)] overflow-y-auto custom-scrollbar">
                {loading && (
                  <div className="flex flex-col items-center justify-center py-12">
                    <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mb-4"></div>
                    <p className="text-sm text-gray-600">Loading your profiles...</p>
                  </div>
                )}

                {error && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex items-center space-x-2">
                      <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />
                      <p className="text-sm text-red-700 font-medium">Error</p>
                    </div>
                    <p className="text-sm text-red-600 mt-1">{error}</p>
                  </div>
                )}

                {!loading && !error && validProfileCount === 0 && (
                  <div className="text-center py-12">
                    <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <DocumentIcon className="w-8 h-8 text-gray-400" />
                    </div>
                    <h3 className="text-lg font-semibold text-gray-800 mb-2">No profiles yet</h3>
                    <p className="text-sm text-gray-600 mb-4 max-w-xs mx-auto leading-relaxed">
                      Generate and save executive profiles to see them appear here for quick access.
                    </p>
                    <div className="flex items-center justify-center space-x-2 text-xs text-gray-500">
                      <InformationCircleIcon className="w-4 h-4" />
                      <span>Click "Save Profile" after generating a profile</span>
                    </div>
                  </div>
                )}

                {/* Profile Accordions - updated to use new grouping structure */}
                {Object.entries(groupedProfiles).map(([groupKey, group]) => (
                  <div key={groupKey} className="border border-gray-200 rounded-lg bg-white shadow-sm hover:shadow-md transition-shadow">
                    <Accordion variant="compact">
                      <AccordionItem value={group.name}>
                        <AccordionTrigger>
                          <div className="flex items-center space-x-3 flex-1 min-w-0">
                            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center flex-shrink-0">
                              <span className="text-white font-semibold text-xs">
                                {group.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
                              </span>
                            </div>
                            <div className="flex-1 min-w-0 text-left">
                              <h4 className="font-semibold text-gray-900 truncate text-sm">{group.name}</h4>
                              {getLatestProfile(group.profiles)?.company && (
                                <p className="text-xs text-gray-500 truncate">
                                  {getLatestProfile(group.profiles).company}
                                </p>
                              )}
                            </div>
                            {group.profiles.length > 1 && (
                              <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded-full font-medium flex-shrink-0">
                                {group.profiles.length} versions
                              </span>
                            )}
                          </div>
                        </AccordionTrigger>
                        <AccordionContent>
                          <div className="space-y-3">
                            <div className="space-y-2">
                              {getLatestProfile(group.profiles)?.title && (
                                <div className="flex items-start space-x-2">
                                  <BriefcaseIcon className="w-3 h-3 text-gray-400 mt-0.5 flex-shrink-0" />
                                  <p className="text-xs text-gray-600">
                                    {getLatestProfile(group.profiles).title}
                                  </p>
                                </div>
                              )}
                              <div className="flex items-start space-x-2">
                                <ClockIcon className="w-3 h-3 text-gray-400 mt-0.5 flex-shrink-0" />
                                <p className="text-xs text-gray-500">
                                  Updated {new Date(getLatestProfile(group.profiles)?.updated_at).toLocaleDateString()}
                                </p>
                              </div>
                            </div>
                            
                            {/* Always show version dropdown if there are multiple versions */}
                            {group.profiles.length > 1 && (
                              <div className="pt-2">
                                <label className="block text-xs font-medium text-gray-700 mb-1">Version:</label>
                                <select
                                  className="w-full border border-gray-200 rounded-md text-xs py-1.5 px-2 pr-8 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                                  value={selectedVersions[group.name] || getLatestProfile(group.profiles).id}
                                  onChange={(e) => handleVersionSelect(group.name, parseInt(e.target.value))}
                                >
                                  {group.profiles.map(v => (
                                    <option key={v.id} value={v.id}>
                                      Version {v.version} {v.is_latest ? '(Latest)' : ''} - {new Date(v.updated_at).toLocaleDateString()}
                                    </option>
                                  ))}
                                </select>
                              </div>
                            )}
                            
                            <div className="flex items-center space-x-2 pt-2">
                              {(() => {
                                const currentVersionId = Number(selectedVersions[group.name] || getLatestProfile(group.profiles)?.id);
                                const isCurrentlyLoaded = Number(loadedProfileId) === currentVersionId && loadedProfileId !== null;
                                
                                return (
                                  <button
                                    onClick={() => handleProfileClick(getLatestProfile(group.profiles))}
                                    className={`flex-1 px-3 py-1.5 text-xs rounded-md transition-colors ${
                                      isCurrentlyLoaded
                                        ? 'bg-red-600 text-white hover:bg-red-700'
                                        : 'bg-blue-600 text-white hover:bg-blue-700'
                                    }`}
                                  >
                                    {isCurrentlyLoaded ? 'Unload Profile' : 'Load Profile'}
                                  </button>
                                );
                              })()}
                              
                              <button
                                onClick={(e) => handleDeleteProfile(getLatestProfile(group.profiles), e)}
                                disabled={deleting === (selectedVersions[group.name] || getLatestProfile(group.profiles)?.id)}
                                className="p-1.5 rounded-md hover:bg-red-100 transition-colors group disabled:opacity-50 disabled:cursor-not-allowed"
                                title="Delete profile version"
                              >
                                {deleting === (selectedVersions[group.name] || getLatestProfile(group.profiles)?.id) ? (
                                  <ArrowPathIcon className="w-4 h-4 text-red-500 animate-spin" />
                                ) : (
                                  <TrashIcon className="w-4 h-4 text-gray-400 group-hover:text-red-500 transition-colors" />
                                )}
                              </button>
                            </div>
                          </div>
                        </AccordionContent>
                      </AccordionItem>
                    </Accordion>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            // Compressed view - profile avatars only in a clean vertical stack
            <div className="p-1 space-y-2 overflow-hidden">
              {loading ? (
                <div className="flex justify-center py-4">
                  <div className="w-6 h-6 border-2 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
                </div>
              ) : error ? (
                <div className="flex justify-center">
                  <motion.div 
                    className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center"
                    whileHover={{ scale: 1.05 }}
                  >
                    <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />
                  </motion.div>
                </div>
              ) : validProfileCount === 0 ? (
                <div className="flex flex-col items-center py-6 space-y-2">
                  <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                    <DocumentIcon className="w-5 h-5 text-gray-400" />
                  </div>
                  <div className="w-8 h-0.5 bg-gray-200 rounded"></div>
                  <div className="mt-4">
                    <p className="text-xs text-gray-500 text-center writing-mode-vertical transform -rotate-90" style={{ writingMode: 'vertical-rl' }}>
                      No profiles
                    </p>
                  </div>
                </div>
              ) : (
                <>
                  {/* Quick refresh button */}
                  <motion.button
                    onClick={fetchProfiles}
                    disabled={loading}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="w-12 h-10 bg-white border border-gray-200 rounded-lg flex items-center justify-center hover:bg-gray-50 transition-colors shadow-sm disabled:opacity-50 mx-auto"
                    title="Refresh profiles"
                  >
                    <ArrowPathIcon className={`w-4 h-4 text-gray-600 ${loading ? 'animate-spin' : ''}`} />
                  </motion.button>

                  {/* Divider */}
                  <div className="w-8 h-0.5 bg-gray-200 rounded mx-auto"></div>

                  {/* Profile count indicator - fixed vertical text */}
                  <div className="text-center py-2 flex justify-center">
                    <p className="text-xs font-medium text-gray-600 writing-mode-vertical transform -rotate-90" style={{ writingMode: 'vertical-rl' }}>
                      {validProfileCount}
                    </p>
                  </div>

                  {/* Another divider */}
                  <div className="w-8 h-0.5 bg-gray-200 rounded mx-auto"></div>

                  {/* Compressed profile list - updated to use new grouping structure */}
                  <div className={`
                    space-y-3 py-2 overflow-hidden
                    ${validProfileCount > 6 ? 'max-h-[calc(100vh-300px)] overflow-y-auto' : ''}
                  `} style={{ scrollbarWidth: 'thin' }}>
                    {Object.entries(groupedProfiles).map(([groupKey, group]) => {
                      const latestProfile = getLatestProfile(group.profiles);
                      if (!latestProfile) return null;
                      
                      const currentVersionId = Number(selectedVersions[group.name] || latestProfile.id);
                      const isCurrentlyLoaded = Number(loadedProfileId) === currentVersionId && loadedProfileId !== null;
                      
                      return (
                        <motion.div
                          key={groupKey}
                          whileHover={{ scale: 1.08 }}
                          whileTap={{ scale: 0.95 }}
                          className="relative group flex justify-center"
                        >
                          <button
                            onClick={() => handleProfileClick(latestProfile)}
                            className={`
                              relative w-11 h-11 rounded-lg transition-all duration-200 shadow-sm hover:shadow-md
                              ${isCurrentlyLoaded 
                                ? 'ring-2 ring-red-300 shadow-lg' 
                                : 'hover:ring-2 hover:ring-blue-200'
                              }
                            `}
                            title={`${isCurrentlyLoaded ? 'Unload' : 'Load'} ${group.name}`}
                          >
                            {/* Avatar */}
                            <div className={`
                              w-full h-full rounded-lg flex items-center justify-center text-white font-semibold text-sm
                              ${isCurrentlyLoaded 
                                ? 'bg-gradient-to-br from-red-500 to-red-600' 
                                : 'bg-gradient-to-br from-blue-500 to-indigo-600'
                              }
                            `}>
                              {group.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
                            </div>
                            
                            {/* Status indicator - active profile */}
                            {isCurrentlyLoaded && (
                              <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full border-2 border-white shadow-sm"></div>
                            )}
                            
                            {/* Version count badge */}
                            {group.profiles.length > 1 && (
                              <div className="absolute -top-1 -left-1 w-4 h-4 bg-blue-500 rounded-full flex items-center justify-center border border-white shadow-sm">
                                <span className="text-xs font-bold text-white">{group.profiles.length}</span>
                              </div>
                            )}
                          </button>
                          
                          {/* Enhanced tooltip on hover - positioned outside sidebar */}
                          <div className="fixed left-20 top-1/2 transform -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-50">
                            <div className="bg-gray-900 text-white text-xs px-3 py-2 rounded-lg whitespace-nowrap shadow-lg">
                              <div className="font-medium">{group.name}</div>
                              {latestProfile.company && (
                                <div className="text-gray-300 text-xs">{latestProfile.company}</div>
                              )}
                              <div className="text-gray-400 text-xs mt-1">
                                {isCurrentlyLoaded ? 'Click to unload' : 'Click to load'}
                              </div>
                              {/* Tooltip arrow */}
                              <div className="absolute left-0 top-1/2 transform -translate-y-1/2 -translate-x-1 w-0 h-0 border-t-4 border-b-4 border-r-6 border-transparent border-r-gray-900"></div>
                            </div>
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                </>
              )}
            </div>
          )}
        </div>
        
        {/* User Card at Bottom - always show but adapt to width */}
        <div className={`border-t border-gray-200 bg-gradient-to-r from-slate-50 to-gray-50 ${isOpen ? 'p-4' : 'p-2'}`}>
          {isOpen ? (
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-gray-600 to-gray-800 rounded-full flex items-center justify-center">
                <UserIcon className="w-4 h-4 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900">rnepal</p>
                <p className="text-xs text-gray-500">Profile Manager</p>
              </div>
              <div className="text-xs text-gray-400">
                <UserCircleIcon className="w-5 h-5" />
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center">
              <div className="w-8 h-8 bg-gradient-to-br from-gray-600 to-gray-800 rounded-lg flex items-center justify-center mb-2 shadow-sm">
                <UserIcon className="w-4 h-4 text-white" />
              </div>
              <div className="w-6 h-0.5 bg-gray-300 rounded"></div>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default ProfileSidebar;