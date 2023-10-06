FROM python:3
ADD requirements.txt /
RUN pip install -r requirements.txt
ADD main.py /
CMD [ "python", "./main.py", "-c https://unifi:8443", "-u svc_rebootap" ]
