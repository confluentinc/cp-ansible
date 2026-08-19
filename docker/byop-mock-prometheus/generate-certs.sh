#!/usr/bin/env bash
# Generate test certs for the BYOP mock Prometheus: a CA, a server cert (SAN = the address C3
# and the nodes dial), and a client cert (for the mTLS scenario). Test-only, output to ./certs
# (gitignored). Run this before `docker build`.
set -euo pipefail

HOST="${1:-byop-prometheus.confluent}"
DIR="$(cd "$(dirname "$0")" && pwd)/certs"
mkdir -p "$DIR"

# Idempotent: if the full set is already present, reuse it (safe to call from pipeline setup).
if [[ -f "$DIR/ca.crt" && -f "$DIR/server.crt" && -f "$DIR/client.crt" ]]; then
  echo "Certs already present in $DIR - skipping generation."
  exit 0
fi

# CA
openssl req -x509 -newkey rsa:2048 -nodes -keyout "$DIR/ca.key" -out "$DIR/ca.crt" \
  -days 3650 -subj "/CN=byop-mock-prometheus-ca"

# Server cert (SAN must cover the address C3 and the nodes dial)
openssl req -newkey rsa:2048 -nodes -keyout "$DIR/server.key" -out "$DIR/server.csr" \
  -subj "/CN=${HOST}"
openssl x509 -req -in "$DIR/server.csr" -CA "$DIR/ca.crt" -CAkey "$DIR/ca.key" -CAcreateserial \
  -out "$DIR/server.crt" -days 3650 \
  -extfile <(printf "subjectAltName=DNS:%s" "${HOST}")

# Client cert (for the mTLS scenario)
openssl req -newkey rsa:2048 -nodes -keyout "$DIR/client.key" -out "$DIR/client.csr" \
  -subj "/CN=c3-client"
openssl x509 -req -in "$DIR/client.csr" -CA "$DIR/ca.crt" -CAkey "$DIR/ca.key" -CAcreateserial \
  -out "$DIR/client.crt" -days 3650

rm -f "$DIR"/*.csr "$DIR"/*.srl
echo "Certs for ${HOST} written to $DIR"
