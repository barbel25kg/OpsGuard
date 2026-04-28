FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl wget netcat-openbsd dnsutils \
    iputils-ping net-tools procfs \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --quiet \
    "pytelegrambotapi>=4.0.0" \
    "requests>=2.28.0" \
    "sh>=1.14.0"

COPY healthcheck.sh /healthcheck.sh
RUN chmod +x /healthcheck.sh

COPY bot.py /bot.py

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD /healthcheck.sh

CMD ["python", "/bot.py"]
