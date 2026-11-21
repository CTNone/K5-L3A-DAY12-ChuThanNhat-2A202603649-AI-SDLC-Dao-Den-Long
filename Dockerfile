FROM python:3.11-slim

WORKDIR /app
ARG WEB_ZIP=dist/dao-den-long-web-v1.0.1.zip
COPY tools/serve_web.py /app/serve_web.py
COPY ${WEB_ZIP} /tmp/web.zip
RUN python -c "import zipfile; zipfile.ZipFile('/tmp/web.zip').extractall('/app/build/web')" && rm /tmp/web.zip

EXPOSE 8000
CMD ["python", "serve_web.py", "--dir", "build/web", "--host", "0.0.0.0", "--port", "8000", "--no-browser"]
