import { useState } from 'react';

const CACHE_EXPIRY = 24 * 60 * 60 * 1000; // 24 hours in milliseconds

const generateCacheKey = (formData) => {
  // Create a stable key from form data
  const relevantData = {
    name: formData.name.trim().toLowerCase(),
    title: formData.title.trim().toLowerCase(),
    company: formData.company.trim().toLowerCase(),
    summary: formData.summary.trim().toLowerCase(),
    linkedin: formData.linkedin.trim().toLowerCase(),
    llm: formData.llm,
    searchEngine: formData.searchEngine,
  };
  return JSON.stringify(relevantData);
};

const getCachedResult = (cacheKey) => {
  try {
    const cached = localStorage.getItem(cacheKey);
    if (cached) {
      const { data, timestamp } = JSON.parse(cached);
      if (Date.now() - timestamp < CACHE_EXPIRY) {
        return data;
      }
      // Remove expired cache entry
      localStorage.removeItem(cacheKey);
    }
  } catch (error) {
    console.error('Cache retrieval error:', error);
  }
  return null;
};

const setCachedResult = (cacheKey, data) => {
  try {
    const cacheData = {
      data,
      timestamp: Date.now()
    };
    localStorage.setItem(cacheKey, JSON.stringify(cacheData));
  } catch (error) {
    console.error('Cache storage error:', error);
  }
};

export const useProfileCache = () => {
  const [isCacheHit, setIsCacheHit] = useState(false);

  const checkCache = (formData) => {
    const cacheKey = generateCacheKey(formData);
    const cachedResult = getCachedResult(cacheKey);
    setIsCacheHit(!!cachedResult);
    return cachedResult;
  };

  const updateCache = (formData, result) => {
    const cacheKey = generateCacheKey(formData);
    setCachedResult(cacheKey, result);
  };

  return {
    checkCache,
    updateCache,
    isCacheHit
  };
};
