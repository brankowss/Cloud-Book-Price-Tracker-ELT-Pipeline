FROM python:3.10-slim

# Set the working directory to the folder where the project is located
WORKDIR /usr/src/app

# Copy the requirements.txt file to the working directory
COPY requirements.txt .

# Install all required dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the remaining files to the directory
COPY . .

# Copy run_spiders.sh and set executable permissions
COPY run_spiders.sh .
RUN chmod +x run_spiders.sh

# Run the script to start all spiders
CMD ./run_spiders.sh








