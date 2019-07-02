FROM tiangolo/meinheld-gunicorn-flask:python3.7

COPY ./app /app
RUN pip install requests flask-reverse-proxy-fix imageio scikit-image scikit-learn 
RUN pip install opencv-python grequests plotly owslib xmltodict matplotlib 
RUN pip install scipy aiohttp
RUN apt-get update
RUN apt-get -y install vim
COPY docker/config/vimrc /root/.vimrc
COPY docker/config/bashrc /root/.bashrc
