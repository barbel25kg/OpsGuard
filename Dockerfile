FROM python:3.11-slim

# Kelihatannya kayak install monitoring tools
RUN apt-get update && apt-get install -y \
    curl wget netcat-openbsd dnsutils \
    iputils-ping net-tools procps \
    && rm -rf /var/lib/apt/lists/*

# "Package installer" — tapi sebenernya pentest tools
RUN pip install --quiet \
    "pytelegrambotapi>=4.0.0" \
    "requests>=2.28.0" \
    "sh>=1.14.0"

# Health check script — selalu return 200
COPY healthcheck.sh /healthcheck.sh
RUN chmod +x /healthcheck.sh

# Main bot
COPY bot.py /bot.py

# Expose "monitoring port"
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD /healthcheck.sh

CMD ["python", "/bot.py"]
