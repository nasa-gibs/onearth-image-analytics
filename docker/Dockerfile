FROM tiangolo/meinheld-gunicorn-flask:python3.7

COPY ../app /app
RUN pip install requests flask-reverse-proxy-fix imageio scikit-image scikit-learn opencv-python grequests
RUN apt-get update
RUN apt-get -y install vim
COPY config/vimrc /root/.vimrc
COPY config/bashrc /root/.bashrc
