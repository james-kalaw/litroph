# Use the official AWS Lambda Python base image
FROM public.ecr.aws/lambda/python:3.12

# Install system dependencies required by Chromium/Playwright
RUN dnf install -y nss atk cups-libs libXcomposite libXdamage libXrandr libgbm pango alsa-lib \
    libxkbcommon atk libdrm mesa-libgbm

# Install Python requirements
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install boto3

# Install Playwright and the Chromium browser engine
RUN playwright install chromium

# Copy your script into the container
COPY scraper.py ${LAMBDA_TASK_ROOT}

# Tell Lambda which function to trigger
CMD [ "scraper.lambda_handler" ]
