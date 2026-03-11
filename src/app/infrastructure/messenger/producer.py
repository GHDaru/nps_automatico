from typing import NoReturn
import pika
from ...domain.models import Task
from .serialization import pack_task
import os


def send_task(
    task: Task,
    queue_name: str = "task_queue",
    rabbitmq_url: str = "amqp://gus:gus@localhost:5672/%2F",
) -> None:
    """
    Envia um Task para o RabbitMQ de forma assíncrona (fire-and-forget).
    """
    params = pika.URLParameters(rabbitmq_url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    message = pack_task(task)
    channel.basic_publish(
        exchange="",
        routing_key=queue_name,
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,  # Mensagem persistente
            content_type="application/x-msgpack",
        ),
    )
    connection.close()
