FROM python:3.11-slim-bookworm AS BASE

WORKDIR /app

COPY requirements.txt .

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    libsystemd-dev \
    && apt-get clean \
    && apt-get autoremove -y

RUN --mount=type=cache,target=/root/.cache \
    pip install --user --no-cache-dir -r requirements.txt


FROM gcr.io/distroless/python3-debian12:latest AS FINAL

ARG LIB_PATH=/usr/lib/x86_64-linux-gnu

LABEL maintainer="Ivan Medaev" \
      tool="lologen" \
      language="python" \
      version="3.11"

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV USER=nonroot

USER ${USER}

WORKDIR /app

COPY --from=BASE --chown=${USER}:${USER} /root/.local /home/${USER}/.local
COPY --chown=${USER}:${USER} lologen.py .
COPY --chown=${USER}:${USER} ./src ./src
COPY --from=BASE ${LIB_PATH}/libcap.so.2 \
    ${LIB_PATH}/libsystemd.so.0 \
    ${LIB_PATH}/libgcrypt.so.20 \
    ${LIB_PATH}/libzstd.so.1 \
    ${LIB_PATH}/liblz4.so.1 \
    ${LIB_PATH}/libgpg-error.so.0 \
    ${LIB_PATH}/

ENTRYPOINT [ "/usr/bin/python3.11", "lologen.py" ]
