// src/adapters/language_adapters/web/NexusProvider.jsx
import React, { createContext, useContext, useEffect, useState, useRef } from 'react';

const NexusContext = createContext(null);

export const NexusProvider = ({ children, config }) => {
  const [state, setState] = useState({});
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const configRef = useRef(config || {});

  useEffect(() => {
    configRef.current = config || {};
  }, [config]);

  useEffect(() => {
    const gatewayUrl = configRef.current.gatewayUrl || 'ws://localhost:8765/ws';
    
    const connect = () => {
      wsRef.current = new WebSocket(gatewayUrl);

      wsRef.current.onopen = () => {
        console.log(`Nexus React client connected`);
        setConnected(true);
        
        // Register module
        const registration = {
          type: 'module_registration',
          module_name: configRef.current.moduleName || 'react_module',
          timestamp: new Date().toISOString(),
          language: 'react'
        };

        wsRef.current.send(JSON.stringify({
          type: 'module_registration',
          data: registration
        }));
      };

      wsRef.current.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleMessage(message);
      };

      wsRef.current.onclose = () => {
        console.log('Nexus React client disconnected');
        setConnected(false);
      };

      wsRef.current.onerror = (error) => {
        console.error('Nexus React client error:', error);
      };
    };

    connect();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const handleMessage = (message) => {
    switch (message.type) {
      case 'state_update':
        setState(prev => ({ ...prev, ...message.data }));
        break;
      default:
        console.log('Received message:', message);
    }
  };

  const sendMessage = (message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, message not sent:', message);
    }
  };

  const readState = async () => {
    return state;
  };

  const writeState = async (newState) => {
    const message = {
      type: 'state_update',
      data: newState,
      module: configRef.current.moduleName || 'react_module',
      timestamp: new Date().toISOString()
    };

    sendMessage(message);
    setState(prev => ({ ...prev, ...newState }));
  };

  const updateField = async (key, value) => {
    const newState = { [key]: value };
    await writeState(newState);
  };

  const getField = async (key) => {
    return state[key];
  };

  const incrementField = async (key, amount = 1) => {
    const currentValue = state[key] || 0;
    const currentNum = typeof currentValue === 'number' ? currentValue : 0;
    const newValue = currentNum + amount;
    
    await updateField(key, newValue);
    return newValue;
  };

  const callRemoteFunction = (funcName, args) => {
    return new Promise((resolve) => {
      const requestId = Math.random().toString(36).substring(2, 15);
      const callRequest = {
        type: 'rpc_call',
        request_id: requestId,
        function: funcName,
        args: args,
        caller: configRef.current.moduleName || 'react_module',
        timestamp: new Date().toISOString()
      };

      sendMessage(callRequest);
      
      // In a real implementation, we'd wait for the response
      resolve('response_pending');
    });
  };

  const registerFunction = (funcName, handler) => {
    const registration = {
      type: 'function_registration',
      function: funcName,
      module: configRef.current.moduleName || 'react_module',
      timestamp: new Date().toISOString()
    };

    sendMessage({
      type: 'function_registration',
      data: registration
    });
  };

  const value = {
    state,
    connected,
    readState,
    writeState,
    updateField,
    getField,
    incrementField,
    callRemoteFunction,
    registerFunction,
    sendMessage
  };

  return (
    <NexusContext.Provider value={value}>
      {children}
    </NexusContext.Provider>
  );
};

export const useNexus = () => {
  const context = useContext(NexusContext);
  if (!context) {
    throw new Error('useNexus must be used within a NexusProvider');
  }
  return context;
};

// Example usage component
export const NexusStateDisplay = ({ field }) => {
  const { state, connected } = useNexus();
  
  return (
    <div className="nexus-state-display">
      <div>Status: {connected ? 'Connected' : 'Disconnected'}</div>
      <div>Field "{field}": {JSON.stringify(state[field])}</div>
    </div>
  );
};