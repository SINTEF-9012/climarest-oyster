FROM python:3.11
EXPOSE 14858
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY ./app/quiberon_bay.geojson /app/quiberon_bay.geojson
COPY ./app/main.py /app/main.py
CMD ["streamlit", "run", "app/main.py", "--server.port=14858", "--server.address=0.0.0.0", "--server.headless=true"]
