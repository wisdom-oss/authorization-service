"""Module implementing a consumer which will reconnect itself if the need arises"""
import asyncio
import logging
import sys
import time
import uuid
from typing import Optional

from pydantic import AmqpDsn

from messaging.basic_consumer import BasicAMQPConsumer


class ReconnectingAMQPConsumer:
    """
    This consumer will automatically reconnect itself to the message broker if the connection was
    terminated in an unnatural way
    """

    def __init__(
            self,
            amqp_url: AmqpDsn,
            amqp_exchange: str,
            amqp_queue: str = "authorization-service#" + str(uuid.uuid1()),
            amqp_reconnection_delay: float = 5.0,
            amqp_reconnection_tries: int = 3
    ):
        """Create a new ReconnectingAMQPConsumer

        :param amqp_url: URL pointing to the message broker
        :param amqp_exchange: Name of the exchange the consumer should attach itself to
        :param amqp_queue: Name of the queue which should be bound to the exchange,
            defaults to "water-usage-forecast-service#" + UUID4
        :param amqp_reconnection_delay: Time which should be waited until a reconnection is tried
        :param amqp_reconnection_tries: Number of reconnection attempts
        """
        self.__amqp_url = amqp_url
        self.__amqp_exchange = amqp_exchange
        self.__amqp_queue = amqp_queue
        self.__amqp_reconnection_delay = amqp_reconnection_delay
        self.__amqp_reconnection_tries = amqp_reconnection_tries
        self.__logger = logging.getLogger(__name__)
        self.__consumer: Optional[BasicAMQPConsumer] = None
        self.__should_run = False
        self.__amqp_reconnection_try_counter = 0

    def start(self):
        """Start the consumer"""
        self.__consumer = BasicAMQPConsumer(
            amqp_url=self.__amqp_url,
            amqp_queue=self.__amqp_queue,
            amqp_exchange=self.__amqp_exchange
        )
        self.__should_run = True
        self.__run_consumer()

    def stop(self):
        self.__should_run = False
        self.__consumer.stop()

    def __run_consumer(self):
        while self.__should_run:
            self.__consumer.start()
            if self.__amqp_reconnection_try_counter < self.__amqp_reconnection_tries:
                self.__reconnect()
            else:
                sys.exit(2)

    def __reconnect(self):
        """Try to reconnect to the message broker

        :return:
        """
        if self.__consumer.should_reconnect:
            self.__amqp_reconnection_try_counter += 1
            self.__consumer.stop()
            self.__logger.debug(
                'Reconnecting to the message broker in %d seconds',
                self.__amqp_reconnection_delay
            )
            time.sleep(self.__amqp_reconnection_delay)
            self.start()
