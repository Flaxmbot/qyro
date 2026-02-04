class QyroClient {
    constructor() {
        this.ws = null;
        this.handlers = new Map(); // topic -> [handlers]
        this.stateHandlers = [];
        this.state = {};
        this.connected = false;
        this.gatewayUrl = 'ws://localhost:8765/ws';
    }

    connect(url) {
        if (url) this.gatewayUrl = url;

        this.ws = new WebSocket(this.gatewayUrl);

        this.ws.onopen = () => {
            console.log('[QYRO] Connected to Gateway');
            this.connected = true;
        };

        this.ws.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                this._handleMessage(msg);
            } catch (e) {
                console.error('[QYRO] Invalid message:', e);
            }
        };

        this.ws.onclose = () => {
            console.log('[QYRO] Disconnected. Reconnecting...');
            this.connected = false;
            setTimeout(() => this.connect(), 3000);
        };
    }

    _handleMessage(msg) {
        if (msg.type === 'state_update') {
            this.state = { ...this.state, ...msg.data };
            this.stateHandlers.forEach(h => h(this.state));
        } else if (msg.type === 'event' || msg.type === 'module_event') {
            const topic = msg.topic || (msg.data && msg.data.type); // Fallback
            if (this.handlers.has(topic)) {
                this.handlers.get(topic).forEach(h => h(msg.data));
            }
        }
    }

    get(key) {
        return this.state[key];
    }

    set(key, value) {
        if (!this.connected) return;
        const update = {};
        update[key] = value;

        this.ws.send(JSON.stringify({
            type: 'state_update',
            data: update
        }));

        // Optimistic update
        this.state = { ...this.state, ...update };
        this.stateHandlers.forEach(h => h(this.state));
    }

    emit(topic, data) {
        if (!this.connected) return;
        // Map generic emit to rpc_call or custom event type if Gateway supports it
        // Currently Gateway supports 'rpc_call' which goes to Kafka
        this.ws.send(JSON.stringify({
            type: 'rpc_call',
            function: topic, // misuse function name as topic
            args: data
        }));
    }

    on(topic, handler) {
        if (!this.handlers.has(topic)) {
            this.handlers.set(topic, []);
        }
        this.handlers.get(topic).push(handler);
    }

    onStateChange(handler) {
        this.stateHandlers.push(handler);
    }
}

export const qyro = new QyroClient();
