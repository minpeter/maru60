# ngspice for the Maru60 power-tree simulation (pcb/tools/power_sim).
# Network is needed only while building; the simulation runs with --network none.
FROM debian:trixie-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends ngspice \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /work
ENTRYPOINT ["ngspice"]
