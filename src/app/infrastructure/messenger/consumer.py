from typing import Callable
import pika
from ...domain.models import Task
from .serialization import unpack_task


def start_consumer(
    process_fn: Callable[[Task], None],
    queue_name: str = "task_queue",
    rabbitmq_url: str = "amqp://gus:gus@rabbitmq:5672/%2F",
) -> None:
    """
    Inicia o consumidor RabbitMQ, processando e confirmando manualmente cada mensagem.
    """
    params = pika.URLParameters(rabbitmq_url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    channel.basic_qos(prefetch_count=1)

    def callback(ch, method, properties, body):
        # try:
        task = unpack_task(body)
        process_fn(task)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        # except Exception as exc:
        #     print(f"Erro ao processar mensagem: {exc}")
        #     ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_consume(
        queue=queue_name, on_message_callback=callback, auto_ack=False
    )
    print(" [*] Aguardando mensagens. Para sair, pressione CTRL+C")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()
