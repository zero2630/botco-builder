FROM python:3.10

RUN mkdir /botco_fastapi

WORKDIR /botco_fastapi

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN chmod a+x app.sh