package qyro

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/confluentinc/confluent-kafka-go/kafka"
	"github.com/redis/go-redis/v9"
)

type Qyro struct {
	redis    *redis.Client
	producer *kafka.Producer
	module   string
	ctx      context.Context
}

func New() *Qyro {
	q := &Qyro{
		ctx:    context.Background(),
		module: getEnv("QYRO_MODULE_NAME", "go_module"),
	}

	// Redis Connection
	host := getEnv("QYRO_REDIS_HOST", "localhost")
	port := getEnv("QYRO_REDIS_PORT", "6379")
	password := getEnv("QYRO_REDIS_PASSWORD", "")

	q.redis = redis.NewClient(&redis.Options{
		Addr:     fmt.Sprintf("%s:%s", host, port),
		Password: password,
	})

	// Kafka Connection
	servers := getEnv("QYRO_KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
	p, err := kafka.NewProducer(&kafka.ConfigMap{
		"bootstrap.servers": servers,
		"client.id":         q.module,
	})

	if err == nil {
		q.producer = p
	} else {
		log.Printf("[QYRO] Kafka connection failed: %v", err)
	}

	return q
}

func (q *Qyro) Get(key string, target interface{}) error {
	val, err := q.redis.Get(q.ctx, key).Result()
	if err != nil {
		return err
	}
	return json.Unmarshal([]byte(val), target)
}

func (q *Qyro) Set(key string, value interface{}) error {
	jsonVal, err := json.Marshal(value)
	if err != nil {
		return err
	}
	return q.redis.Set(q.ctx, key, jsonVal, 0).Err()
}

func (q *Qyro) Emit(topic string, data interface{}) error {
	jsonVal, err := json.Marshal(data)
	if err != nil {
		return err
	}

	if q.producer != nil {
		topic_str := topic
		err = q.producer.Produce(&kafka.Message{
			TopicPartition: kafka.TopicPartition{Topic: &topic_str, Partition: kafka.PartitionAny},
			Value:          jsonVal,
			Key:            []byte(q.module),
		}, nil)
		return err
	}

	// Redis Fallback
	return q.redis.Publish(q.ctx, "qyro:"+topic, jsonVal).Err()
}

func getEnv(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return fallback
}
