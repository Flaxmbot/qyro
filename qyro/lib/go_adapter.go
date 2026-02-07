// Qyro Go Adapter v1 - Cross-Language RPC Support
//
// Provides the Qyro API for Go services:
// - Shared state (Redis)
// - Event streaming (Kafka)
// - Cross-language RPC
//
// For detailed usage examples, visit: https://qyro.dev/docs/go-adapter

package qyro

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"sync"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/google/uuid"
	"github.com/segmentio/kafka-go"
)

// Configuration
var (
	RedisHost     = getEnv("REDIS_HOST", "redis")
	RedisPort     = getEnv("REDIS_PORT", "6379")
	KafkaServers  = getEnv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
	ServiceName   = getEnv("QYRO_SERVICE_NAME", "go-service")
	RPCTopic      = "qyro.rpc.requests"
	RPCRespTopic  = "qyro.rpc.responses"
	RPCTimeout    = 30 * time.Second
)

var ctx = context.Background()

// Lazy-loaded clients
var (
	redisClient  *redis.Client
	redisOnce    sync.Once
	kafkaWriter  *kafka.Writer
	writerOnce   sync.Once
)

// RPC State
var (
	exposedFunctions = make(map[string]func([]interface{}) (interface{}, error))
	pendingRequests  = make(map[string]chan RPCResponse)
	funcMutex        sync.RWMutex
	reqMutex         sync.RWMutex
)

// RPCRequest represents an RPC call
type RPCRequest struct {
	RequestID     string                 `json:"request_id"`
	SourceService string                 `json:"source_service"`
	TargetService string                 `json:"target_service"`
	FunctionName  string                 `json:"function_name"`
	Args          []interface{}          `json:"args"`
	Kwargs        map[string]interface{} `json:"kwargs"`
	Timestamp     float64                `json:"timestamp"`
}

// RPCResponse represents an RPC response
type RPCResponse struct {
	RequestID     string      `json:"request_id"`
	SourceService string      `json:"source_service"`
	Success       bool        `json:"success"`
	Result        interface{} `json:"result"`
	Error         string      `json:"error,omitempty"`
	Timestamp     float64     `json:"timestamp"`
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

// GetRedis returns the Redis client
func GetRedis() *redis.Client {
	redisOnce.Do(func() {
		redisClient = redis.NewClient(&redis.Options{
			Addr: fmt.Sprintf("%s:%s", RedisHost, RedisPort),
		})
	})
	return redisClient
}

// GetKafkaWriter returns the Kafka producer
func GetKafkaWriter(topic string) *kafka.Writer {
	return &kafka.Writer{
		Addr:     kafka.TCP(KafkaServers),
		Topic:    topic,
		Balancer: &kafka.LeastBytes{},
	}
}

// =============================================================================
// Shared State API (Redis)
// =============================================================================

// Set stores a value in Redis
func Set(key string, value interface{}) error {
	data, err := json.Marshal(value)
	if err != nil {
		return err
	}
	return GetRedis().Set(ctx, key, data, 0).Err()
}

// Get retrieves a value from Redis
func Get(key string) (string, error) {
	return GetRedis().Get(ctx, key).Result()
}

// GetJSON retrieves and unmarshals a value
func GetJSON(key string, dest interface{}) error {
	val, err := GetRedis().Get(ctx, key).Result()
	if err != nil {
		return err
	}
	return json.Unmarshal([]byte(val), dest)
}

// Delete removes a key
func Delete(key string) error {
	return GetRedis().Del(ctx, key).Err()
}

// Exists checks if a key exists
func Exists(key string) (bool, error) {
	n, err := GetRedis().Exists(ctx, key).Result()
	return n > 0, err
}

// Incr increments a counter
func Incr(key string, amount int64) (int64, error) {
	return GetRedis().IncrBy(ctx, key, amount).Result()
}

// =============================================================================
// Event Streaming API (Kafka)
// =============================================================================

// Publish sends a message to a Kafka topic
func Publish(topic string, message interface{}) error {
	data, err := json.Marshal(message)
	if err != nil {
		return err
	}
	
	w := GetKafkaWriter(topic)
	defer w.Close()
	
	return w.WriteMessages(ctx, kafka.Message{
		Value: data,
	})
}

// Subscribe listens to a Kafka topic
func Subscribe(topic, groupID string, handler func([]byte) error) {
	if groupID == "" {
		groupID = fmt.Sprintf("qyro-%s", ServiceName)
	}
	
	r := kafka.NewReader(kafka.ReaderConfig{
		Brokers:  []string{KafkaServers},
		Topic:    topic,
		GroupID:  groupID,
		MinBytes: 10e3,
		MaxBytes: 10e6,
	})
	
	go func() {
		for {
			m, err := r.ReadMessage(ctx)
			if err != nil {
				log.Printf("[Qyro] Kafka read error: %v", err)
				continue
			}
			if err := handler(m.Value); err != nil {
				log.Printf("[Qyro] Handler error: %v", err)
			}
		}
	}()
}

// =============================================================================
// Cross-Language RPC API
// =============================================================================

// Expose registers a function for RPC calls
func Expose(name string, fn func([]interface{}) (interface{}, error)) {
	fullName := fmt.Sprintf("%s.%s", ServiceName, name)
	funcMutex.Lock()
	exposedFunctions[fullName] = fn
	funcMutex.Unlock()
	Info(fmt.Sprintf("Exposed function: %s", fullName))
}

// Call invokes a function in another service
func Call(functionPath string, args ...interface{}) (interface{}, error) {
	requestID := uuid.New().String()
	
	// Parse target service
	var targetService string
	for i, c := range functionPath {
		if c == '.' {
			targetService = functionPath[:i]
			break
		}
	}
	
	request := RPCRequest{
		RequestID:     requestID,
		SourceService: ServiceName,
		TargetService: targetService,
		FunctionName:  functionPath,
		Args:          args,
		Kwargs:        make(map[string]interface{}),
		Timestamp:     float64(time.Now().UnixNano()) / 1e9,
	}
	
	// Create response channel
	respChan := make(chan RPCResponse, 1)
	reqMutex.Lock()
	pendingRequests[requestID] = respChan
	reqMutex.Unlock()
	
	// Ensure response listener is running
	go startResponseListener()
	
	// Send request
	if err := Publish(RPCTopic, request); err != nil {
		return nil, err
	}
	
	// Wait for response
	select {
	case resp := <-respChan:
		if resp.Success {
			return resp.Result, nil
		}
		return nil, fmt.Errorf("RPC Error: %s", resp.Error)
	case <-time.After(RPCTimeout):
		reqMutex.Lock()
		delete(pendingRequests, requestID)
		reqMutex.Unlock()
		return nil, fmt.Errorf("RPC call to '%s' timed out", functionPath)
	}
}

// StartRPCServer starts the RPC server
func StartRPCServer() {
	r := kafka.NewReader(kafka.ReaderConfig{
		Brokers:  []string{KafkaServers},
		Topic:    RPCTopic,
		GroupID:  fmt.Sprintf("qyro-rpc-server-%s", ServiceName),
		MinBytes: 10e3,
		MaxBytes: 10e6,
	})
	
	Info(fmt.Sprintf("RPC Server started for service: %s", ServiceName))
	
	go func() {
		for {
			m, err := r.ReadMessage(ctx)
			if err != nil {
				continue
			}
			
			var req RPCRequest
			if err := json.Unmarshal(m.Value, &req); err != nil {
				continue
			}
			
			// Check if for us
			if req.TargetService != ServiceName {
				continue
			}
			
			go handleRPCRequest(req)
		}
	}()
}

func handleRPCRequest(req RPCRequest) {
	resp := RPCResponse{
		RequestID:     req.RequestID,
		SourceService: ServiceName,
		Timestamp:     float64(time.Now().UnixNano()) / 1e9,
	}
	
	funcMutex.RLock()
	fn, exists := exposedFunctions[req.FunctionName]
	funcMutex.RUnlock()
	
	if !exists {
		resp.Success = false
		resp.Error = fmt.Sprintf("Function '%s' not found", req.FunctionName)
	} else {
		result, err := fn(req.Args)
		if err != nil {
			resp.Success = false
			resp.Error = err.Error()
		} else {
			resp.Success = true
			resp.Result = result
		}
	}
	
	Publish(RPCRespTopic, resp)
}

var responseListenerOnce sync.Once

func startResponseListener() {
	responseListenerOnce.Do(func() {
		r := kafka.NewReader(kafka.ReaderConfig{
			Brokers:  []string{KafkaServers},
			Topic:    RPCRespTopic,
			GroupID:  fmt.Sprintf("qyro-rpc-client-%s-%s", ServiceName, uuid.New().String()[:8]),
			MinBytes: 10e3,
			MaxBytes: 10e6,
		})
		
		go func() {
			for {
				m, err := r.ReadMessage(ctx)
				if err != nil {
					continue
				}
				
				var resp RPCResponse
				if err := json.Unmarshal(m.Value, &resp); err != nil {
					continue
				}
				
				reqMutex.RLock()
				ch, exists := pendingRequests[resp.RequestID]
				reqMutex.RUnlock()
				
				if exists {
					ch <- resp
					reqMutex.Lock()
					delete(pendingRequests, resp.RequestID)
					reqMutex.Unlock()
				}
			}
		}()
	})
}

// ListExposedFunctions returns all exposed functions
func ListExposedFunctions() []map[string]string {
	funcMutex.RLock()
	defer funcMutex.RUnlock()
	
	var funcs []map[string]string
	for name := range exposedFunctions {
		funcs = append(funcs, map[string]string{
			"name":    name,
			"service": ServiceName,
		})
	}
	return funcs
}

// =============================================================================
// Service Discovery
// =============================================================================

// RegisterService registers this service for discovery
func RegisterService(metadata map[string]interface{}) {
	info := map[string]interface{}{
		"name":      ServiceName,
		"host":      getEnv("HOSTNAME", "localhost"),
		"functions": ListExposedFunctions(),
	}
	for k, v := range metadata {
		info[k] = v
	}
	Set(fmt.Sprintf("qyro:service:%s", ServiceName), info)
	Info(fmt.Sprintf("Service registered: %s", ServiceName))
}

// =============================================================================
// Logging
// =============================================================================

// Log prints a formatted log message
func Log(message, level string) {
	ts := time.Now().Format(time.RFC3339)
	fmt.Printf("[%s] [%s] [%s] %s\n", ts, level, ServiceName, message)
}

// Info logs an info message
func Info(message string) { Log(message, "INFO") }

// Warn logs a warning message
func Warn(message string) { Log(message, "WARN") }

// Error logs an error message
func Error(message string) { Log(message, "ERROR") }

// Debug logs a debug message
func Debug(message string) { Log(message, "DEBUG") }
