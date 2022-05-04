FROM python:3.10-slim
# Set some labels
LABEL de.uol.wisdom-oss.vendor="WISdoM 2.0 Project Group"
LABEL de.uol.wisdom-oss.maintainer="wisdom@uol.de"
LABEL de.uol.wisdom-oss.service-name="authorization-service"

WORKDIR /opt/service
COPY . /opt/service
RUN python -m pip install --upgrade pip wheel
RUN python -m pip install -r /opt/service/requirements.txt
RUN python -m pip install gunicorn[gevent]

EXPOSE 5000
ENTRYPOINT ["gunicorn", "-cgunicorn.config.py", "api:service"]