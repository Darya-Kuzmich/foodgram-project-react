FROM python:3.8.5
WORKDIR /code
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
RUN chmod +x ./start.sh
CMD ["./start.sh"]