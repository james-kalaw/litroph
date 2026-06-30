# Use the official AWS Lambda Python base image (Amazon Linux 2023)
FROM public.ecr.aws/lambda/python:3.12

# Install ALL system dependencies required by Chromium/Playwright on Amazon Linux
RUN dnf install -y nss atk cups-libs libXcomposite libXcursor libXdamage \
    libXext libXi libXtst libXrandr libXScrnSaver pango alsa-lib \
    libxkbcommon libdrm mesa-libgbm gtk3 at-spi2-atk at-spi2-core \
    xorg-x11-server-Xvfb

# Install Python requirements
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install boto3

# Install Playwright and the Chromium browser engine globally
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN playwright install chromium

# Copy your script into the container
COPY scraper.py ${LAMBDA_TASK_ROOT}

# Tell Lambda which function to trigger
CMD [ "scraper.lambda_handler" ]