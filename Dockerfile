FROM python:3.8.10-slim as builder
# supress pip warning
SHELL ["/bin/bash", "-c"]
ADD requirements/requirements_client.txt /tmp/requirements.txt
COPY . /tmp/package/

# suppress warning
ENV PATH=$PATH:/root/.local/bin 
WORKDIR /tmp/package

RUN apt-get -y update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    libopenblas-dev \
    git  \
    && python -m pip install --upgrade pip \
    && python setup.py install 

# COPY --chown=root:root . /app/
# WORKDIR /app
# RUN python /app/setup.py install --user


FROM python:3.8.10-slim as app
LABEL maintener="Xavier Petit <nuxion@gmail.com>"
RUN groupadd app -g 991 \
    && useradd -m -d /home/app app -u 1000 -g 991 \
    && apt-get update -y  \
    && apt-get install -y --no-install-recommends \
    vim-tiny \
    && mkdir -p /app/workflows \
    && mkdir -p /app/outputs \
    && chown -R app:app /app
COPY --from=builder --chown=app:app /root/.local /home/app/.local/
COPY --chown=app:app . /app
RUN  mv /app/nb.bin /home/app/.local/bin/nb \
     && chmod +x /home/app/.local/bin/nb

USER app
WORKDIR /app
 
ENV PATH=$PATH:/home/app/.local/bin
ENV PYTHONPATH=/app
CMD ["nb"]
