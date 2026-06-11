#!/bin/bash
# Cert generation for ANSIENG-5765 case 9: 4-tier PKI, full chain inlined in cert file.
# Hierarchy: Root -> Int1 -> Int2 -> Leaf
# Produces:
#   out/caBundle.pem   = Root ONLY
#   out/<host>.crt     = leaf + Int2 + Int1 concatenated (whole chain in one file)
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

# 1. Root CA (self-signed).
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

# 4. Per-host leaf, signed by Int2. Inline the whole chain into <host>.crt.
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
        -out "$OUT/${host}.leaf-only.crt" \
        -extfile "$OUT/${host}.ext"

    # Inline the chain: leaf + Int2 + Int1 (no root in cert file).
    cat "$OUT/${host}.leaf-only.crt" "$OUT/int2.crt" "$OUT/int1.crt" > "$OUT/${host}.crt"

    rm -f "$OUT/${host}.csr" "$OUT/${host}.ext" "$OUT/${host}.leaf-only.crt"
done < "$HOSTS_FILE"

# 5. CA bundle: Root ONLY (case 9).
cp "$OUT/root.crt" "$OUT/caBundle.pem"

# Cleanup CA scratch files.
rm -f "$OUT"/int*.csr "$OUT"/int*.ext "$OUT"/*.srl

echo "case 9 cert generation complete:"
ls -1 "$OUT" | sed 's/^/  /'
