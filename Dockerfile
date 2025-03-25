# Use the official Airflow image as base
FROM apache/airflow:2.9.0-python3.11

# Switch to root for installing system dependencies
USER root

# Install system dependencies needed for building packages and general tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        git \
        curl \
        ca-certificates \
        gcc \
        postgresql-client \
        libpq-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install UV using a more robust method
RUN curl -L https://github.com/astral-sh/uv/releases/download/0.1.21/uv-x86_64-unknown-linux-gnu.tar.gz -o uv.tar.gz && \
    mkdir -p /tmp/uvtemp && \
    tar -xzf uv.tar.gz -C /tmp/uvtemp && \
    find /tmp/uvtemp -name "uv" -type f -executable -exec cp {} /usr/local/bin/uv \; && \
    rm -rf /tmp/uvtemp uv.tar.gz && \
    chmod +x /usr/local/bin/uv && \
    uv --version

# Set working directory for the application code
WORKDIR /app

# Copy project files
COPY ./pyproject.toml ./README.md* /app/
COPY ./src /app/src/

# Create a virtual environment using UV
RUN uv venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" \
    VIRTUAL_ENV="/app/.venv"

# Install the specific pendulum version needed for Airflow 2.6.3
# Then install your package and Airflow with postgres support
RUN . /app/.venv/bin/activate && \
    uv pip install pendulum==2.1.2 && \
    uv pip install -e . && \
    uv pip install \
        --constraint="https://raw.githubusercontent.com/apache/airflow/constraints-2.9.0/constraints-3.11.txt" \
        "apache-airflow==2.9.0" \
        "apache-airflow[postgres]" && \
    uv pip freeze > /tmp/installed_packages.txt && \
    echo "Installed packages:" && cat /tmp/installed_packages.txt

# Create directories that Airflow requires and set proper permissions
RUN mkdir -p /opt/airflow/dags /opt/airflow/logs /opt/airflow/data/meta \
    /opt/airflow/data/logs/inventory_logs /opt/airflow/data/logs/PLAYER \
    /opt/airflow/data/logs/GAME /opt/airflow/data/logs/SEASON && \
    chown -R airflow:root /opt/airflow /app

# Copy Airflow DAGs and custom configuration into the appropriate directories
COPY ./airflow/dags /opt/airflow/dags/
COPY ./airflow/airflow.cfg /opt/airflow/airflow.cfg

# Create wait-for-postgres script
RUN echo '#!/usr/bin/env bash' > /wait-for-postgres.sh && \
    echo 'set -e' >> /wait-for-postgres.sh && \
    echo 'host="${1:-postgres}"' >> /wait-for-postgres.sh && \
    echo 'max_retries=30' >> /wait-for-postgres.sh && \
    echo 'retry_count=0' >> /wait-for-postgres.sh && \
    echo '' >> /wait-for-postgres.sh && \
    echo 'until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$host" -U "airflow" -d "airflow" -c "\q" > /dev/null 2>&1 || [ $retry_count -eq $max_retries ]; do' >> /wait-for-postgres.sh && \
    echo '  retry_count=$((retry_count+1))' >> /wait-for-postgres.sh && \
    echo '  echo "PostgreSQL is unavailable - sleeping ($retry_count/$max_retries)"' >> /wait-for-postgres.sh && \
    echo '  sleep 2' >> /wait-for-postgres.sh && \
    echo 'done' >> /wait-for-postgres.sh && \
    echo '' >> /wait-for-postgres.sh && \
    echo 'if [ $retry_count -eq $max_retries ]; then' >> /wait-for-postgres.sh && \
    echo '  echo "PostgreSQL did not become available in time - exiting"' >> /wait-for-postgres.sh && \
    echo '  exit 1' >> /wait-for-postgres.sh && \
    echo 'fi' >> /wait-for-postgres.sh && \
    echo '' >> /wait-for-postgres.sh && \
    echo 'echo "PostgreSQL is up and accepting connections"' >> /wait-for-postgres.sh && \
    chmod +x /wait-for-postgres.sh

# Copy your entrypoint script into the container and make it executable
COPY ./docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Create healthcheck script
RUN echo '#!/usr/bin/env bash' > /healthcheck.sh && \
    echo 'source /app/.venv/bin/activate' >> /healthcheck.sh && \
    echo 'python -c "import nba_data_pull" && curl --fail http://localhost:8080/health' >> /healthcheck.sh && \
    chmod +x /healthcheck.sh

# Switch back to the non-root airflow user for security and runtime
USER airflow

# Ensure that Python can find your package
ENV PYTHONPATH=/app:/app/src:/opt/airflow

# Expose the Airflow webserver port
EXPOSE 8080

# Set the entrypoint and default command
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["webserver"]