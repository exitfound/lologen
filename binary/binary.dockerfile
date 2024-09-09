FROM python:3.11-slim-bookworm AS BASE

WORKDIR /app

COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache \
    pip install --user --no-cache-dir -r requirements.txt

COPY lologen.py .

RUN apt-get update \
    && apt-get -y install --no-install-recommends binutils \
    && apt-get clean \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt /var/lib/dpkg /tmp/* /var/tmp/* \
    && python3 -m PyInstaller --onefile --noconfirm --clean --name lologen lologen.py


FROM gcr.io/distroless/base-debian12:latest AS FINAL

LABEL maintainer="Ivan Medaev" \
      tool="lologen" \
      language="python" \
      version="3.11"

ENV CHIPSET_ARCH=x86_64-linux-gnu
ENV USER=nonroot

WORKDIR /app

COPY --from=BASE /lib/${CHIPSET_ARCH}/libz.so.1 /lib/${CHIPSET_ARCH}/
COPY --from=BASE --chown=${USER}:${GROUP} /app/dist/lologen .

USER ${USER}

ENTRYPOINT [ "./lologen" ]
