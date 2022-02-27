---
sidebar_label: reconnecting_consumer
title: messaging.reconnecting_consumer
---

Module implementing a consumer which will reconnect itself if the need arises


## ReconnectingAMQPConsumer Objects

```python
class ReconnectingAMQPConsumer()
```

This consumer will automatically reconnect itself to the message broker if the connection was

terminated in an unnatural way


#### \_\_init\_\_

```python
def __init__(amqp_queue: str = "authorization-service#" + secrets.token_hex(nbytes=4), amqp_reconnection_delay: float = 5.0, amqp_reconnection_tries: int = 3)
```

Create a new ReconnectingAMQPConsumer

**Arguments**:

- `amqp_queue`: Name of the queue which should be bound to the exchange,
defaults to &quot;water-usage-forecast-service#&quot; + UUID4
- `amqp_reconnection_delay`: Time which should be waited until a reconnection is tried
- `amqp_reconnection_tries`: Number of reconnection attempts

#### start

```python
def start()
```

Start the consumer


#### \_\_reconnect

```python
def __reconnect()
```

Try to reconnect to the message broker


