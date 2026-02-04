// src/adapters/language_adapters/web/nexus-client.js
class NexusClient {
  constructor(options = {}) {
    this.config = {
      kafkaBootstrapServers: options.kafkaBootstrapServers || 'localhost:9092',
      redisUrl: options.redisUrl || 'ws://localhost:6379',
      moduleName: options.moduleName || 'web_module',
      gatewayUrl: options.gatewayUrl || 'ws://localhost:8765/ws',
      ...options
    };

    this.state = {};
    this.callbacks = [];
    this.ws = null;
    this.connected = false;
    
    this.connect();
  }

  connect() {
    try {
      this.ws = new WebSocket(this.config.gatewayUrl);
      
      this.ws.onopen = () => {
        console.log(`Nexus client connected as ${this.config.moduleName}`);
        this.connected = true;
        this.registerModule();
      };

      this.ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        this.handleMessage(message);
      };

      this.ws.onclose = () => {
        console.log('Nexus client disconnected');
        this.connected = false;
      };

      this.ws.onerror = (error) => {
        console.error('Nexus client error:', error);
      };
    } catch (error) {
      console.error('Failed to connect to Nexus:', error);
    }
  }

  registerModule() {
    const registration = {
      type: 'module_registration',
      module_name: this.config.moduleName,
      timestamp: new Date().toISOString(),
      language: 'javascript'
    };

    this.sendMessage({
      type: 'module_registration',
      data: registration
    });
  }

  sendMessage(message) {
    if (this.connected && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, message not sent:', message);
    }
  }

  handleMessage(message) {
    switch (message.type) {
      case 'state_update':
        this.state = { ...this.state, ...message.data };
        this.notifyCallbacks(this.state);
        break;
      case 'rpc_response':
        // Handle RPC response
        break;
      case 'broadcast':
        // Handle broadcast message
        break;
      default:
        console.log('Received message:', message);
    }
  }

  async readState() {
    return new Promise((resolve) => {
      // In a real implementation, we'd make a request to the gateway
      // For now, return the cached state
      resolve(this.state);
    });
  }

  async writeState(newState) {
    const message = {
      type: 'state_update',
      data: newState,
      module: this.config.moduleName,
      timestamp: new Date().toISOString()
    };

    this.sendMessage(message);
    this.state = { ...this.state, ...newState };
    this.notifyCallbacks(this.state);
  }

  async updateField(key, value) {
    const newState = { [key]: value };
    await this.writeState(newState);
  }

  async getField(key) {
    const state = await this.readState();
    return state[key];
  }

  incrementField(key, amount = 1) {
    return new Promise(async (resolve) => {
      const currentValue = await this.getField(key) || 0;
      const currentNum = typeof currentValue === 'number' ? currentValue : 0;
      const newValue = currentNum + amount;
      
      await this.updateField(key, newValue);
      resolve(newValue);
    });
  }

  callRemoteFunction(funcName, args) {
    return new Promise((resolve) => {
      const requestId = Math.random().toString(36).substring(2, 15);
      const callRequest = {
        type: 'rpc_call',
        request_id: requestId,
        function: funcName,
        args: args,
        caller: this.config.moduleName,
        timestamp: new Date().toISOString()
      };

      this.sendMessage(callRequest);
      
      // In a real implementation, we'd wait for the response
      resolve('response_pending');
    });
  }

  registerFunction(funcName, handler) {
    const registration = {
      type: 'function_registration',
      function: funcName,
      module: this.config.moduleName,
      timestamp: new Date().toISOString()
    };

    this.sendMessage({
      type: 'function_registration',
      data: registration
    });
  }

  subscribeToChanges(callback) {
    this.callbacks.push(callback);
  }

  notifyCallbacks(newState) {
    this.callbacks.forEach(callback => {
      try {
        callback(newState);
      } catch (error) {
        console.error('Error in state change callback:', error);
      }
    });
  }

  close() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Export for different environments
if (typeof module !== 'undefined' && module.exports) {
  module.exports = NexusClient;
} else if (typeof window !== 'undefined') {
  window.NexusClient = NexusClient;
}