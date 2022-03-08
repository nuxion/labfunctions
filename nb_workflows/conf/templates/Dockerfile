FROM {{ data.image }} as builder
# supress pip warning
# For Dev & Debug
# ADD dist/nb_workflows-0.5.0-py3-none-any.whl /tmp

SHELL ["/bin/bash", "-c"]
ADD requirements.txt /tmp
# suppress warning
ENV PATH=$PATH:/root/.local/bin

RUN apt-get -y update \
    && apt-get install -y --no-install-recommends \
       {{ data.build_packages }} \
    && pip install --user -r /tmp/requirements.txt
    # && pip install --user /tmp/nb_workflows-0.5.0-py3-none-any.whl
FROM {{ data.image }} as app
LABEL maintener="{{ data.maintener }}"
RUN groupadd app -g {{ data.user.gid }} \
    && useradd -m -d /home/app app -u {{ data.user.uid }} -g {{ data.user.gid }} \
    && apt-get update -y  \
    && apt-get install -y --no-install-recommends \
    {{ data.final_packages }}
COPY --from=builder --chown=app:app /root/.local /home/app/.local/
COPY --chown=app:app . /app

USER app
WORKDIR /app
ENV PATH=$PATH:/home/app/.local/bin
ENV PYTHONPATH=/app
# CMD ["python3", "run.py"]
