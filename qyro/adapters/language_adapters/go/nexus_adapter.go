// src/adapters/language_adapters/go/nexus_adapter.go
package nexus

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"time"

	"github.com/Shopify/sarama"
	"github.com/go-redis/redis/v8"
)

// Config holds the configuration for the Nexus adapter
type Config struct {
	KafkaBootstrapServers string
	RedisAddr            string
	ModuleName           string
}

// DefaultConfig returns a default configuration
func DefaultConfig() *Config {
	return &Config{
		KafkaBootstrapServers: "localhost:9092",
		RedisAddr:            "localhost:6379",
		ModuleName:           "go_module",
	}
}

// State represents the shared state
type State map[string]interface{}

// Nexus represents the main adapter struct
type Nexus struct {
	config      *Config
	kafkaClient sarama.Client
	kafkaSyncProducer sarama.SyncProducer
	redisClient *redis.Client
	stateCache  State
	ctx         context.Context
	cancel      context.CancelFunc
}

// New creates a new Nexus instance
func New() *Nexus {
	ctx, cancel := context.WithCancel(context.Background())
	return &Nexus{
		config:     DefaultConfig(),
		stateCache: make(State),
		ctx:        ctx,
		cancel:     cancel,
	}
}

// NewWithConfig creates a new Nexus instance with custom configuration
func NewWithConfig(config *Config) *Nexus {
	ctx, cancel := context.WithCancel(context.Background())
	return &Nexus{
		config:     config,
		stateCache: make(State),
		ctx:        ctx,
		cancel:     cancel,
	}
}

// Connect initializes the connections to Kafka and Redis
func (n *Nexus) Connect() error {
	// Initialize Redis client
	n.redisClient = redis.NewClient(&redis.Options{
		Addr: n.config.RedisAddr,
	})
	
	// Test Redis connection
	if _, err := n.redisClient.Ping(n.ctx).Result(); err != nil {
		return fmt.Errorf("failed to connect to Redis: %v", err)
	}

	// Initialize Kafka client
	config := sarama.NewConfig()
	config.Producer.RequiredAcks = sarama.WaitForLocal
	config.Producer.Retry.Max = 3
	config.Producer.Return.Successes = true

	client, err := sarama.NewClient([]string{n.config.KafkaBootstrapServers}, config)
	if err != nil {
		return fmt.Errorf("failed to create Kafka client: %v", err)
	}
	n.kafkaClient = client

	// Create sync producer
	syncProducer, err := sarama.NewSyncProducerFromClient(client)
	if err != nil {
		return fmt.Errorf("failed to create Kafka sync producer: %v", err)
	}
	n.kafkaSyncProducer = syncProducer

	// Register module
	if err := n.registerModule(); err != nil {
		return fmt.Errorf("failed to register module: %v", err)
	}

	return nil
}

// registerModule registers this module with the system
func (n *Nexus) registerModule() error {
	registration := map[string]interface{}{
		"type":      "module_registration",
		"module_name": n.config.ModuleName,
		"timestamp": time.Now().Format(time.RFC3339),
		"language":  "go",
	}

	jsonData, err := json.Marshal(registration)
	if err != nil {
		return err
	}

	msg := &sarama.ProducerMessage{
		Topic: "nexus_module_events",
		Key:   sarama.StringEncoder(n.config.ModuleName),
		Value: sarama.ByteEncoder(jsonData),
	}

	_, _, err = n.kafkaSyncProducer.SendMessage(msg)
	return err
}

// ReadState reads the current state from Redis
func (n *Nexus) ReadState() (State, error) {
	result, err := n.redisClient.HGetAll(n.ctx, "nexus:state").Result()
	if err != nil {
		return nil, err
	}

	state := make(State)
	for key, value := range result {
		var parsedValue interface{}
		if err := json.Unmarshal([]byte(value), &parsedValue); err != nil {
			// If JSON parsing fails, store as string
			state[key] = value
		} else {
			state[key] = parsedValue
		}
	}

	n.stateCache = state
	return state, nil
}

// WriteState writes the entire state to Redis
func (n *Nexus) WriteState(state State) error {
	// Convert state to Redis hash
	data := make(map[string]interface{})
	for key, value := range state {
		jsonValue, err := json.Marshal(value)
		if err != nil {
			log.Printf("Warning: failed to marshal value for key %s: %v", key, err)
			continue
		}
		data[key] = string(jsonValue)
	}

	err := n.redisClient.HMSet(n.ctx, "nexus:state", data).Err()
	if err != nil {
		return err
	}

	// Publish state change event to Kafka
	stateChange := map[string]interface{}{
		"type":     "state_change",
		"module":   n.config.ModuleName,
		"changes":  state,
		"timestamp": time.Now().Format(time.RFC3339),
	}

	jsonData, err := json.Marshal(stateChange)
	if err != nil {
		return err
	}

	msg := &sarama.ProducerMessage{
		Topic: "nexus_state_changes",
		Key:   sarama.StringEncoder(n.config.ModuleName),
		Value: sarama.ByteEncoder(jsonData),
	}

	_, _, err = n.kafkaSyncProducer.SendMessage(msg)
	return err
}

// UpdateField updates a single field in the state
func (n *Nexus) UpdateField(key string, value interface{}) error {
	jsonValue, err := json.Marshal(value)
	if err != nil {
		return err
	}

	err = n.redisClient.HSet(n.ctx, "nexus:state", key, string(jsonValue)).Err()
	if err != nil {
		return err
	}

	// Publish field update event to Kafka
	fieldUpdate := map[string]interface{}{
		"type":      "field_update",
		"module":    n.config.ModuleName,
		"key":       key,
		"value":     value,
		"timestamp": time.Now().Format(time.RFC3339),
	}

	jsonData, err := json.Marshal(fieldUpdate)
	if err != nil {
		return err
	}

	msg := &sarama.ProducerMessage{
		Topic: "nexus_field_updates",
		Key:   sarama.StringEncoder(key),
		Value: sarama.ByteEncoder(jsonData),
	}

	_, _, err = n.kafkaSyncProducer.SendMessage(msg)
	return err
}

// GetField retrieves a specific field from the state
func (n *Nexus) GetField(key string) (interface{}, error) {
	state, err := n.ReadState()
	if err != nil {
		return nil, err
	}
	
	value, exists := state[key]
	if !exists {
		return nil, fmt.Errorf("field '%s' does not exist", key)
	}
	
	return value, nil
}

// IncrementField increments a numeric field
func (n *Nexus) IncrementField(key string, amount int64) (int64, error) {
	currentValue, err := n.GetField(key)
	if err != nil {
		// If field doesn't exist, start with 0
		currentValue = 0
	}

	var currentNum int64
	switch v := currentValue.(type) {
	case int64:
		currentNum = v
	case float64:
		currentNum = int64(v)
	case int:
		currentNum = int64(v)
	case json.Number:
		if num, err := v.Int64(); err == nil {
			currentNum = num
		} else {
			currentNum = 0
		}
	default:
		currentNum = 0
	}

	newValue := currentNum + amount
	err = n.UpdateField(key, newValue)
	if err != nil {
		return 0, err
	}

	return newValue, nil
}

// CallRemoteFunction calls a remote function via Kafka
func (n *Nexus) CallRemoteFunction(funcName string, args interface{}) (interface{}, error) {
	requestID := fmt.Sprintf("%d", time.Now().UnixNano())
	callRequest := map[string]interface{}{
		"type":      "rpc_call",
		"request_id": requestID,
		"function":  funcName,
		"args":      args,
		"caller":    n.config.ModuleName,
		"timestamp": time.Now().Format(time.RFC3339),
	}

	jsonData, err := json.Marshal(callRequest)
	if err != nil {
		return nil, err
	}

	msg := &sarama.ProducerMessage{
		Topic: "nexus_rpc_requests",
		Key:   sarama.StringEncoder(funcName),
		Value: sarama.ByteEncoder(jsonData),
	}

	_, _, err = n.kafkaSyncProducer.SendMessage(msg)
	if err != nil {
		return nil, err
	}

	// In a real implementation, we'd wait for the response
	// For now, return a placeholder
	return "response_pending", nil
}

// RegisterFunction registers a function to be callable remotely
func (n *Nexus) RegisterFunction(funcName string, handler func(interface{}) interface{}) error {
	registration := map[string]interface{}{
		"type":      "function_registration",
		"function":  funcName,
		"module":    n.config.ModuleName,
		"timestamp": time.Now().Format(time.RFC3339),
	}

	jsonData, err := json.Marshal(registration)
	if err != nil {
		return err
	}

	msg := &sarama.ProducerMessage{
		Topic: "nexus_function_registry",
		Key:   sarama.StringEncoder(funcName),
		Value: sarama.ByteEncoder(jsonData),
	}

	_, _, err = n.kafkaSyncProducer.SendMessage(msg)
	return err
}

// SubscribeToChanges subscribes to state change events
func (n *Nexus) SubscribeToChanges(callback func(State)) error {
	// This would typically create a Kafka consumer
	// For now, we'll just return nil
	log.Println("Subscribing to state changes...")
	return nil
}

// Close closes all connections
func (n *Nexus) Close() error {
	if n.cancel != nil {
		n.cancel()
	}
	
	var err1, err2, err3 error
	if n.kafkaSyncProducer != nil {
		err1 = n.kafkaSyncProducer.Close()
	}
	if n.kafkaClient != nil {
		err2 = n.kafkaClient.Close()
	}
	if n.redisClient != nil {
		err3 = n.redisClient.Close()
	}
	
	if err1 != nil {
		return err1
	}
	if err2 != nil {
		return err2
	}
	return err3
}