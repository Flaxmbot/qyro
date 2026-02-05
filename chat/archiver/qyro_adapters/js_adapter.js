const Redis = require("ioredis");
const { Kafka } = require("kafkajs");

const redis = new Redis({
  host: process.env.REDIS_HOST || "redis",
  port: process.env.REDIS_PORT || 6379,
});

const kafka = new Kafka({
  clientId: "qyro-client",
  brokers: [(process.env.KAFKA_BOOTSTRAP_SERVERS || "kafka:9092")],
});

const producer = kafka.producer();
let isProducerConnected = false;

async function ensureProducer() {
  if (!isProducerConnected) {
    await producer.connect();
    isProducerConnected = true;
  }
}

module.exports = {
  set: async (key, value) => {
    const val = typeof value === "object" ? JSON.stringify(value) : value;
    await redis.set(key, val);
  },

  get: async (key) => {
    const val = await redis.get(key);
    try {
      return JSON.parse(val);
    } catch (e) {
      return val;
    }
  },

  publish: async (topic, message) => {
    await ensureProducer();
    await producer.send({
      topic,
      messages: [{ value: JSON.stringify(message) }],
    });
  },

  subscribe: async (topic, groupId, callback) => {
    const consumer = kafka.consumer({ groupId: groupId || "default" });
    await consumer.connect();
    await consumer.subscribe({ topic, fromBeginning: true });

    await consumer.run({
      eachMessage: async ({ topic, partition, message }) => {
        const val = JSON.parse(message.value.toString());
        callback(val);
      },
    });
  },
};
