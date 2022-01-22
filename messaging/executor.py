"""This module will be used to execute the incoming messages"""
import logging

__logger = logging.getLogger(__name__)


def execute(message: dict) -> dict:
    """AMQP Message Executor

    This executor is responsible for selecting the correct forecasting procedures depending on
    the data present in the message. The message is expected as a dictionary.

    :param message: Message from the message broker
    :type message: dict
    :return: Response which should be sent back to the message broker
    """
    # TODO: Implement logic for

