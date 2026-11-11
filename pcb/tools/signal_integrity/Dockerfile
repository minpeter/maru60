# ngspice for the signal-integrity decks (network is only needed at build time)
FROM debian:bookworm-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends ngspice \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /work
ENTRYPOINT ["ngspice"]
