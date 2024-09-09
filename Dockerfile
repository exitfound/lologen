FROM python:3.11-slim-bookworm AS BASE

WORKDIR /app

COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache \
    pip install --user --no-cache-dir -r requirements.txt


FROM gcr.io/distroless/python3-debian12:latest AS FINAL

LABEL maintainer="Ivan Medaev" \
      tool="lologen" \
      language="python" \
      version="3.11"

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV USER=nonroot

WORKDIR /app

COPY --from=BASE --chown=${USER}:${USER} /root/.local /home/${USER}/.local
COPY --chown=${USER}:${USER} lologen.py .

USER ${USER}

ENTRYPOINT [ "/usr/bin/python3.11", "lologen.py" ]
