#!/bin/bash -x

set -e

for C in `echo root-ca intermediate`; do

  mkdir $C
  cd $C
  mkdir certs crl newcerts private
  cd ..

  echo 1000 > $C/serial
  touch $C/index.txt $C/index.txt.attr

  echo '
[ ca ]
default_ca = CA_default
[ CA_default ]
dir            = '$C'                     # Where everything is kept
certs          = $dir/certs               # Where the issued certs are kept
crl_dir        = $dir/crl                 # Where the issued crl are kept
database       = $dir/index.txt           # database index file.
new_certs_dir  = $dir/newcerts            # default place for new certs.
certificate    = $dir/cacert.pem          # The CA certificate
serial         = $dir/serial              # The current serial number
crl            = $dir/crl.pem             # The current CRL
private_key    = $dir/private/ca.key.pem  # The private key
RANDFILE       = $dir/.rnd                # private random number file
nameopt        = default_ca
certopt        = default_ca
policy         = policy_match
default_days   = 365
default_md     = sha256

[ policy_match ]
countryName            = optional
stateOrProvinceName    = optional
organizationName       = optional
organizationalUnitName = optional
commonName             = supplied
emailAddress           = optional

[req]
req_extensions = v3_req
distinguished_name = req_distinguished_name

[req_distinguished_name]

[v3_req]
basicConstraints = CA:TRUE
' > $C/openssl.conf
done

mkdir requests
mkdir out

# Create Root CA1
openssl genrsa -out root-ca/private/ca1.key 2048
openssl req -config root-ca/openssl.conf -new -x509 -days 3650 -key root-ca/private/ca1.key -sha256 -extensions v3_req -out root-ca/certs/ca1.crt -subj '/CN=Root-ca1'

# Create intermediate CA1 and Sign by Root CA1
openssl genrsa -out intermediate/private/intermediate1.key 2048
openssl req -config intermediate/openssl.conf -sha256 -new -key intermediate/private/intermediate1.key -out intermediate/certs/intermediate1.csr -subj '/CN=Intermediate1'
openssl ca -batch -config root-ca/openssl.conf -keyfile root-ca/private/ca1.key -cert root-ca/certs/ca1.crt -extensions v3_req -notext -md sha256 -in intermediate/certs/intermediate1.csr -out intermediate/certs/intermediate1.crt

filename="ca1-hosts"
# remove the empty lines
for I in `sed '/^$/d' $filename`; do
  #for I in `seq 1 3` ; do
  openssl req -new -keyout out/$I.key -out requests/$I.request -days 365 -nodes -subj "/CN=$I" -newkey rsa:2048
  openssl ca -batch -config root-ca/openssl.conf -keyfile intermediate/private/intermediate1.key -cert intermediate/certs/intermediate1.crt -out out/$I.crt -notext -infiles requests/$I.request

  # create full chain
  cat out/$I.crt intermediate/certs/intermediate1.crt > out/$I.chain
done

# DUPLICATING CODE... whatever

# Create Root CA2
openssl genrsa -out root-ca/private/ca2.key 2048
openssl req -config root-ca/openssl.conf -new -x509 -days 3650 -key root-ca/private/ca2.key -sha256 -extensions v3_req -out root-ca/certs/ca2.crt -subj '/CN=Root-ca2'

# Create intermediate CA2 and Sign by Root CA2
openssl genrsa -out intermediate/private/intermediate2.key 2048
openssl req -config intermediate/openssl.conf -sha256 -new -key intermediate/private/intermediate2.key -out intermediate/certs/intermediate2.csr -subj '/CN=Intermediate2'
openssl ca -batch -config root-ca/openssl.conf -keyfile root-ca/private/ca2.key -cert root-ca/certs/ca2.crt -extensions v3_req -notext -md sha256 -in intermediate/certs/intermediate2.csr -out intermediate/certs/intermediate2.crt

filename="ca2-hosts"
# remove the empty lines
for I in `sed '/^$/d' $filename`; do
  #for I in `seq 1 3` ; do
  openssl req -new -keyout out/$I.key -out requests/$I.request -days 365 -nodes -subj "/CN=$I" -newkey rsa:2048
  openssl ca -batch -config root-ca/openssl.conf -keyfile intermediate/private/intermediate2.key -cert intermediate/certs/intermediate2.crt -out out/$I.crt -notext -infiles requests/$I.request

  # create full chain
  cat out/$I.crt intermediate/certs/intermediate2.crt > out/$I.chain
done

# Create CA Bundle
cat root-ca/certs/ca1.crt root-ca/certs/ca2.crt > out/caBundle.pem
