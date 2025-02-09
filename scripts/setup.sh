#!/bin/bash

# Set versions
ICEBERG_VERSION="1.4.2"
SPARK_VERSION="3.4"

# Create jars directory if it doesn't exist
mkdir -p apps/analysis/spark/jars/

# Download Iceberg JARs
SPARK_JAR="apps/analysis/spark/jars/iceberg-spark-runtime-${SPARK_VERSION}_2.12-${ICEBERG_VERSION}.jar"
AWS_JAR="apps/analysis/spark/jars/iceberg-aws-bundle-${ICEBERG_VERSION}.jar"

if [ ! -f "$SPARK_JAR" ]; then
    echo "Downloading Spark Runtime JAR..."
    wget -P apps/analysis/spark/jars/ \
        https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-${SPARK_VERSION}_2.12/${ICEBERG_VERSION}/iceberg-spark-runtime-${SPARK_VERSION}_2.12-${ICEBERG_VERSION}.jar
else
    echo "Spark Runtime JAR already exists, skipping download."
fi

if [ ! -f "$AWS_JAR" ]; then
    echo "Downloading AWS Bundle JAR..."
    wget -P apps/analysis/spark/jars/ \
        https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-aws-bundle/${ICEBERG_VERSION}/iceberg-aws-bundle-${ICEBERG_VERSION}.jar
else
    echo "AWS Bundle JAR already exists, skipping download."
fi

echo "Setup complete! You can now run docker-compose up -d"