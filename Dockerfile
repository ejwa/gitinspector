FROM python:3.7
# Set the working directory.
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY . /usr/src/app
ENV PYTHONPATH="/usr/src/app:${PYTHONPATH}"
RUN pip install pipenv
RUN pipenv lock --requirements > requirements.txt
RUN pip install -r requirements.txt
RUN chmod -R 777 /usr/src/app/gitinspector.py
ENTRYPOINT ["/usr/src/app/gitinspector.py"]
