FROM python:3.8.10-slim as builder
ENV DEBIAN_FRONTEND=noninteractive
USER root
SHELL ["/bin/bash", "-c"]
ADD requirements/requirements.txt /tmp/requirements.txt
# add root/local/bin to path to suppress pip warning
ENV PATH=$PATH:/root/.local/bin
ENV DEBIAN_FRONTEND=noninteractive


RUN apt-get update -y && apt-get install -y --no-install-recommends \
   build-essential libopenblas-dev git \
   && pip install --user -r /tmp/requirements.txt


FROM python:3.8.10-slim as app
MAINTAINER "Xavier Petit <nuxion@gmail.com>"
USER root
SHELL ["/bin/bash", "-c"]
ENV DEBIAN_FRONTEND=noninteractive

RUN groupadd app -g 1090 \
    && useradd -m -d /home/app app -u 1089 -g 1090

COPY --from=builder --chown=app:app /root/.local /home/app/.local/
COPY --chown=app:app . /app
RUN  mv /app/nb.bin /home/app/.local/bin/nb \
     && chmod +x /home/app/.local/bin/nb

USER app
WORKDIR /app
ENV PATH=$PATH:/home/app/.local/bin
ENV PYTHONPATH=/app
CMD ["nb"]
