FROM python:3.12-alpine

WORKDIR / 

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app app

EXPOSE 80/tcp

ENTRYPOINT ["flask", "--app", "app", "run"]
CMD ["--host","0.0.0.0", "--port", "80"]
