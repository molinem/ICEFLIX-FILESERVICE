#!/usr/bin/env python3

import logging #For logger
import IceStorm


def getTopic_manager(broker):
    """Method for obtain topic manager object"""
    topic_manager = None
    topic_manager = IceStorm.TopicManagerPrx.checkedCast(broker.propertyToProxy("IceStorm.TopicManager"))
    if not topic_manager:
        logging.error("[TOPIC MANAGER] -> This proxy is not valid")
    return topic_manager


def get_topic(topic_manager, topic):
    """Method for obtain topic from proxy"""
    topic_retrive = None
    try:
        """Retrive topic"""
        topic_retrive = topic_manager.retrieve(topic)
    except IceStorm.NoSuchTopic:
        """If not topic topic manager create his"""
        topic_retrive = topic_manager.create(topic)
    finally:
        return topic_retrive