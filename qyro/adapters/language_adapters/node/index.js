const { createClient } = require('redis');
const { Kafka } = require('kafkajs');

class Qyro {
    constructor() {
        this.moduleName = process.env.QYRO_MODULE_NAME || 'node_module';
        this.redis = null;
        this.kafkaProducer = null;
        this.kafkaConsumer = null;
        this.handlers = new Map();

        this._initRedis();
        this._initKafka();
    }

    async _initRedis() {
        const host = process.env.QYRO_REDIS_HOST || 'localhost';
        const port = process.env.QYRO_REDIS_PORT || 6379;
        const password = process.env.QYRO_REDIS_PASSWORD || undefined;

        this.redis = createClient({
            url: `redis://${password ? ':' + password + '@' : ''}${host}:${port}`
        });

        this.redis.on('error', err => console.error('[QYRO] Redis Client Error', err));
        await this.redis.connect();

        // Subscriber client
        this.redisSub = this.redis.duplicate();
        await this.redisSub.connect();
    }

    async _initKafka() {
        const brokers = (process.env.QYRO_KAFKA_BOOTSTRAP_SERVERS || 'localhost:9092').split(',');

        this.kafka = new Kafka({
            clientId: this.moduleName,
            brokers: brokers,
            retry: { retries: 5 }
        });

        this.kafkaProducer = this.kafka.producer();
        try {
            await this.kafkaProducer.connect();
        } catch (e) {
            console.error("[QYRO] Kafka producer failed:", e.message);
            this.kafkaProducer = null;
        }
    }

    async get(key) {
        if (!this.redis) return null;
        const val = await this.redis.get(key);
        try {
            return JSON.parse(val);
        } catch {
            return val;
        }
    }

    async set(key, value) {
        if (!this.redis) return;
        const val = (typeof value === 'object') ? JSON.stringify(value) : value;
        await this.redis.set(key, val);
    }

    async emit(topic, data) {
        const msg = JSON.stringify(data);

        if (this.kafkaProducer) {
            try {
                await this.kafkaProducer.send({
                    topic: topic,
                    messages: [{ key: this.moduleName, value: msg }]
                });
                return;
            } catch (e) {
                console.warn("[QYRO] Kafka emit failed, falling back to Redis", e.message);
            }
        }

        if (this.redis) {
            await this.redis.publish(`qyro:${topic}`, msg);
        }
    }

    on(topic, handler) {
        this.handlers.set(topic, handler);
    }

    async start() {
        // Prefer Kafka for events
        if (this.kafkaProducer) { // Implies Kafka is available
            const consumer = this.kafka.consumer({ groupId: this.moduleName });
            await consumer.connect();
            await consumer.subscribe({ topics: Array.from(this.handlers.keys()), fromBeginning: false });

            await consumer.run({
                eachMessage: async ({ topic, partition, message }) => {
                    const handler = this.handlers.get(topic);
                    if (handler) {
                        try {
                            const data = JSON.parse(message.value.toString());
                            await handler(data);
                        } catch (e) {
                            console.error(`[QYRO] Error in handler for ${topic}:`, e);
                        }
                    }
                },
            });
            console.log(`[QYRO] Listening on Kafka: ${Array.from(this.handlers.keys())}`);
        } else if (this.redisSub) {
            // Redis Fallback
            for (const topic of this.handlers.keys()) {
                await this.redisSub.subscribe(`qyro:${topic}`, (message) => {
                    const handler = this.handlers.get(topic);
                    if (handler) {
                        try {
                            const data = JSON.parse(message);
                            handler(data);
                        } catch (e) {
                            console.error(`[QYRO] Error in handler for ${topic}:`, e);
                        }
                    }
                });
            }
            console.log(`[QYRO] Listening on Redis: ${Array.from(this.handlers.keys())}`);
        }
    }
}

module.exports = new Qyro();
