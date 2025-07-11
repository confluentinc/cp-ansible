#!/bin/bash -x

set -e

# Clean up existing directories first
rm -rf root-ca intermediate requests out

for C in `echo root-ca intermediate`; do
  mkdir -p $C/{certs,crl,newcerts,private}
  echo 1000 > $C/serial
  touch $C/index.txt $C/index.txt.attr

  # Create OpenSSL config for CA certificates
  cat > $C/openssl.conf << EOF
[ ca ]
default_ca = CA_default

[ CA_default ]
dir               = .                    # Current directory
certs             = \$dir/certs          # Where the issued certs are kept
crl_dir           = \$dir/crl            # Where the issued crl are kept
database          = \$dir/index.txt      # database index file
new_certs_dir     = \$dir/newcerts      # default place for new certs
certificate       = \$dir/certs/ca.crt   # The CA certificate
serial            = \$dir/serial         # The current serial number
private_key       = \$dir/private/ca.key # The private key
RANDFILE          = \$dir/private/.rand  # private random number file
nameopt           = default_ca
certopt          = default_ca
policy           = policy_match
default_days     = 365
default_md       = sha256
copy_extensions  = copy
email_in_dn      = no
rand_serial      = yes

[ policy_match ]
countryName             = optional
stateOrProvinceName     = optional
organizationName        = optional
organizationalUnitName  = optional
commonName             = supplied
emailAddress           = optional

[req]
distinguished_name = req_distinguished_name
req_extensions = v3_ca

[req_distinguished_name]

# For CA certificates
[v3_ca]
basicConstraints = critical,CA:TRUE
keyUsage = critical,digitalSignature,keyEncipherment,keyCertSign,cRLSign

# For server certificates
[v3_req_server]
basicConstraints = CA:FALSE
keyUsage = critical,digitalSignature,keyEncipherment
extendedKeyUsage = serverAuth,clientAuth
EOF

  # Create separate OpenSSL config for server certificates
  cat > $C/server-openssl.conf << EOF
[ req ]
distinguished_name = req_distinguished_name
req_extensions = v3_req_server

[ req_distinguished_name ]

[ v3_req_server ]
basicConstraints = CA:FALSE
keyUsage = critical,digitalSignature,keyEncipherment
extendedKeyUsage = serverAuth,clientAuth
subjectAltName = \${ENV::SAN}
EOF
done

mkdir -p requests out

# Create Root CA1
openssl genrsa -out root-ca/private/ca1.key 2048
(cd root-ca && openssl req -config openssl.conf -new -x509 -days 3650 \
    -key private/ca1.key -sha256 -extensions v3_ca \
    -out certs/ca1.crt -subj '/CN=Root-ca1')

# Create intermediate CA1 and Sign by Root CA1
openssl genrsa -out intermediate/private/intermediate1.key 2048
(cd intermediate && openssl req -config openssl.conf -sha256 -new \
    -key private/intermediate1.key -out certs/intermediate1.csr \
    -subj '/CN=Intermediate1')
(cd root-ca && openssl ca -batch -config openssl.conf \
    -keyfile private/ca1.key -cert certs/ca1.crt \
    -extensions v3_ca -notext -md sha256 \
    -in ../intermediate/certs/intermediate1.csr \
    -out ../intermediate/certs/intermediate1.crt)

# Process CA1 hosts
filename="ca1-hosts"
while IFS=: read -r service hostname || [ -n "$service" ]; do
    [ -z "$service" ] && continue  # Skip empty lines

    FQDN="$hostname.confluent"
    IP=$(dig +short "$hostname")

    # Set SAN environment variable
    export SAN="DNS:$hostname,DNS:$FQDN${IP:+,IP:$IP}"

    echo "Creating certificate for $hostname with CN=$service and SAN=$SAN"

    # Create certificate with correct CN and SAN
    openssl req -new -keyout "out/$hostname.key" \
        -out "requests/$hostname.request" \
        -days 365 -nodes \
        -subj "/CN=$service" \
        -newkey rsa:2048 \
        -config root-ca/server-openssl.conf \
        -extensions v3_req_server

    # Sign certificate
    (cd root-ca && openssl ca -batch \
        -config openssl.conf \
        -keyfile ../intermediate/private/intermediate1.key \
        -cert ../intermediate/certs/intermediate1.crt \
        -out "../out/$hostname.crt" \
        -notext \
        -extensions v3_req_server \
        -infiles "../requests/$hostname.request")

    # Create full chain
    cat "out/$hostname.crt" intermediate/certs/intermediate1.crt > "out/$hostname.chain"
done < "$filename"

# Create Root CA2
openssl genrsa -out root-ca/private/ca2.key 2048
(cd root-ca && openssl req -config openssl.conf -new -x509 -days 3650 \
    -key private/ca2.key -sha256 -extensions v3_ca \
    -out certs/ca2.crt -subj '/CN=Root-ca2')

# Create intermediate CA2 and Sign by Root CA2
openssl genrsa -out intermediate/private/intermediate2.key 2048
(cd intermediate && openssl req -config openssl.conf -sha256 -new \
    -key private/intermediate2.key -out certs/intermediate2.csr \
    -subj '/CN=Intermediate2')
(cd root-ca && openssl ca -batch -config openssl.conf \
    -keyfile private/ca2.key -cert certs/ca2.crt \
    -extensions v3_ca -notext -md sha256 \
    -in ../intermediate/certs/intermediate2.csr \
    -out ../intermediate/certs/intermediate2.crt)

# Process CA2 hosts
filename="ca2-hosts"
while IFS=: read -r service hostname || [ -n "$service" ]; do
    [ -z "$service" ] && continue  # Skip empty lines

    FQDN="$hostname.confluent"
    IP=$(dig +short "$hostname")

    # Set SAN environment variable
    export SAN="DNS:$hostname,DNS:$FQDN${IP:+,IP:$IP}"

    echo "Creating certificate for $hostname with CN=$service and SAN=$SAN"

    # Create certificate with correct CN and SAN
    openssl req -new -keyout "out/$hostname.key" \
        -out "requests/$hostname.request" \
        -days 365 -nodes \
        -subj "/CN=$service" \
        -newkey rsa:2048 \
        -config root-ca/server-openssl.conf \
        -extensions v3_req_server

    # Sign certificate
    (cd root-ca && openssl ca -batch \
        -config openssl.conf \
        -keyfile ../intermediate/private/intermediate2.key \
        -cert ../intermediate/certs/intermediate2.crt \
        -out "../out/$hostname.crt" \
        -notext \
        -extensions v3_req_server \
        -infiles "../requests/$hostname.request")

    # Create full chain
    cat "out/$hostname.crt" intermediate/certs/intermediate2.crt > "out/$hostname.chain"
done < "$filename"

# Create CA Bundle
cat root-ca/certs/ca1.crt root-ca/certs/ca2.crt > out/caBundle.pem
