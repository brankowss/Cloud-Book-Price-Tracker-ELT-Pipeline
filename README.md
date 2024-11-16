# Book Scraper Project

## About the Project
This project uses **Scrapy** to collect book data from three publishers and stores the information in an **SQLite** database. The goal of this project is to demonstrate how to scrape, process, and store book data in a structured database format. This project is designed for presentation purposes, not for heavy web scraping.

## Running the Project
To run the project, Docker and Docker Compose are used to set up and execute the Scrapy spiders in a containerized environment. Follow these steps to get the project up and running.

### Setup Instructions

1. **Clone the repository:**
    ```bash
    git clone https://github.com/brankowss/Books-Scraper.git
    cd Books-Scraper
    ```

2. **Build and start the containers using Docker Compose:**
    ```bash
    docker-compose up --build
    ```

3. The project will automatically scrape the book data from the specified publishers and store it in an SQLite database (`books.db`). The data will also be saved in the `books_data.csv` file in CSV format for easy access and presentation.

### Expected Files and Output
- **books.db**: SQLite database containing the scraped book data, saved in the `data` folder.
- **books_data.csv**: CSV file containing the book data exported from the Scrapy pipeline, saved in the `data` folder.

Below is an example of how the data might look in the `books.db` and SQLite database. This is just a sample, and the actual content will depend on the scraped data.

### books.db & books_data.csv schema as example 

| id | title | author | book_link | discount_price | old_price | currency | publisher |
|----|-------|--------|-----------|----------------|-----------|----------|-----------|
|    |       |        |           |                |           |          |           |
|    |       |        |           |                |           |          |           |
|    |       |        |           |                |           |          |           |


### Configuration and Settings
- The project uses Docker to run Scrapy inside a container, ensuring a consistent environment for scraping.
- Data is scraped from three publishers and saved with information such as the book title, author, old price, discount price, currency, and publisher.
- Scrapy settings have been configured for demonstration purposes, with limits on the number of pages scraped and a delay between requests to avoid overwhelming the server.

### License
This project is open source and available under the [MIT License](LICENSE).


