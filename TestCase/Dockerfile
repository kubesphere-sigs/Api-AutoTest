FROM python:3.7.3

WORKDIR .

ADD . .

RUN pip install -r requirements.txt

CMD ["pytest", "-q","TestCase/testUser.py","--alluredir","allure-results"]
