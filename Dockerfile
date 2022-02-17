FROM python:3.8.10-slim as builder
# supress pip warning
SHELL ["/bin/bash", "-c"]
ADD requirements.txt /tmp
# suppress warning
ENV PATH=$PATH:/root/.local/bin 

RUN apt-get -y update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    libopenblas-dev \
    git \
    && pip install --user -r /tmp/requirements.txt

FROM python:3.8.10-slim as app
LABEL maintener="Xavier Petit <nuxion@gmail.com>"
RUN groupadd app -g 1090 \
    && useradd -m -d /home/app app -u 1089 -g 1090 \
    && apt-get update -y  \
    && apt-get install -y --no-install-recommends \
    vim-tiny
    # ssh openssh-client rsync libopenblas-base vim-tiny
COPY --from=builder --chown=app:app /root/.local /home/app/.local/
COPY --chown=app:app . /app
COPY --chown=app:app ./scripts/nb.bin /home/app/.local/bin/nb

USER app
WORKDIR /app
# RUN mkdir /app/multiproc
# ENV prometheus_multiproc_dir=multiproc
# RUN python -m spacy download es_core_news_sm \
# EXPOSE 3333
ENV PATH=$PATH:/home/app/.local/bin
ENV PYTHONPATH=/app
CMD ["nb"]
