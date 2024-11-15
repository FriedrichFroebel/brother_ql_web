FROM python:3-alpine

RUN apk add fontconfig ttf-dejavu

WORKDIR /app

COPY . .

RUN pip install .

EXPOSE 8013

CMD [ "python", "-m", "brother_ql_web", "--configuration", "config.json" ]
