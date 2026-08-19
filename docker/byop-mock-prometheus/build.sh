#!/usr/bin/env bash
# Build the BYOP mock external Prometheus image (certs + docker build) in one step, so no one has
# to remember the manual sequence. Idempotent: re-running is safe. Call this from the pipeline
# setup (next to the other mock images) and from local runs before any BYOP molecule scenario.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
HOST="${1:-byop-prometheus.confluent}"
TAG="${BYOP_MOCK_IMAGE:-byop-mock-prometheus:latest}"

# 1. Certs (CA + server + client) on the host - both the image build and the molecule
#    byop_distribute_ca / byop_distribute_client_cert playbooks read them from ./certs.
"$DIR/generate-certs.sh" "$HOST"

# 2. Image
docker build -t "$TAG" "$DIR"
echo "Built $TAG (SAN=$HOST)"
