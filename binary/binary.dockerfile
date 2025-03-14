FROM python:3.11-slim-bookworm AS base

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        binutils \
        gcc \
        libc6-dev \
        libsystemd-dev \
    && apt-get clean \
    && apt-get autoremove -y

COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache \
    pip install --user --no-cache-dir -r requirements.txt

COPY ./src ./src
COPY lologen.py .

RUN python3 -m PyInstaller --onefile --noconfirm --clean --name lologen lologen.py


FROM gcr.io/distroless/base-debian12:latest AS final

LABEL maintainer="Ivan Medaev" \
      tool="lologen" \
      language="python" \
      version="3.11"

ENV CHIPSET_ARCH=x86_64-linux-gnu
ENV USER=nonroot

USER ${USER}

WORKDIR /app

COPY --from=base /lib/${CHIPSET_ARCH}/libz.so.1 /lib/${CHIPSET_ARCH}/
COPY --from=base --chown=${USER}:${USER} /app/dist/lologen .

ENTRYPOINT [ "./lologen" ]
