# BYOP mock Prometheus for cp-ansible molecule tests.
#
# A standalone Prometheus configured the way a customer's external Prometheus must be for BYOP:
# the OTLP receiver on, the Confluent resource attributes promoted, an out-of-order window, and
# C3's recording rules loaded. TLS is required. Basic auth and mTLS are both supported via two
# web-config files; the molecule scenario picks one by overriding the command.
#
# Build (run ./generate-certs.sh first to populate ./certs):
#   ./generate-certs.sh
#   docker build -t byop-mock-prometheus:latest .
FROM prom/prometheus:v3.2.1

COPY prometheus.yml                /etc/prometheus/prometheus.yml
COPY recording_rules-generated.yml /etc/prometheus/recording_rules-generated.yml
COPY web-config-basic.yml          /etc/prometheus/web-config-basic.yml
COPY web-config-mtls.yml           /etc/prometheus/web-config-mtls.yml
# Prometheus runs as nobody (65534); the private keys are 0600, so copy them owned by that user.
COPY --chown=65534:65534 certs/    /etc/prometheus/certs/

# Default: Basic auth over TLS. The mTLS scenario overrides the command to use web-config-mtls.yml.
CMD ["--config.file=/etc/prometheus/prometheus.yml", \
     "--web.config.file=/etc/prometheus/web-config-basic.yml", \
     "--web.enable-otlp-receiver", \
     "--storage.tsdb.path=/prometheus"]
