#!/bin/bash
# Cert generation for ANSIENG-5765 case 1: 2-tier PKI.
# Produces:
#   out/caBundle.pem   = Root CA (self-signed) ONLY
#   out/<host>.crt     = leaf certificate, signed directly by the Root (leaf only, no inline intermediate)
#   out/<host>.key     = leaf private key
set -euo pipefail

OUT=out
HOSTS_FILE="${1:-hosts}"

rm -rf "$OUT" && mkdir -p "$OUT"

# Helper: write a minimal openssl extfile for a leaf cert with SANs.
write_leaf_ext() {
    local hostname=$1 fqdn=$2 outfile=$3
    cat > "$outfile" <<EOF
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth, clientAuth
subjectAltName = DNS:${hostname},DNS:${fqdn}
EOF
}

# 1. Root CA (self-signed).
openssl req -new -x509 -nodes -days 3650 \
    -keyout "$OUT/root.key" \
    -out   "$OUT/root.crt" \
    -subj '/CN=ANSIENG-5765-Root/O=Confluent/OU=Test'

# 2. Per-host leaf, signed directly by Root.
while IFS= read -r host || [ -n "$host" ]; do
    [ -z "$host" ] && continue
    fqdn="${host}.confluent"

    openssl req -new -nodes \
        -keyout "$OUT/${host}.key" \
        -out   "$OUT/${host}.csr" \
        -subj  "/CN=${host}/O=Confluent/OU=Test"

    write_leaf_ext "$host" "$fqdn" "$OUT/${host}.ext"

    openssl x509 -req -days 3650 -sha256 \
        -in "$OUT/${host}.csr" \
        -CA "$OUT/root.crt" -CAkey "$OUT/root.key" -CAcreateserial \
        -out "$OUT/${host}.crt" \
        -extfile "$OUT/${host}.ext"

    rm -f "$OUT/${host}.csr" "$OUT/${host}.ext"
done < "$HOSTS_FILE"

# 3. Assemble CA bundle (Root only for case 1).
cp "$OUT/root.crt" "$OUT/caBundle.pem"

echo "case 1 cert generation complete:"
ls -1 "$OUT" | sed 's/^/  /'
