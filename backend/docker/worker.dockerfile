FROM python:3.13-bullseye
COPY --from=docker.io/astral/uv:latest /uv /uvx /bin/

COPY ./ /app

WORKDIR /app

RUN uv sync

CMD [ "uv", "run", "worker.py" ]