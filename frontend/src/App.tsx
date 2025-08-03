import React, { useState, useEffect, useCallback } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  Tabs,
  Tab,
  CircularProgress,
  Alert,
} from '@mui/material';
import { Movie as MovieIcon } from '@mui/icons-material';

import Dashboard from './pages/Dashboard';
import ScrapingPage from './pages/ScrapingPage';
import AnalysisPage from './pages/AnalysisPage';
import RatingsPage from './pages/RatingsPage';
import ChatPage from './pages/ChatPage';
import { ApiService } from './services/api';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel({ children, value, index }: TabPanelProps) {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function App() {
  const [tabValue, setTabValue] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasData, setHasData] = useState(false);
  const [lastDataCheck, setLastDataCheck] = useState<number>(0);

  useEffect(() => {
    checkDataStatus();
  }, []);

  const checkDataStatus = useCallback(async () => {
    try {
      setIsLoading(true);
      const stats = await ApiService.getRatingStats();
      const hasDataNow = stats.total_ratings > 0;
      setHasData(hasDataNow);
      setLastDataCheck(Date.now());
    } catch (err) {
      console.error('Error checking data status:', err);
      setError('Failed to connect to API');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Throttled version to prevent excessive API calls
  const throttledCheckDataStatus = useCallback(async () => {
    const now = Date.now();
    // Only check if it's been more than 5 seconds since last check
    if (now - lastDataCheck > 5000) {
      await checkDataStatus();
    }
  }, [lastDataCheck, checkDataStatus]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  if (isLoading) {
    return (
      <Box 
        display="flex" 
        justifyContent="center" 
        alignItems="center" 
        minHeight="100vh"
      >
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (error) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <MovieIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            IMDB Ratings Analyzer
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 3 }}>
        {!hasData && tabValue !== 1 && (
          <Alert severity="info" sx={{ mb: 3 }}>
            No rating data found. Please start by scraping your IMDB ratings.
          </Alert>
        )}

        <Tabs 
          value={tabValue} 
          onChange={handleTabChange} 
          centered
          sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}
        >
          <Tab label="Dashboard" disabled={!hasData} />
          <Tab label="Import Data" />
          <Tab label="Analysis" disabled={!hasData} />
          <Tab label="All Ratings" disabled={!hasData} />
          <Tab label="Chat" disabled={!hasData} />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <Dashboard onDataUpdate={throttledCheckDataStatus} />
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <ScrapingPage onDataUpdate={throttledCheckDataStatus} />
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <AnalysisPage />
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <RatingsPage />
        </TabPanel>

        <TabPanel value={tabValue} index={4}>
          <ChatPage />
        </TabPanel>
      </Container>
    </Box>
  );
}

export default App;