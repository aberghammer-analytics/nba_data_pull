# Use the official Airflow image as base
FROM apache/airflow:2.6.3-python3.11
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Switch to root for installing system dependencies
USER root

# Install system dependencies needed for building packages and general tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        git \
        curl \
        ca-certificates \
        gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the project into the image
ADD . /app

# Set working directory for the application code
WORKDIR /app

# Copy essential project files first for caching benefits
COPY ./pyproject.toml ./README.md /app/
# Copy the entire src directory containing your package code
COPY ./src /app/src/

RUN uv venv /app/.venv

# Install the package and its dependencies using uv
SHELL ["/bin/bash", "-c"]
RUN source /app/.venv/bin/activate && \
    uv pip install -e . && \
    uv pip freeze > /tmp/installed_packages.txt && \
    echo "Installed packages:" && cat /tmp/installed_packages.txt

# Create directories that Airflow requires and set proper permissions
RUN mkdir -p /opt/airflow/dags /opt/airflow/logs /opt/airflow/data/meta \
    /opt/airflow/data/logs/inventory_logs /opt/airflow/data/logs/PLAYER \
    /opt/airflow/data/logs/GAME /opt/airflow/data/logs/SEASON && \
    chown -R airflow:root /opt/airflow

# Copy Airflow DAGs and custom configuration into the appropriate directories
COPY ./airflow/dags /opt/airflow/dags/
COPY ./airflow/airflow.cfg /opt/airflow/airflow.cfg

# Copy your entrypoint script into the container and make it executable
COPY ./docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Switch back to the non-root airflow user for security and runtime
USER airflow

# Ensure that Python can find your package by adding /app and /app/src to PYTHONPATH
ENV PYTHONPATH=/app:/app/src:/app/.venv/lib/python3.11/site-packages:${PYTHONPATH}

# Expose the Airflow webserver port so it can be accessed externally
EXPOSE 8080

# Set the entrypoint and default command to run the Airflow webserver
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["webserver"]
