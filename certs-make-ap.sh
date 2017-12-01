#!/bin/bash
set -xe

# Step 1 - Generate SSL key and certificate for each Kafka broker
keytool -keystore server.keystore.jks -alias localhost -validity 365 -keyalg RSA -genkey -storepass password123 -keypass password123 -dname "CN=example.com, OU=PS, O=ExampleInc, L=Earth, S=Denial, C=GB"

# Step 2 - Creating your own CA
openssl req -new -x509 -keyout ca-key -out ca-cert -days 365 -passout pass:password123 -subj "/C=GB/ST=Denial/L=Earth/O=BookeCA/CN=example-bookeca.com"
## save CA cert into server and client trust stores
keytool -keystore server.truststore.jks -alias CARoot -import -file ca-cert -storepass password123 -keypass password123 -noprompt
keytool -keystore client.truststore.jks -alias CARoot -import -file ca-cert -storepass password123 -keypass password123 -noprompt

# Step 3 - Signing the certificate
## First, you need to export the certificate from the keystore (cert-file)
keytool -keystore server.keystore.jks -alias localhost -certreq -file cert-file -storepass password123 -keypass password123

## sign the cert with the CA key, get back signed cert (cert-signed)
openssl x509 -req -CA ca-cert -CAkey ca-key -in cert-file -out cert-signed -days 365 -CAcreateserial -passin pass:password123

## Finally, you need to import both the certificate of the CA and the signed certificate into the keystore:
keytool -keystore server.keystore.jks -alias CARoot -import -file ca-cert -storepass password123 -keypass password123 -noprompt
keytool -keystore server.keystore.jks -alias localhost -import -file cert-signed -storepass password123 -keypass password123 -noprompt
