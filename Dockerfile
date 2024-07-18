rROM python:3.11-slim

RUN pip install Wartungsplan

RUN useradd -d /var/lib/wartungsplan wartungsplan

USER wartungsplan

VOLUME /etc/wartungsplan.conf

ENTRYPOINT ["/usr/local/bin/Wartungsplan"]
