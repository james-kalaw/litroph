# LitroPH: Fuel-Efficient Route Optimization Dashboard

## Overview

LitroPH is an end-to-end data engineering and analytics project that helps Filipino motorists estimate the most fuel-efficient and cost-effective driving route using weekly Philippine fuel prices and real-time traffic conditions.

Unlike conventional navigation applications that prioritize only travel time or distance, LitroPH estimates the actual fuel expense of multiple route alternatives by combining:

- Weekly fuel price data from GasWatch PH
- Real-time routing and traffic information from the TomTom Routing API
- User-provided vehicle fuel efficiency (km/L)

The project demonstrates the complete lifecycle of a modern cloud-based data engineering pipeline, from automated data ingestion and transformation to deployment of an interactive analytics application.

---

## Objectives

The project aims to:

- Automate the collection of weekly Philippine fuel prices.
- Build a cloud-native data pipeline using AWS services.
- Transform raw data into analytics-ready datasets using dbt.
- Estimate trip fuel costs using live traffic information.
- Visualize alternative routes and fuel expenses through an interactive dashboard.
- Demonstrate production deployment using AWS EC2.

---

## System Architecture

The project follows the Medallion Architecture commonly used in modern data engineering.

```
                    GasWatch PH
                         │
                         ▼
                 AWS EventBridge
                         │
                         ▼
                  AWS Lambda
             (Playwright Scraper)
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
        Amazon S3             Amazon RDS
      Raw JSON Archive      PostgreSQL Warehouse
              │                     │
              └──────────┬──────────┘
                         ▼
                     dbt Core
             Data Transformation Layer
                         │
                         ▼
                Analytics Tables
                         │
                         ▼
                  Streamlit Dashboard
                         │
                         ▼
              TomTom Routing API
             Real-Time Route Analysis
```

---

## Medallion Architecture

### Bronze Layer

The Bronze layer stores raw data collected from the source without modification.

Contents:

- Weekly fuel prices scraped from GasWatch PH
- Raw JSON files archived in Amazon S3
- Original records loaded into PostgreSQL

Purpose:

- Preserve source data
- Support reproducibility
- Enable future reprocessing

---

### Silver Layer

The Silver layer cleans and structures the raw data.

Transformations performed using dbt include:

- Data validation
- Duplicate removal
- Brand normalization
- Data type standardization
- Schema organization

Purpose:

- Improve data quality
- Prepare data for analytics
- Maintain referential integrity

---

### Gold Layer

The Gold layer contains business-ready datasets consumed by the dashboard.

Examples include:

- Current fuel prices
- National average prices
- Brand comparisons
- Dashboard-ready tables

Purpose:

- Fast analytical queries
- Dashboard visualization
- Business reporting

---

## Technology Stack

### Programming Languages

- Python
- SQL

### Cloud Services

- AWS Lambda
- Amazon EventBridge
- Amazon S3
- Amazon RDS PostgreSQL
- Amazon ECR
- Amazon EC2
- IAM

### Data Engineering

- dbt Core
- PostgreSQL
- pandas

### Web Scraping

- Playwright
- BeautifulSoup

### Frontend

- Streamlit
- Plotly
- Folium
- streamlit-folium

### APIs

- TomTom Routing API
- TomTom Geocoding API

### Deployment

- Ubuntu Server
- systemd
- Nginx
- Git
- GitHub

---

## Project Structure

```
LitroPH/
│
├── app.py
├── scraper.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── dbt/
│   ├── models/
│   ├── macros/
│   ├── seeds/
│   └── dbt_project.yml
│
├── assets/
│
├── notebooks/
│
├── docs/
│
└── README.md
```

---

## Data Pipeline

```
GasWatch PH

↓

AWS EventBridge

↓

AWS Lambda (Docker + Playwright)

↓

Amazon S3 (Raw Archive)

↓

Amazon RDS PostgreSQL

↓

dbt Transformations

↓

Analytics Tables

↓

Streamlit Dashboard

↓

TomTom Routing API

↓

Interactive Route Recommendations
```

---

## Fuel Cost Formula

The application estimates the total fuel expense using the following equation:

\[
\text{Fuel Cost} =
\frac{\text{Distance}}
{\text{Fuel Efficiency} \times \text{Traffic Multiplier}}
\times
\text{Fuel Price}
\]

Where:

- Distance is obtained from the TomTom Routing API.
- Fuel Efficiency is provided by the user.
- Traffic Multiplier adjusts efficiency based on live congestion.
- Fuel Price is retrieved from the transformed warehouse.

This methodology follows general fuel economy principles published by the U.S. Department of Energy and the U.S. Environmental Protection Agency.

---

## Features

- Automated weekly fuel price scraping
- Serverless cloud ingestion
- Raw data archival
- PostgreSQL relational warehouse
- dbt transformation pipeline
- Interactive Streamlit dashboard
- Live TomTom routing
- Alternative route comparison
- Fuel cost estimation
- Responsive Folium maps
- Production deployment on AWS EC2

---

## Deployment

The production application is hosted on:

- Ubuntu Server
- Amazon EC2
- Nginx reverse proxy
- systemd service manager

The Streamlit application runs as a background service and automatically restarts after server reboots.

---

## Future Enhancements

Planned improvements include:

- Vehicle database integration
- Electric vehicle routing
- Historical fuel price analytics
- Fuel price forecasting
- Personalized user profiles
- Nationwide route support

---

## References

- GasWatch PH — https://gaswatchph.com/
- Amazon Web Services — https://aws.amazon.com/
- PostgreSQL — https://www.postgresql.org/
- dbt Core — https://docs.getdbt.com/
- Streamlit — https://streamlit.io/
- TomTom Developer Portal — https://developer.tomtom.com/
- Folium — https://python-visualization.github.io/folium/
- Plotly — https://plotly.com/python/
- U.S. Department of Energy Fuel Economy — https://afdc.energy.gov/
- U.S. Environmental Protection Agency Fuel Economy — https://www.fueleconomy.gov/

---

## Author

**James Andre L. Kalaw**
Data Science and Analytics Student  
Technological Institute of the Phhilippines - Quezon City
Technological Institute of the Philippines

This repository serves as a portfolio project demonstrating cloud-native data engineering, analytics engineering, data warehousing, and interactive geospatial visualization using modern open-source tools and AWS cloud services.
