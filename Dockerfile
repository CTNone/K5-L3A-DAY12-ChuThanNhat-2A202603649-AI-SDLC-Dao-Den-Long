FROM python:3.11-slim

WORKDIR /app
COPY . /app
EXPOSE 8000

# The static build must exist at build/web. Run `python tools/build_web.py` first
# or extract the release web zip there.
CMD ["python3", "game.py", "--no-browser", "--port", "8000"]
