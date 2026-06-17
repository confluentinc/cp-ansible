#!/bin/bash
# Cert generation for ANSIENG-5765 case 10: 4-tier PKI, partial chain.
# Hierarchy: Root -> Int1 -> Int2 -> Leaf, but the Root is intentionally omitted
# from the CA bundle (DoD-style partial chain).
# Produces:
#   out/caBundle.pem   = Int1 + Int2 (NO root)
#   out/<host>.crt     = leaf ONLY (no inline intermediates)
#   out/<host>.key     = leaf private key
set -euo pipefail

OUT=out
HOSTS_FILE="${1:-hosts}"

rm -rf "$OUT" && mkdir -p "$OUT"

ca_ext() {
    cat > "$1" <<EOF
basicConstraints = critical, CA:TRUE
keyUsage = critical, keyCertSign, cRLSign
EOF
}

leaf_ext() {
    local hostname=$1 fqdn=$2 outfile=$3
    cat > "$outfile" <<EOF
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth, clientAuth
subjectAltName = DNS:${hostname},DNS:${fqdn}
EOF
}

# 1. Root CA (self-signed) — generated but NOT shipped in the bundle.
openssl req -new -x509 -nodes -days 3650 \
    -keyout "$OUT/root.key" \
    -out   "$OUT/root.crt" \
    -subj '/CN=ANSIENG-5765-Root/O=Confluent/OU=Test'

# 2. Int1 (signed by Root).
ca_ext "$OUT/int1.ext"
openssl req -new -nodes -keyout "$OUT/int1.key" -out "$OUT/int1.csr" \
    -subj '/CN=ANSIENG-5765-Int1/O=Confluent/OU=Test'
openssl x509 -req -days 3650 -sha256 \
    -in "$OUT/int1.csr" \
    -CA "$OUT/root.crt" -CAkey "$OUT/root.key" -CAcreateserial \
    -out "$OUT/int1.crt" \
    -extfile "$OUT/int1.ext"

# 3. Int2 (signed by Int1).
ca_ext "$OUT/int2.ext"
openssl req -new -nodes -keyout "$OUT/int2.key" -out "$OUT/int2.csr" \
    -subj '/CN=ANSIENG-5765-Int2/O=Confluent/OU=Test'
openssl x509 -req -days 3650 -sha256 \
    -in "$OUT/int2.csr" \
    -CA "$OUT/int1.crt" -CAkey "$OUT/int1.key" -CAcreateserial \
    -out "$OUT/int2.crt" \
    -extfile "$OUT/int2.ext"

# 4. Per-host leaf, signed by Int2.
while IFS= read -r host || [ -n "$host" ]; do
    [ -z "$host" ] && continue
    fqdn="${host}.confluent"

    openssl req -new -nodes \
        -keyout "$OUT/${host}.key" \
        -out   "$OUT/${host}.csr" \
        -subj  "/CN=${host}/O=Confluent/OU=Test"

    leaf_ext "$host" "$fqdn" "$OUT/${host}.ext"

    openssl x509 -req -days 3650 -sha256 \
        -in "$OUT/${host}.csr" \
        -CA "$OUT/int2.crt" -CAkey "$OUT/int2.key" -CAcreateserial \
        -out "$OUT/${host}.crt" \
        -extfile "$OUT/${host}.ext"

    rm -f "$OUT/${host}.csr" "$OUT/${host}.ext"
done < "$HOSTS_FILE"

# 5. CA bundle: Int1 + Int2 ONLY. Root is deliberately omitted (partial chain).
cat "$OUT/int1.crt" "$OUT/int2.crt" > "$OUT/caBundle.pem"

# Remove the root from the output entirely so it cannot leak into the install.
rm -f "$OUT"/root.crt "$OUT"/root.key
rm -f "$OUT"/int*.csr "$OUT"/int*.ext "$OUT"/*.srl

echo "case 10 cert generation complete (no root):"
ls -1 "$OUT" | sed 's/^/  /'
