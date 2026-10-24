# Use the official AWS Lambda Python base image
FROM public.ecr.aws/lambda/python:3.12

# Install system dependencies required by Chromium/Playwright
RUN dnf install -y nss atk cups-libs libXcomposite libXcursor libXdamage \
    libXext libXi libXtst libXrandr libXScrnSaver pango alsa-lib \
    libxkbcommon libdrm mesa-libgbm gtk3 at-spi2-atk at-spi2-core \
    xorg-x11-server-Xvfb


# Install the pipeline requirements (scraper + loader); boto3 is only needed for the S3 archive on AWS
COPY requirements-pipeline.txt .
RUN pip install -r requirements-pipeline.txt boto3

# Install Playwright Chromium to a fixed path accessible by any user
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN playwright install chromium
RUN chmod -R 777 /ms-playwright

# Copy your script into the container
COPY scraper.py ${LAMBDA_TASK_ROOT}

# Tell Lambda which function to trigger
CMD [ "scraper.lambda_handler" ]
