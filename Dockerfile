FROM python:3.10-alpine

# Setup some labels for the Image
LABEL de.uol.wisdom-oss.vendor="Project group WISdoM 2.0"
LABEL de.uol.wisdom-oss.maintainer="wisdom@uol.de"
LABEL de.uol.wisdom-oss.service_name="auth-service"

# Add a user to the service who will execute the code
RUN addgroup --system auth-service && \
    adduser --home /opt/auth-service --system --gecos "" auth-service --ingroup auth-service

# Install the build essentials package
RUN apk add --update alpine-sdk libffi-dev cargo
# Copy the source code to the image
COPY src /opt/auth-service

# Copy the requirements file to the image
COPY requirements.txt /opt/auth-service

# Install the requirements
RUN python -m pip install -r /opt/auth-service/requirements.txt
# Install the build essentials package
RUN apk del alpine-sdk libffi-dev cargo
# Set the working directory to the service folder
WORKDIR /opt/auth-service
# Change to the service user
USER auth-service
# Expose the port used by uvicorn
EXPOSE 5000

ENTRYPOINT ["python", "service.py"]

