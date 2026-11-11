FROM maru60-kicad:9.0.2
USER root
RUN apt-get update && apt-get install -y --no-install-recommends gcc-arm-none-eabi libnewlib-arm-none-eabi libstdc++-arm-none-eabi-newlib build-essential git ca-certificates python3-venv python3-pip && rm -rf /var/lib/apt/lists/*
RUN python3 -m venv /opt/qmk && /opt/qmk/bin/pip install qmk
ENV PATH="/opt/qmk/bin:${PATH}"
WORKDIR /qmk
