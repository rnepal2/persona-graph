import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Card from './ui/Card';
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from './ui/Accordion';
import { 
  XMarkIcon, 
  ArrowPathIcon, 
  DocumentIcon, 
  DocumentTextIcon,
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
      // Skip empty profiles instead of showing them
      console.warn('Skipping profile with empty name:', profile);
      return acc;
    }
    
    if (!acc[key]) {
      acc[key] = [];
    }
    acc[key].push(profile);
    return acc;
  }, {});

  // Count valid profiles (those that will be displayed)
  const validProfileCount = Object.values(groupedProfiles).reduce((total, versions) => total + versions.length, 0);

  // Initialize selected versions when profiles are loaded
  useEffect(() => {
    if (profiles.length > 0) {
      const initialSelectedVersions = {};
      Object.entries(groupedProfiles).forEach(([name, profileVersions]) => {
        const latestProfile = getLatestProfile(profileVersions);
        if (latestProfile) {
          initialSelectedVersions[name] = latestProfile.id;
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

  // Handle profile click
  const handleProfileClick = async (profile) => {
    console.log('Profile clicked:', profile);
    
    if (!profile || !profile.id) {
      console.error('Invalid profile object:', profile);
      return;
    }
    
    // If we have a selected version for this name, use that instead of the profile.id
    const versionId = selectedVersions[profile.name] || profile.id;
    console.log('Using version ID:', versionId);
    
    setSelectedProfile(profile);
    
    // Fetch and display the full profile data
    try {
      const response = await fetch(`http://localhost:5000/api/profile/${versionId}`);
      if (response.ok) {
        const data = await response.json();
        console.log('Full profile data:', data);
        
        if (data.success && data.profile) {
          const fullProfile = data.profile;
          
          // Convert database profile to ResultsDisplay format
          const resultFormat = {
            basic_info: {
              name: fullProfile.name || '',
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
                
                // Ensure the references are in the expected format for ResultsDisplay
                // ResultsDisplay expects: metadata.filter(meta => meta.background_references).flatMap(meta => meta.background_references)
                if (Array.isArray(references) && references.length > 0) {
                  // If references are already in the right format (array of reference objects)
                  if (references[0] && (references[0].title || references[0].link)) {
                    return [{ background_references: references }];
                  }
                  // If references are already wrapped
                  return references;
                }
                
                return [];
              } catch (e) {
                console.warn('Error parsing references_data:', e);
                return [];
              }
            })()
          };
          
          console.log('Converted result format:', resultFormat);
          onProfileSelect(resultFormat);
        }
      } else {
        console.error('Failed to fetch profile:', response.status);
      }
    } catch (err) {
      console.error('Error fetching full profile:', err);
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
    // Update the selected version for this profile name
    setSelectedVersions(prev => ({
      ...prev,
      [profileName]: versionId
    }));
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
        if (selectedProfile?.id === profileId) {
          setSelectedProfile(null);
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
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ width: 0, opacity: 0 }}
          animate={{ width: 320, opacity: 1 }}
          exit={{ width: 0, opacity: 0 }}
          transition={{ duration: 0.3, ease: "easeInOut" }}
          className="fixed left-0 top-0 h-full bg-gradient-to-b from-slate-50 to-white shadow-2xl z-50 overflow-hidden border-r border-gray-200"
        >
          <div className="h-full flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-blue-100 to-indigo-100">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <DocumentTextIcon className="w-4 h-4 text-blue-600" />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-gray-800">
                      Profile Library
                    </h2>
                    <p className="text-xs text-gray-600">
                      Your saved executive profiles
                    </p>
                  </div>
                </div>                <button
                  onClick={onToggle}
                  className="p-2 rounded-full hover:bg-gray-200 transition-colors group"
                  title="Close sidebar"
                >
                  <ChevronDoubleLeftIcon className="w-4 h-4 text-gray-600 group-hover:text-gray-800" />
                </button>
              </div>
              
              {/* Actions */}
              <div className="flex items-center justify-between">                <button
                  onClick={fetchProfiles}
                  disabled={loading}
                  className="flex items-center space-x-2 px-3 py-1.5 bg-white border border-gray-200 rounded-md hover:bg-gray-50 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Refresh profiles"
                >
                  <ArrowPathIcon
                    className={`w-3 h-3 text-gray-600 ${loading ? 'animate-spin' : ''}`} 
                  />
                  <span className="text-xs font-medium text-gray-700">
                    {loading ? 'Refreshing...' : 'Refresh'}
                  </span>
                </button>                  
                <div className="flex items-center space-x-2 text-xs text-gray-500">
                  <DocumentTextIcon className="w-3 h-3" />
                  <span>{validProfileCount} profile{validProfileCount !== 1 ? 's' : ''}</span>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4">
              <div className="space-y-2 max-h-[calc(100vh-280px)] overflow-y-auto custom-scrollbar">
                {loading && (
                  <div className="flex flex-col items-center justify-center py-12">
                    <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mb-4"></div>
                    <p className="text-sm text-gray-600">Loading your profiles...</p>
                  </div>
                )}

                {error && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">                    <div className="flex items-center space-x-2">
                      <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />
                      <p className="text-sm text-red-700 font-medium">Error</p>
                    </div>
                    <p className="text-sm text-red-600 mt-1">{error}</p>
                  </div>
                )}

                {!loading && !error && validProfileCount === 0 && (
                  <div className="text-center py-12">                    <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <DocumentIcon className="w-8 h-8 text-gray-400" />
                    </div>
                    <h3 className="text-lg font-semibold text-gray-800 mb-2">No profiles yet</h3>
                    <p className="text-sm text-gray-600 mb-4 max-w-xs mx-auto leading-relaxed">
                      Generate and save executive profiles to see them appear here for quick access.
                    </p>                    <div className="flex items-center justify-center space-x-2 text-xs text-gray-500">
                      <InformationCircleIcon className="w-4 h-4" />
                      <span>Click "Save Profile" after generating a profile</span>
                    </div>
                  </div>
                )}

                {/* Profile Accordions */}
                {Object.entries(groupedProfiles).map(([name, profileVersions]) => (
                  <div key={name} className="border border-gray-200 rounded-lg bg-white shadow-sm hover:shadow-md transition-shadow">
                    <Accordion variant="compact">
                      <AccordionItem value={name}>
                        <AccordionTrigger>
                          <div className="flex items-center space-x-3 flex-1 min-w-0">
                            {/* Avatar */}
                            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center flex-shrink-0">
                              <span className="text-white font-semibold text-xs">
                                {name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
                              </span>
                            </div>
                            
                            {/* Profile Info */}
                            <div className="flex-1 min-w-0 text-left">
                              <h4 className="font-semibold text-gray-900 truncate text-sm">
                                {name}
                              </h4>
                              {getLatestProfile(profileVersions)?.company && (
                                <p className="text-xs text-gray-500 truncate">
                                  {getLatestProfile(profileVersions).company}
                                </p>
                              )}
                            </div>
                            
                            {/* Version Badge */}
                            {profileVersions.length > 1 && (
                              <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded-full font-medium flex-shrink-0">
                                {profileVersions.length} versions
                              </span>
                            )}
                          </div>
                        </AccordionTrigger>
                        
                        <AccordionContent>
                          <div className="space-y-3">
                            {/* Profile Details */}
                            <div className="space-y-2">
                              {getLatestProfile(profileVersions)?.title && (                                <div className="flex items-start space-x-2">
                                  <BriefcaseIcon className="w-3 h-3 text-gray-400 mt-0.5 flex-shrink-0" />
                                  <p className="text-xs text-gray-600">
                                    {getLatestProfile(profileVersions).title}
                                  </p>
                                </div>
                              )}
                                <div className="flex items-start space-x-2">
                                <ClockIcon className="w-3 h-3 text-gray-400 mt-0.5 flex-shrink-0" />
                                <p className="text-xs text-gray-500">
                                  Updated {new Date(getLatestProfile(profileVersions)?.updated_at).toLocaleDateString()}
                                </p>
                              </div>
                            </div>
                            
                            {/* Version Selector Dropdown */}
                            {profileVersions.length > 1 && (
                              <div className="pt-2">
                                <label className="block text-xs font-medium text-gray-700 mb-1">
                                  Version:
                                </label>
                                <select
                                  className="w-full border border-gray-200 rounded-md text-xs py-1.5 px-2 pr-8 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                                  value={selectedVersions[name] || getLatestProfile(profileVersions).id}
                                  onChange={(e) => handleVersionSelect(name, parseInt(e.target.value))}
                                >
                                  {profileVersions.map(v => (
                                    <option key={v.id} value={v.id}>
                                      Version {v.version} {v.is_latest ? '(Latest)' : ''} - {new Date(v.updated_at).toLocaleDateString()}
                                    </option>
                                  ))}
                                </select>
                              </div>
                            )}
                            
                            {/* Action Buttons */}
                            <div className="flex items-center space-x-2 pt-2">
                              <button
                                onClick={() => handleProfileClick(getLatestProfile(profileVersions))}
                                className="flex-1 px-3 py-1.5 bg-blue-600 text-white text-xs rounded-md hover:bg-blue-700 transition-colors"
                              >
                                Load Profile
                              </button>
                              
                              <button
                                onClick={(e) => handleDeleteProfile(getLatestProfile(profileVersions), e)}
                                disabled={deleting === (selectedVersions[name] || getLatestProfile(profileVersions)?.id)}
                                className="p-1.5 rounded-md hover:bg-red-100 transition-colors group disabled:opacity-50 disabled:cursor-not-allowed"
                                title="Delete profile version"
                              >                                {deleting === (selectedVersions[name] || getLatestProfile(profileVersions)?.id) ? (
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
            
            {/* User Card at Bottom */}
            <div className="p-4 border-t border-gray-200 bg-gradient-to-r from-slate-50 to-gray-50">
              <div className="flex items-center space-x-3">                <div className="w-8 h-8 bg-gradient-to-br from-gray-600 to-gray-800 rounded-full flex items-center justify-center">
                  <UserIcon className="w-4 h-4 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900">rnepal</p>
                  <p className="text-xs text-gray-500">Profile Manager</p>
                </div>                <div className="text-xs text-gray-400">
                  <UserCircleIcon className="w-5 h-5" />
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default ProfileSidebar;
