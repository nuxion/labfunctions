FROM python:3.8.10-slim as builder
# supress pip warning
SHELL ["/bin/bash", "-c"]
ADD requirements.txt /tmp
ADD dist/nb_workflows-0.8.0a5-py3-none-any.whl /tmp
# suppress warning
ENV PATH=$PATH:/root/.local/bin 

RUN apt-get -y update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    && pip install --user -r /tmp/requirements.txt \
    && pip install --user /tmp/nb_workflows-0.8.0a5-py3-none-any.whl
# COPY --chown=root:root . /app/
# WORKDIR /app
# RUN python /app/setup.py install --user


FROM python:3.8.10-slim as app
LABEL maintener="Xavier Petit <nuxion@gmail.com>"
RUN groupadd app -g 1090 \
    && useradd -m -d /home/app app -u 1089 -g 1090 \
    && apt-get update -y  \
    && apt-get install -y --no-install-recommends \
    vim-tiny git\
    && mkdir -p /app/workflows \
    && mkdir -p /app/outputs \
    && chown -R app:app /app
COPY --from=builder --chown=app:app /root/.local /home/app/.local/ 

USER app
WORKDIR /app
ENV PATH=$PATH:/home/app/.local/bin
# ENV PYTHONPATH=/app
CMD ["nb"]
