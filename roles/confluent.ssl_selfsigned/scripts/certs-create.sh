#!/bin/bash

set -o nounset \
    -o errexit \
    -o verbose
#    -o xtrace

# Cleanup files
rm -f *.crt *.csr *_creds *.jks *.srl *.key *.pem *.der *.p12


for i in broker client
do
	echo "------------------------------- $i -------------------------------"


	# Create host keystore
	keytool -genkey -noprompt \
				 -alias $i \
				 -dname "CN=$i,OU=$3,O=$4,L=$5,S=$6,C=$7" \
                                 -ext san=dns:$i \
				 -keystore $i.keystore.jks \
				 -keyalg RSA \
				 -storepass $8 \
				 -keypass $9


        # Import the CA cert into the keystore
	keytool -noprompt -keystore $i.keystore.jks -alias CARoot -import -file $1  -storepass $8 -keypass $9

        # Import the host certificate into the keystore
	keytool -noprompt -keystore $i.keystore.jks -alias $i -import -file $2 -storepass $8 -keypass $9

	# Create truststore and import the CA cert
	keytool -noprompt -keystore $i.truststore.jks -alias CARoot -import -file $1 -storepass $8 -keypass $9

	# Save creds
  	echo "confluent" > ${i}_sslkey_creds
  	echo "confluent" > ${i}_keystore_creds
  	echo "confluent" > ${i}_truststore_creds

	# Create pem files and keys used for Schema Registry HTTPS testing
	#   openssl x509 -noout -modulus -in client.certificate.pem | openssl md5
	#   openssl rsa -noout -modulus -in client.key | openssl md5 
        #   echo "GET /" | openssl s_client -connect localhost:8082/subjects -cert client.certificate.pem -key client.key -tls1 
	keytool -export -alias $i -file $i.der -keystore $i.keystore.jks -storepass $8
	openssl x509 -inform der -in $i.der -out $i.certificate.pem
	keytool -importkeystore -srckeystore $i.keystore.jks -destkeystore $i.keystore.p12 -deststoretype PKCS12 -deststorepass $8 -srcstorepass $8 -noprompt
	openssl pkcs12 -in $i.keystore.p12 -nodes -nocerts -out $i.key -passin pass:$9

done


