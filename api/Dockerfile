FROM python:3.12-alpine

RUN adduser -D -H bridns
WORKDIR /app
COPY app.py .
USER bridns

EXPOSE 8000
CMD ["python", "-u", "app.py"]
