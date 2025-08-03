import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  List,
  ListItem,
  Avatar,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import { Send as SendIcon, Person as PersonIcon, SmartToy as BotIcon } from '@mui/icons-material';
import { ApiService } from '../services/api';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isLoading?: boolean;
}

interface ChatResponse {
  response: string;
  conversation_id: string;
}

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Load conversation history when component mounts
    loadConversationHistory();
  }, []);

  const loadConversationHistory = async () => {
    try {
      const history = await ApiService.getChatHistory();
      if (history.messages && history.messages.length > 0) {
        setMessages(history.messages.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        })));
        setConversationId(history.conversation_id);
      } else {
        // Start with a welcome message
        const welcomeMessage: ChatMessage = {
          id: 'welcome',
          role: 'assistant',
          content: `Hello! I'm your IMDb ratings assistant. I can help you analyze your movie preferences, find specific ratings, get recommendations, and answer questions about your viewing habits. 

What would you like to know about your movie ratings?`,
          timestamp: new Date(),
        };
        setMessages([welcomeMessage]);
      }
    } catch (error) {
      console.error('Error loading conversation history:', error);
      // Start with welcome message if loading fails
      const welcomeMessage: ChatMessage = {
        id: 'welcome',
        role: 'assistant',
        content: `Hello! I'm your IMDb ratings assistant. I can help you analyze your movie preferences, find specific ratings, get recommendations, and answer questions about your viewing habits. 

What would you like to know about your movie ratings?`,
        timestamp: new Date(),
      };
      setMessages([welcomeMessage]);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    const loadingMessage: ChatMessage = {
      id: `loading-${Date.now()}`,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isLoading: true,
    };

    setMessages(prev => [...prev, userMessage, loadingMessage]);
    setInputValue('');
    setIsLoading(true);
    setError(null);

    try {
      const response: ChatResponse = await ApiService.sendChatMessage({
        message: userMessage.content,
        conversation_id: conversationId,
      });

      setConversationId(response.conversation_id);

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
      };

      setMessages(prev => prev.filter(msg => !msg.isLoading).concat(assistantMessage));
    } catch (error) {
      console.error('Error sending message:', error);
      setError('Failed to send message. Please try again.');
      setMessages(prev => prev.filter(msg => !msg.isLoading));
    } finally {
      setIsLoading(false);
    }
  };

  const formatMessageContent = (content: string) => {
    // Basic markdown-like formatting for better readability
    return content
      .split('\n')
      .map((line, index) => (
        <Typography key={index} variant="body2" sx={{ mb: line.trim() === '' ? 1 : 0 }}>
          {line || '\u00A0'}
        </Typography>
      ));
  };

  return (
    <Box sx={{ height: '80vh', display: 'flex', flexDirection: 'column' }}>
      <Typography variant="h4" sx={{ mb: 3, textAlign: 'center' }}>
        Chat with Your Movie Assistant
      </Typography>

      <Paper 
        elevation={2} 
        sx={{ 
          flex: 1, 
          display: 'flex', 
          flexDirection: 'column',
          overflow: 'hidden'
        }}
      >
        {/* Messages Area */}
        <Box 
          sx={{ 
            flex: 1, 
            overflow: 'auto', 
            p: 2,
            backgroundColor: '#f5f5f5'
          }}
        >
          <List sx={{ py: 0 }}>
            {messages.map((message) => (
              <ListItem
                key={message.id}
                sx={{
                  display: 'flex',
                  justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
                  px: 0,
                  py: 1,
                }}
              >
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: message.role === 'user' ? 'row-reverse' : 'row',
                    alignItems: 'flex-start',
                    maxWidth: '80%',
                    gap: 1,
                  }}
                >
                  <Avatar
                    sx={{
                      bgcolor: message.role === 'user' ? 'primary.main' : 'secondary.main',
                      width: 32,
                      height: 32,
                    }}
                  >
                    {message.role === 'user' ? <PersonIcon /> : <BotIcon />}
                  </Avatar>
                  
                  <Paper
                    elevation={1}
                    sx={{
                      p: 2,
                      bgcolor: message.role === 'user' ? 'primary.light' : 'white',
                      color: 'black',
                      borderRadius: 2,
                      position: 'relative',
                    }}
                  >
                    {message.isLoading ? (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <CircularProgress size={16} />
                        <Typography variant="body2">Thinking...</Typography>
                      </Box>
                    ) : (
                      <>
                        {formatMessageContent(message.content)}
                        <Chip
                          label={message.timestamp.toLocaleTimeString()}
                          size="small"
                          variant="outlined"
                          sx={{ 
                            mt: 1, 
                            height: 20, 
                            fontSize: '0.7rem',
                            opacity: 0.7 
                          }}
                        />
                      </>
                    )}
                  </Paper>
                </Box>
              </ListItem>
            ))}
          </List>
          <div ref={messagesEndRef} />
        </Box>

        {/* Error Display */}
        {error && (
          <Alert severity="error" sx={{ m: 2, mt: 0 }}>
            {error}
          </Alert>
        )}

        {/* Input Area */}
        <Box
          component="form"
          onSubmit={handleSendMessage}
          sx={{
            p: 2,
            borderTop: 1,
            borderColor: 'divider',
            backgroundColor: 'white',
          }}
        >
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              multiline
              maxRows={4}
              placeholder="Ask me about your movie ratings, preferences, or get recommendations..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              disabled={isLoading}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage(e);
                }
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 3,
                  color: 'black',
                },
                input: {
                  color: 'black',
                },
                textarea: {
                  color: 'black',
                }
              }}
            />
            <Button
              type="submit"
              variant="contained"
              disabled={!inputValue.trim() || isLoading}
              sx={{
                minWidth: 56,
                height: 56,
                borderRadius: 3,
              }}
            >
              {isLoading ? <CircularProgress size={24} /> : <SendIcon />}
            </Button>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default ChatPage;