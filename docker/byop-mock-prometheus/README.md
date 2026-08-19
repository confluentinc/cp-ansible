# byop-mock-prometheus

A prebuilt mock external Prometheus for the cp-ansible BYOP molecule tests, modeled on the
`usmagent-mock-ccloud` image pattern. It is a standalone Prometheus configured the way a
customer's external Prometheus must be for BYOP:

- the OTLP receiver enabled (`--web.enable-otlp-receiver`)
- the Confluent resource attributes promoted (`otlp.promote_resource_attributes`)
- an out-of-order window (`storage.tsdb.out_of_order_time_window: 10m`)
- C3's recording rules loaded (`recording_rules-generated.yml`)
- TLS required, with Basic auth and mTLS both available

## Files

- `Dockerfile` - builds the image from `prom/prometheus`
- `prometheus.yml` - OTLP promotion, out-of-order window, recording rules (no alerting)
- `recording_rules-generated.yml` - a copy of C3's recording rules (keep in sync with control-center-backend/config)
- `web-config-basic.yml` - TLS + Basic auth (default)
- `web-config-mtls.yml` - TLS + `RequireAndVerifyClientCert` (mTLS scenario)
- `generate-certs.sh` - generates test CA, server cert (SAN = the dialed host), and client cert into `./certs` (gitignored)

## Build

```bash
cd docker/byop-mock-prometheus
./generate-certs.sh byop-prometheus.confluent          # SAN = the host C3 dials in the molecule scenario
# set the Basic-auth password hash to match the scenario password:
#   htpasswd -nBC 10 "" | tr -d ':\n'   -> paste into web-config-basic.yml for user 'c3'
docker build -t byop-mock-prometheus:latest .
```

The molecule pipeline builds/pulls this image the same way it does `usmagent-mock-ccloud:latest`.

## How the molecule scenario uses it

Add it as a platform in the scenario's `molecule.yml` (on the `confluent` network):

```yaml
- name: byop-prometheus
  hostname: byop-prometheus.confluent
  groups: [byop_prometheus]
  image: byop-mock-prometheus:latest
  networks:
    - name: confluent
```

Then point C3 and the nodes at it via the inventory vars:

```yaml
control_center_next_gen_external_prometheus_enabled: true
control_center_next_gen_dependency_prometheus_host: byop-prometheus.confluent
control_center_next_gen_dependency_prometheus_port: 9090
control_center_next_gen_dependency_prometheus_ssl_enabled: true
# basic-auth scenario: point the truststore at the mock CA (docker/.../certs/ca.crt)
# mTLS scenario: override the container command to use web-config-mtls.yml and supply the client cert/key
```
