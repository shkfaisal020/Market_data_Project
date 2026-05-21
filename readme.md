# Conceptual / System Design

## 1. Scaling: Handling 1 Billion Events Per Day

If the data volume increased to 1 billion events per day, the architecture would move from a single-node ETL system to a distributed streaming architecture.

### Proposed Changes

- Introduce Apache Kafka as a distributed message broker to handle high-throughput event ingestion.
- Replace the single Python ETL process with Apache Spark Streaming or Apache Flink for distributed parallel processing.
- Store raw and processed data in scalable cloud storage systems such as Amazon S3, Delta Lake, Snowflake, or BigQuery.
- Use Kubernetes for container orchestration, auto-scaling, and high availability.
- Implement data partitioning strategies based on instrument_id and event_date to improve performance.
- Introduce caching layers and load balancers for handling high API traffic.

This architecture would provide:
- Horizontal scalability
- Fault tolerance
- Real-time processing
- High throughput
- Better resiliency

---

## 2. Monitoring: Health Checks in Production

To ensure the pipeline is running correctly in production, multiple monitoring and health check mechanisms would be implemented.

### API Health Checks
A dedicated endpoint such as:

GET /health

would verify:
- API availability
- Database connectivity
- Response latency
- Internal service status

### ETL Monitoring
The ETL pipeline would continuously monitor:
- Records processed per minute
- Failed records count
- Processing latency
- API timeout frequency
- Database insertion failures

### Monitoring Tools

#### Prometheus
Used for collecting application and infrastructure metrics.

#### Grafana
Used for dashboard visualization and alerting.

#### ELK Stack
Used for centralized logging:
- Elasticsearch
- Logstash
- Kibana

### Alerting
Automated alerts would be configured for:
- Pipeline failures
- High error rates
- Service downtime
- Data quality issues
- Resource utilization spikes

---

## 3. Recovery & Idempotency

If the pipeline fails midway through a large batch (e.g., 10GB), idempotency mechanisms ensure no partial or duplicate data is written.

### Database Constraints
Unique constraints on:
- instrument_id
- timestamp

prevent duplicate records from being inserted.

### Checkpointing
The ETL process would maintain checkpoints such as:
- Last processed batch ID
- Kafka offsets
- Processing timestamps

This allows recovery from the exact failure point.

### Transaction Management
Database operations would use atomic transactions:
- Commit only after successful processing
- Rollback if any failure occurs

### Retry Mechanism
Failed batches would automatically retry using:
- Exponential backoff
- Dead-letter queues for problematic records

### Idempotent Processing
The pipeline would be designed so that reprocessing the same batch multiple times produces the same final result without duplicates.

This guarantees reliable and fault-tolerant data processing in production environments.