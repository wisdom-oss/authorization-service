"""AMQP Basic Consumer"""
import logging
import secrets
import sys
from typing import Optional

import pika
import pika.channel
import pika.exceptions
import pika.exchange_type
import pika.frame
import ujson
from pydantic import AmqpDsn

import security
from messaging import executor
from models.amqp.outgoing import AMQPErrorResponse


class BasicAMQPConsumer:
    """
    This consumer works asynchronously and consumes messages from a specified RabbitMQ server via
    the AMQP v0-9-1 protocol. The consumer is based on the example made by the pika library.
    Furthermore, this consumer will import an executor module which will handle the execution of
    some actions based on the messages content and headers.
    """

    def __init__(
            self,
            amqp_url: AmqpDsn,
            amqp_exchange: str,
            amqp_queue: str,
    ):
        """Create a new BasicAMQPConsumer

        This consumer will not connect itself to the message broker and start listening to the
        queue on the exchange with the routing key.

        :param amqp_url: URL containing the connection settings to the AMQP Message Broker
        :type amqp_url: str
        :param amqp_exchange: Name of the exchange which this consumer will use to listen to
        :type amqp_exchange: str
        :param amqp_queue: Name of the queue the consumer will bind itself to
        :type amqp_queue: str
        """
        # Save all properties privately to the object
        self.__amqp_url = amqp_url
        self.__amqp_exchange = amqp_exchange
        self.__amqp_queue = amqp_queue
        self.__logger = logging.getLogger('AMQP.BasicConsumer')

        # Initializing some attributes for later usage
        self.__connection: Optional[pika.SelectConnection] = None
        self.__channel: Optional[pika.channel.Channel] = None
        self.__prefetch_count = 0
        self.__consumer_tag = None
        self.__consuming = False
        self.__closing = False

        self.should_reconnect = False
        self.graceful_shutdown = False
        # Reduce the logging level of pika
        logging.getLogger("pika").setLevel(logging.WARNING)

    def start(self):
        """Start the consumer and the consuming process"""
        self.__connection = self.__connect()
        self.__connection.ioloop.start()

    def stop(self):
        """Close the existing message broker connection in a clean way"""
        if not self.__closing:
            self.__closing = True
            self.__logger.info("Closing the connection to the message broker")
            if self.__consuming:
                self.__stop_consuming()
                # self.__connection.ioloop.start()
            self.__logger.info("Closed the connection to the message broker")
        else:
            self.__logger.info("The connection is already being closed!")
            self.__connection.ioloop.stop()

    def __connect(self) -> pika.SelectConnection:
        """Open a connection to the AMQP message broker

        :return: Connection to the message broker
        :rtype: pika.SelectConnection
        """
        self.__logger.info(
            'Connecting to the message broker on %s',
            self.__amqp_url.host
        )
        connection_parameters = pika.URLParameters(self.__amqp_url)
        # Set a connection name to identify it in the rabbitmq dashboard
        connection_parameters.client_properties = {
            'connection_name': secrets.token_urlsafe(nbytes=16),
            'product': 'WISdoM OSS Authorization Service',
            'platform': 'Python {}'.format(sys.version),
        }
        # Create the connection
        return pika.SelectConnection(
            parameters=connection_parameters,
            on_open_callback=self.__callback_connection_opened,
            on_open_error_callback=self.__callback_connection_error,
            on_close_callback=self.__callback_connection_closed
        )

    def __open_channel(self):
        """Open a new channel to the message broker"""
        self.__logger.info('Trying to open a new channel to the message broker')
        self.__connection.channel(on_open_callback=self.__callback_channel_opened)

    def __close_channel(self):
        """Close the current channel"""
        self.__logger.info(
            "Closing the current channel (channel ID: %s)",
            self.__channel.channel_number
        )
        self.__close_connection()

    def __close_connection(self):
        """Close the connection to the message broker"""
        # Check the internal status of the connection
        if self.__connection.is_closing:
            self.__logger.info("The connection to the message broker is already closing")
        elif self.__connection.is_closed:
            self.__logger.info("The connection to the message broker was closed already")
        else:
            self.__logger.info("Closing the connection to the message broker")
            self.__connection.close()

    def __stop_consuming(self):
        """This will stop the consuming of messages by this consumer"""
        if self.__channel:
            self.__logger.info('Canceling the consuming process')
            self.__channel.basic_cancel(
                self.__consumer_tag,
                callback=self.__callback_cancel_ok
            )
            self.__channel.queue_delete(
                queue=self.__amqp_queue,
                if_unused=False,
                if_empty=False,
                callback=self.__callback_queue_delete_ok
            )

    def __reconnect(self):
        """Set the reconnection need to true

        :return:
        """
        self.should_reconnect = True
        self.stop()

    def __setup_exchange(self):
        """Set up the exchange on the channel present in the consumer

        :return:
        """
        self.__logger.info(
            'Setting up the exchange "%s" on the channel #%i',
            self.__amqp_exchange, self.__channel.channel_number
        )
        # Create a callback for the successful creation
        self.__channel.exchange_declare(
            exchange=self.__amqp_exchange,
            exchange_type=pika.exchange_type.ExchangeType.fanout.value,
            callback=self.__callback_exchange_declare_ok
        )

    def __setup_queue(self):
        """Set up a queue which is attached to the fanout exchange

        :return:
        """
        self.__logger.info(
            'Trying to declare a queue on the exchange "%s"',
            self.__amqp_exchange
        )
        self.__channel.queue_declare(
            queue=self.__amqp_queue,
            callback=self.__callback_queue_declare_ok
        )

    def __enable_message_consuming(self):
        """This will start the consuming of messages by this consumer

        :return:
        """
        self.__logger.info(
            'Starting to consume messages from exchange %s',
            self.__amqp_exchange
        )
        self.__channel.add_on_cancel_callback(self.__callback_consumer_cancelled)
        self.__consuming = True
        self.__consumer_tag = self.__channel.basic_consume(
            queue=self.__amqp_queue,
            on_message_callback=self.__callback_new_message,
            callback=self.__callback_consume_started
        )
        
    def __callback_consume_started(self, __consume_status: pika.frame.Method):
        """Callback for a successfully started consume session
        
        :param __consume_status:
        :return:
        """
        self.__logger.info('Successfully started consuming messages')
        
    def __callback_connection_opened(self, __connection: pika.BaseConnection):
        """Callback for a successful connection attempt.

        If this callback is called, the consumer will try to open up a channel

        :param __connection: Connection handle which was opened
        """
        self.__logger.info(
            'Opened connection "%s" to message broker.',
            __connection.params.client_properties.get('connection_name')
        )
        self.__open_channel()

    def __callback_connection_error(
            self,
            __connection: pika.BaseConnection,
            __error: Exception
    ):
        """Callback for a failed connection attempt

        :param __connection: Connection which could not be established
        :type __connection: pika.BaseConnection
        :param __error: Connection error
        :type __error: Exception
        """
        self.__logger.error(
            'An error occurred during the connection attempt to the message broker: %s. Retrying '
            'in 5 seconds',
            __error
        )
        self.__connection.ioloop.call_later(5, self.__connection.ioloop.close)

    def __callback_connection_closed(
            self,
            __connection: pika.connection.Connection,
            __reason: Exception
    ):
        """Callback for an unexpected connection closure

        :param __connection: The connection which was closed
        :param __reason: The closure reason
        """
        self.__channel = None
        if self.__closing:
            self.__connection.ioloop.stop()
        else:
            self.__logger.warning(
                "The connection (Connection Name: %s) was closed unexpected: %s",
                __connection.params.client_properties.get("connection_name"),
                __reason
            )
            self.__reconnect()

    def __callback_channel_opened(self, __channel: pika.channel.Channel):
        """Callback for a successfully opened channel

        This will save the channel to the object and try to set up an exchange on this channel
        """
        self.__logger.info(
            'Opened channel (Channel ID: %s) to the message broker',
            __channel.channel_number
        )
        self.__channel = __channel
        # Add a callback which fires if the channel was closed
        self.__channel.add_on_close_callback(self.__callback_channel_closed)
        # Set up the exchange on the channel
        self.__setup_exchange()

    def __callback_channel_closed(
            self,
            __channel: pika.channel.Channel,
            __reason: Exception
    ):
        """Callback for a closed channel

        :param __channel: The closed channel
        :type __channel: pika.channel.Channel
        :param __reason: Reason for closing the channel
        :type __reason: Exception
        """
        if isinstance(__reason, pika.exceptions.ConnectionClosedByBroker):
            self.__logger.warning('The connection was closed by the message broker. Trying to '
                                  'reconnect')
            self.__reconnect()
        elif isinstance(__reason, pika.exceptions.ChannelClosedByClient):
            self.graceful_shutdown = True
            self.__logger.info('The channel (Channel ID: %s) was closed successfully during a '
                               'graceful shutdown', __channel.channel_number)
        else:
            self.__logger.warning(
                'The channel (Channel ID: %s) was closed for the following reason: %s',
                __channel.channel_number,
                __reason
            )
            # Close the connection to the message broker
            self.__close_connection()

    def __callback_cancel_ok(
            self,
            __frame: pika.frame.Method,
    ):
        """Callback which is called if the channel was cancelled successfully

        :param __frame:
        :return:
        """
        self.__logger.info("Channel was cancelled successfully")
        self.__consuming = False
        self.__close_channel()

    def __callback_exchange_declare_ok(
            self,
            __frame: pika.frame.Method,
    ):
        """Callback used for a successful exchange declaration on the message broker

        :param __frame: Method frame
        """
        self.__logger.info(
            'Successfully declared the exchange %s on the channel #%i',
            self.__amqp_exchange, self.__channel.channel_number
        )
        self.__setup_queue()

    def __callback_queue_declare_ok(
            self,
            __frame: pika.frame.Method,
    ):
        """Callback for successfully declaring a queue on an exchange

        :param __frame: Frame indicating the status of the executed command
        :return:
        """
        self.__logger.info(
            'Successfully declared queue "%s" on exchange "%s"',
            self.__amqp_queue, self.__amqp_exchange
        )
        self.__channel.queue_bind(
            queue=self.__amqp_queue,
            exchange=self.__amqp_exchange,
            callback=self.__callback_queue_bind_ok
        )

    def __callback_queue_bind_ok(
            self,
            __frame: pika.frame.Method
    ):
        """Callback for a successful queue bind

        :param __frame:
        :return:
        """
        self.__logger.info(
            'Successfully bound queue "%s" to the exchange "%s"',
            self.__amqp_queue, self.__amqp_exchange
        )
        self.__channel.basic_qos(
            prefetch_count=self.__prefetch_count,
            callback=self.__callback_basic_qos_ok
        )

    def __callback_queue_delete_ok(
            self,
            __frame: pika.frame.Method
    ):
        """Callback for a successful queue bind

        :param __frame:
        :return:
        """
        self.__logger.info(
            'Successfully deleted queue "%s" from the exchange "%s"',
            self.__amqp_queue, self.__amqp_exchange
        )

    def __callback_basic_qos_ok(
            self,
            __frame: pika.frame.Method
    ):
        """Callback for a successful QOS (Quality of Service) setup

        :param __frame:
        :return:
        """
        self.__logger.info(
            'Successfully set the QOS prefetch count to %d',
            self.__prefetch_count
        )
        self.__enable_message_consuming()

    def __callback_consumer_cancelled(
            self,
            __frame: pika.frame.Method
    ):
        """Callback which will be called if the consumer was cancelled

        :param __frame:
        :return:
        """
        self.__logger.warning(
            'Consumer was cancelled. The consumer will shutdown: %s',
            __frame
        )
        if self.__channel:
            self.__channel.close()

    def __callback_new_message(
            self,
            channel: pika.channel.Channel,
            delivery: pika.spec.Basic.Deliver,
            msg_prop: pika.spec.BasicProperties,
            content: bytes
    ):
        """Callback for new messages read from the server

        :param channel: Channel used to get the message
        :param delivery: Basic information about the message delivery
        :param msg_prop: Message properties
        :param content: Message content
        """
        self.__logger.info(
            'Received new message (message id: #%s) via exchange "%s"',
            delivery.delivery_tag, delivery.exchange
        )
        # Create some message properties for every response
        _msg_properties = pika.BasicProperties(
            correlation_id=msg_prop.correlation_id if msg_prop.correlation_id is not None else "",
            app_id='AUTH_SERVER'
        )
        # Try to get the credentials from the message headers
        _foreign_client_id = msg_prop.app_id
        _foreign_client_secret = msg_prop.headers.get('X-WISdoM-Auth', None)
        # Now check if any of the values are NoneType
        if None in [_foreign_client_id, _foreign_client_secret]:
            # Reject the message due to the missing authorization
            self.__logger.warning(
                'The received message will be rejected due to missing Authorization information. '
                'The sender will be informed about this if any reply-to address and a correlation '
                'id was set'
            )
            channel.basic_reject(delivery.delivery_tag, requeue=False)
            # Check if the reply-to attribute was set
            if msg_prop.reply_to is not None:
                # Send a error message
                channel.basic_publish(
                    exchange='',
                    routing_key=msg_prop.reply_to,
                    body=AMQPErrorResponse(
                        error='MISSING_AUTHORIZATION',
                        error_description='The required authorization information was not found'
                    ).json().encode('utf-8'),
                    properties=_msg_properties
                )
            else:
                self.__logger.error(
                    'The message either contained no reply-to field or no correlation id or both '
                    'fields are missing. Therefore the message will be rejected without any '
                    'explanation'
                )
            return
        # Now check if the client secret and id are valid
        if not security.client_credentials_valid(_foreign_client_id, _foreign_client_secret):
            self.__logger.warning(
                'An unauthorized message was received. The message will be rejected without '
                'requeueing the message. If a routing key was set the sender will be informed of '
                'this'
            )
            channel.basic_reject(delivery.delivery_tag, requeue=False)
            # Check if a reply to attribute was set
            if msg_prop.reply_to is not None:
                # Send a error message
                channel.basic_publish(
                    exchange='',
                    routing_key=msg_prop.reply_to,
                    body=AMQPErrorResponse(
                        error='INVALID_GRANT',
                        error_description='The authorization credentials are not valid. Please '
                                          'check your credentials'
                    ).json().encode('utf-8'),
                    properties=_msg_properties
                )
            else:
                self.__logger.info(
                    'The message did not contain a reply-to property. Therefore the sender will '
                    'not be informed of the error'
                )
            return
        # Since the message was valid run the message executor which will receive the message
        # body only. The executor will only be called if a correlation id and the reply-to field
        # were set
        if None in [msg_prop.correlation_id, msg_prop.reply_to]:
            self.__logger.warning(
                'Missing information detected. The message will not be passed to the executor and '
                'the sender can not be notified of this error'
            )
            return
        _exc_result = executor.execute({"payload": ujson.loads(content)})
        self.__logger.info('Executed action successfully. Now returning the message')
        # Return the message to the message broker
        channel.basic_publish(
            exchange='',
            routing_key=msg_prop.reply_to,
            body=_exc_result.json(by_alias=True, exclude_none=True).encode('utf-8'),
            properties=_msg_properties
        )


