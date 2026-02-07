/**
 * Qyro JavaScript Adapter v2 - Enhanced with RPC Support
 *
 * Provides the Qyro API for Node.js/JavaScript services:
 * - Shared state (Redis)
 * - Event streaming (Kafka)
 * - Cross-language RPC
 *
 * For detailed usage examples, visit: https://qyro.dev/docs/js-adapter
 */

const Redis = require("ioredis");
const { Kafka } = require("kafkajs");
const { v4: uuidv4 } = require("uuid");

// Configuration
const REDIS_HOST = process.env.REDIS_HOST || "redis";
const REDIS_PORT = parseInt(process.env.REDIS_PORT || "6379");
const KAFKA_BOOTSTRAP_SERVERS = process.env.KAFKA_BOOTSTRAP_SERVERS || "kafka:9092";
const SERVICE_NAME = process.env.QYRO_SERVICE_NAME || "js-service";
const RPC_TOPIC = "qyro.rpc.requests";
const RPC_RESPONSE_TOPIC = "qyro.rpc.responses";
const RPC_TIMEOUT = parseInt(process.env.QYRO_RPC_TIMEOUT || "30000");

// Lazy-loaded connections
let redis = null;
let kafka = null;
let producer = null;
let isProducerConnected = false;

// RPC State
const exposedFunctions = new Map();
const pendingRequests = new Map();
let rpcServerRunning = false;
let rpcConsumer = null;
let responseConsumer = null;

// =============================================================================
// Connection Management
// =============================================================================

function getRedis() {
  if (!redis) {
    redis = new Redis({
      host: REDIS_HOST,
      port: REDIS_PORT,
      lazyConnect: true,
    });
  }
  return redis;
}

function getKafka() {
  if (!kafka) {
    kafka = new Kafka({
      clientId: `qyro-${SERVICE_NAME}`,
      brokers: [KAFKA_BOOTSTRAP_SERVERS],
    });
  }
  return kafka;
}

async function getProducer() {
  if (!producer) {
    producer = getKafka().producer();
  }
  if (!isProducerConnected) {
    await producer.connect();
    isProducerConnected = true;
  }
  return producer;
}

// =============================================================================
// Shared State API (Redis)
// =============================================================================

async function set(key, value) {
  const r = getRedis();
  const val = typeof value === "object" ? JSON.stringify(value) : String(value);
  await r.set(key, val);
}

async function get(key) {
  const r = getRedis();
  const val = await r.get(key);
  if (val === null) return null;
  try {
    return JSON.parse(val);
  } catch (e) {
    return val;
  }
}

async function del(key) {
  const r = getRedis();
  return (await r.del(key)) > 0;
}

async function exists(key) {
  const r = getRedis();
  return (await r.exists(key)) > 0;
}

async function incr(key, amount = 1) {
  const r = getRedis();
  return await r.incrby(key, amount);
}

async function expire(key, seconds) {
  const r = getRedis();
  return await r.expire(key, seconds);
}

// =============================================================================
// Event Streaming API (Kafka)
// =============================================================================

async function publish(topic, message) {
  const p = await getProducer();
  await p.send({
    topic,
    messages: [{ value: JSON.stringify(message) }],
  });
}

async function subscribe(topic, groupId, callback) {
  const consumer = getKafka().consumer({
    groupId: groupId || `qyro-${SERVICE_NAME}`,
  });

  await consumer.connect();
  await consumer.subscribe({ topic, fromBeginning: true });

  await consumer.run({
    eachMessage: async ({ topic, partition, message }) => {
      const val = JSON.parse(message.value.toString());
      await callback(val, { topic, partition });
    },
  });

  return consumer;
}

// =============================================================================
// Cross-Language RPC API
// =============================================================================

/**
 * Expose a function for cross-language RPC calls.
 * 
 * @param {string} name - Function name (optional, defaults to function.name)
 * @returns {Function} Decorator function
 * 
 * @example
 * const myFunction = expose("myFunction", async (x, y) => x + y);
 * 
 * // Or with default naming
 * async function calculate(a, b) { return a + b; }
 * expose(null, calculate);
 */
function expose(name, fn) {
  if (typeof name === "function") {
    fn = name;
    name = fn.name;
  }

  const fullName = `${SERVICE_NAME}.${name}`;

  exposedFunctions.set(fullName, {
    fn,
    name,
    fullName,
    metadata: {
      service: SERVICE_NAME,
      localName: name,
      fullName,
    },
  });

  log(`Exposed function: ${fullName}`);
  return fn;
}

/**
 * Call a function in another service.
 * 
 * @param {string} functionPath - Full path like "service-name.function_name"
 * @param  {...any} args - Arguments to pass to the function
 * @returns {Promise<any>} The result of the remote function call
 * 
 * @example
 * const result = await call("api.calculate", 1, 2);
 */
async function call(functionPath, ...args) {
  const [targetService] = functionPath.split(".", 1);

  const requestId = uuidv4();
  const request = {
    request_id: requestId,
    source_service: SERVICE_NAME,
    target_service: targetService,
    function_name: functionPath,
    args,
    kwargs: {},
    timestamp: Date.now() / 1000,
  };

  // Ensure response listener is running
  await ensureResponseListener();

  // Create promise for response
  const responsePromise = new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      pendingRequests.delete(requestId);
      reject(new Error(`RPC call to '${functionPath}' timed out after ${RPC_TIMEOUT}ms`));
    }, RPC_TIMEOUT);

    pendingRequests.set(requestId, { resolve, reject, timeout });
  });

  // Send request
  const p = await getProducer();
  await p.send({
    topic: RPC_TOPIC,
    messages: [{ value: JSON.stringify(request) }],
  });

  return responsePromise;
}

/**
 * Start the RPC server to handle incoming calls.
 */
async function startRPCServer() {
  if (rpcServerRunning) return;
  rpcServerRunning = true;

  rpcConsumer = getKafka().consumer({
    groupId: `qyro-rpc-server-${SERVICE_NAME}`,
  });

  await rpcConsumer.connect();
  await rpcConsumer.subscribe({ topic: RPC_TOPIC, fromBeginning: false });

  await rpcConsumer.run({
    eachMessage: async ({ message }) => {
      try {
        const request = JSON.parse(message.value.toString());

        // Check if this request is for us
        if (request.target_service !== SERVICE_NAME) return;

        let response;
        try {
          const funcEntry = exposedFunctions.get(request.function_name);
          if (!funcEntry) {
            throw new Error(`Function '${request.function_name}' not found`);
          }

          const result = await funcEntry.fn(...request.args);

          response = {
            request_id: request.request_id,
            source_service: SERVICE_NAME,
            success: true,
            result,
            error: null,
            timestamp: Date.now() / 1000,
          };
        } catch (err) {
          response = {
            request_id: request.request_id,
            source_service: SERVICE_NAME,
            success: false,
            result: null,
            error: err.message,
            timestamp: Date.now() / 1000,
          };
        }

        // Send response
        const p = await getProducer();
        await p.send({
          topic: RPC_RESPONSE_TOPIC,
          messages: [{ value: JSON.stringify(response) }],
        });
      } catch (err) {
        console.error("[Qyro RPC] Error handling request:", err);
      }
    },
  });

  log(`RPC Server started for service: ${SERVICE_NAME}`);
}

async function ensureResponseListener() {
  if (responseConsumer) return;

  responseConsumer = getKafka().consumer({
    groupId: `qyro-rpc-client-${SERVICE_NAME}-${uuidv4().slice(0, 8)}`,
  });

  await responseConsumer.connect();
  await responseConsumer.subscribe({ topic: RPC_RESPONSE_TOPIC, fromBeginning: false });

  await responseConsumer.run({
    eachMessage: async ({ message }) => {
      try {
        const response = JSON.parse(message.value.toString());

        const pending = pendingRequests.get(response.request_id);
        if (!pending) return;

        clearTimeout(pending.timeout);
        pendingRequests.delete(response.request_id);

        if (response.success) {
          pending.resolve(response.result);
        } else {
          pending.reject(new Error(`RPC Error: ${response.error}`));
        }
      } catch (err) {
        console.error("[Qyro RPC] Error processing response:", err);
      }
    },
  });
}

function listExposedFunctions() {
  return Array.from(exposedFunctions.values()).map((f) => f.metadata);
}

// =============================================================================
// Service Discovery
// =============================================================================

async function registerService(metadata = {}) {
  const serviceInfo = {
    name: SERVICE_NAME,
    host: process.env.HOSTNAME || "localhost",
    functions: listExposedFunctions(),
    ...metadata,
  };
  await set(`qyro:service:${SERVICE_NAME}`, serviceInfo);
  log(`Service registered: ${SERVICE_NAME}`);
}

async function discoverServices() {
  const r = getRedis();
  const keys = await r.keys("qyro:service:*");
  const services = {};

  for (const key of keys) {
    const serviceName = key.replace("qyro:service:", "");
    services[serviceName] = await get(key);
  }

  return services;
}

// =============================================================================
// Logging
// =============================================================================

function log(message, level = "INFO") {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] [${level}] [${SERVICE_NAME}] ${message}`);
}

function info(message) { log(message, "INFO"); }
function warn(message) { log(message, "WARN"); }
function error(message) { log(message, "ERROR"); }
function debug(message) { log(message, "DEBUG"); }

// =============================================================================
// Cleanup
// =============================================================================

async function shutdown() {
  if (redis) await redis.quit();
  if (producer && isProducerConnected) await producer.disconnect();
  if (rpcConsumer) await rpcConsumer.disconnect();
  if (responseConsumer) await responseConsumer.disconnect();
}

process.on("SIGTERM", async () => {
  await shutdown();
  process.exit(0);
});

process.on("SIGINT", async () => {
  await shutdown();
  process.exit(0);
});

// =============================================================================
// Exports
// =============================================================================

module.exports = {
  // State
  set,
  get,
  delete: del,
  exists,
  incr,
  expire,

  // Events
  publish,
  subscribe,

  // RPC
  expose,
  call,
  startRPCServer,
  listExposedFunctions,

  // Discovery
  registerService,
  discoverServices,

  // Logging
  log,
  info,
  warn,
  error,
  debug,

  // Lifecycle
  shutdown,
};
