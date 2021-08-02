FROM amd64/python:3.8
ARG DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install runit, python, nginx
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libsm6 libxext6 libxrender-dev unzip \
    make cmake automake gcc g++ pkg-config \
    wget runit nginx \
    python3-numpy python3-opencv python3-h5py \
    libhdf5-serial-dev hdf5-tools libhdf5-dev  \
    zlib1g-dev zip liblapack-dev libblas-dev gfortran

RUN apt -y autoremove && \
    apt -y autoclean && \
    apt -y clean && \
    rm -rf /var/lib/apt/lists/*

# Set timezone
ENV TZ=Asia/Taipei
RUN ln -fs /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone
RUN dpkg-reconfigure -f noninteractive tzdata

# Set locale
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# Copy the requirements.txt file
RUN pip3 install --upgrade pip && cd /app
COPY app/requirements.txt .

# Install requirements packages
RUN pip install setuptools wheel testresources
RUN pip install -r requirements.txt

# Copy the app file
RUN cd /app
COPY app/ .
RUN mv ./lib/* .

# Copy nginx config file
RUN rm -rf /etc/nginx/sites-enabled/default
COPY yolov3-ovms-app.conf /etc/nginx/sites-enabled/default
RUN service nginx restart

# Start Server
CMD [ "python", "yolov3-ovms-app.py", "-p", "44000"]
