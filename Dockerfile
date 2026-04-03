FROM continuumio/miniconda3

WORKDIR /app

RUN conda install -c conda-forge pythonocc-core -y && \
    pip install flask

COPY . .

EXPOSE 5000

CMD ["python", "server.py"]