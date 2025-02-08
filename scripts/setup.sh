#!/bin/bash

# Set versions
ICEBERG_VERSION="1.4.2"
SPARK_VERSION="3.4"

# Download Iceberg JARs
echo "Downloading Iceberg JARs..."
wget -P apps/analysis/spark/jars/ \
    https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-${SPARK_VERSION}_2.12/${ICEBERG_VERSION}/iceberg-spark-runtime-${SPARK_VERSION}_2.12-${ICEBERG_VERSION}.jar

wget -P apps/analysis/spark/jars/ \
    https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-aws-bundle/${ICEBERG_VERSION}/iceberg-aws-bundle-${ICEBERG_VERSION}.jar

echo "Setup complete! You can now run docker-compose up -d"