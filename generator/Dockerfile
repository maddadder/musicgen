# Use an official PyTorch GPU-enabled image as a parent image
FROM pytorch/pytorch

# Set the working directory in the container
WORKDIR /usr/src/app

# export timezone - for python3.9-dev install
ENV TZ=US/Pacific

# place timezone data /etc/timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install FFmpeg
RUN apt-get update && \
    apt-get install --yes ffmpeg libsndfile1-dev

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run consumer.py when the container launches
CMD ["python", "./consumer.py"]
