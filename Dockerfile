FROM python:3

RUN apt-get -qq update && \
  # TODO fine tune these requirements
  apt-get install -y exempi && \
  apt-get clean && rm -rf /var/lib/apt/lists/*
RUN pip install poetry

WORKDIR /app
COPY poetry.lock pyproject.toml /app/
RUN poetry config virtualenvs.create false \
  && poetry install --no-dev --no-interaction --no-ansi

COPY . /app

EXPOSE 8080
CMD ["uvicorn", "--host", "0.0.0.0", "--port", "8080", "gallery.server:app"]
