from src.app.infrastructure.messenger.consumer import start_consumer
from src.app.controllers.input_dados import InputDadosController


if __name__ == "__main__":
    start_consumer(
        process_fn=InputDadosController.processar_mensagem,
        rabbitmq_url="amqp://gus:gus@rabbitmq:5672/%2F",
    )
