FROM python:3.13-bullseye
COPY --from=docker.io/astral/uv:latest /uv /uvx /bin/

COPY ./ /app

WORKDIR /app

RUN uv sync

EXPOSE 5020

CMD ["uv", "run", "main.py"]
