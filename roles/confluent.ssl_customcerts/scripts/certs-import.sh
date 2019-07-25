#!/bin/bash

set -o nounset \
    -o errexit \
    -o verbose



for i in broker client
do
	echo "------------------------------- $i -------------------------------"



        # Import the CA cert into the keystore
	keytool -noprompt -keystore $i.keystore.jks -alias CARoot -import -file $1  -storepass $4 -keypass $6 -keyalg RSA

        # Import the host certificate into the keystore
	keytool -noprompt -keystore $i.keystore.jks -alias host -import -file $2 -storepass $4 -keypass $7 -keyalg RSA

	# Import the private key into the keystore (must be pkcs12)
        keytool -importkeystore -deststorepass $4 -destkeystore $i.keystore.jks -srcstorepass $8 -srckeystore $3 -srcstoretype PKCS12

        # Create truststore and import the CA cert
	keytool -noprompt -keystore $i.truststore.jks -alias CARoot -import -file $1 -storepass $5 -keypass $6 -keyalg RSA

	# Save creds
  	echo "confluent" > ${i}_sslkey_creds
  	echo "confluent" > ${i}_keystore_creds
  	echo "confluent" > ${i}_truststore_creds

	# Create pem files and keys used for Schema Registry HTTPS testing
	keytool -export -alias host -file $i.der -keystore $i.keystore.jks -storepass $4
	openssl x509 -inform der -in $i.der -out $i.certificate.pem
	keytool -importkeystore -srckeystore $i.keystore.jks -destkeystore $i.keystore.p12 -deststoretype PKCS12 -deststorepass $4 -srcstorepass $4 -noprompt

done


