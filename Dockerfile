FROM python:3.9
# Setup some labels for the Image
LABEL de.uol.wisdom-oss.vendor="Project group WISdoM 2.0"
LABEL de.uol.wisdom-oss.maintainer="wisdom@uol.de"
LABEL de.uol.wisdom-oss.service_name="auth-service"
# Add a user to the service who will execute the code
RUN addgroup --system auth-service && \
    adduser --home /opt/auth-service --system --gecos "" auth-service --ingroup auth-service
# Copy the source code to the image
COPY . /opt/auth-service
# Copy the requirements file to the image
COPY requirements.txt /opt/auth-service
# Install the requirements
RUN python -m pip install -r /opt/auth-service/requirements.txt
# Install hypercorn as http server
RUN python -m pip install hypercorn[uvloop]
# Set the working directory to the service folder
WORKDIR /opt/auth-service
# Change to the service user
USER auth-service
# Expose the port used by uvicorn
EXPOSE 5000
# Set the entrypoint to the service.py
ENTRYPOINT ["hypercorn", "-b0.0.0.0:5000", "-w16", "-kuvloop", "api:auth_service_rest"]

