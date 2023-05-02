FROM bmeares/meerschaum

RUN mrsm install plugin compose

COPY --chown=meerschaum ./ /app
WORKDIR /app

RUN mrsm compose show plugins
ENTRYPOINT ["mrsm", "compose", "run"]
