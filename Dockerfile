# Simple dockerfile for gitinspector
# Usage:
# To build the image, execute the following command in the repository of gitinspector. 
# docker build -t gitinspector . 
#
# Run the following commands in the repository you want to analyze:
# docker run --rm -it -v $(pwd):/repo gitinspector -f cs,fs -m -r -T -w /repo -F json > myresults.json
# docker run --rm -it gitinspector --help 


FROM python:3.7-alpine

WORKDIR /app
COPY . .

RUN apk update && apk add git

ENTRYPOINT ["python3", "/app/gitinspector.py"]
