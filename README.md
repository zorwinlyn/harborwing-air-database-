# harborwing-air-database-
1. Project Overview
The HarborWing Air Database is an IT8 Midterm Drill project that uses a relational database to organize airline information. It stores passenger details, reservations, payments, airports, flight schedules, flight legs, and flight costs.

The project uses MySQL Workbench for database design and implementation, and Python with Faker to generate fictional sample data.

2. Objectives
Organize airline information in a relational database.
Reduce duplicate passenger and airport information.
Manage reservations, payments, and connecting flights.
Separate scheduled flight times from actual flight times.
Store flight costs with their validity periods.
Practice SQL queries and automated data generation.
3. Technologies Used
MySQL Server
MySQL Workbench
Python 3
Faker
mysql-connector-python
GitHub
4. Repository Structure
harborwing-air-database/
├── sql/
│   ├── schema.sql
│   ├── example_queries.sql
│   └── verify_counts.sql
├── data-generation/
│   ├── generate_data.py
│   └── requirements.txt
├── harborwing_air.mwb
├── database-diagram.pdf
├── README.md
└── explainer-video.mp4
5. Database Tables
The database contains 11 core tables:

booking_agent: Stores booking agent information.
passenger: Stores passenger details.
reservation: Stores reservation information and passenger references.
payment: Stores payment dates, amounts, and statuses.
airport: Stores airport codes, names, and locations.
flight_schedule: Stores scheduled flight information.
flight_leg: Stores individual flight-leg information and actual flight times.
calendar_date: Stores calendar dates and business-day indicators.
flight_cost: Stores flight costs and their validity periods.
reservation_payment: Connects reservations with payments.
reservation_leg: Connects reservations with flight legs.
6. Database Relationships
One passenger can have many reservations.
One booking agent can handle many reservations, while a reservation may have no booking agent.
Reservations and payments have a many-to-many relationship through reservation_payment.
Reservations and flight legs have a many-to-many relationship through reservation_leg.
Each flight leg belongs to one scheduled flight.
Airports are referenced as flight origins and destinations.
Flight costs are associated with scheduled flights and calendar dates.
Primary keys identify records, while foreign keys connect related tables. Composite primary keys in the linking tables prevent duplicate pairs.

7. Requirements
Before running the project, install:

MySQL Server
MySQL Workbench
Python 3
The MySQL server must be running, and the database connection settings must be correct.

8. How to Create the Database
Open MySQL Workbench.
Connect to your MySQL server.
Open sql/schema.sql.
Execute the SQL statements to create the database and tables.
Confirm that the harborwing_air schema and its 11 core tables exist.
Important: Review the SQL script before executing it. Back up existing data if the script drops or recreates tables.

9. Install Python Dependencies
Open Command Prompt in the repository folder and run:

python -m pip install -r data-generation/requirements.txt
The required libraries are Faker and mysql-connector-python.

10. Generate Sample Data
Open data-generation/generate_data.py.
Configure the MySQL host, port, username, password, and database name.
Save the script.
Run:
python data-generation/generate_data.py
The script is intended to generate fictional sample records and insert them into the database.

After execution, review the output and check for errors. The project requires at least 50 records in every core table.

11. Verify Record Counts
Open sql/verify_counts.sql in MySQL Workbench and execute the query.

Check the results for all 11 tables. Each table must contain at least 50 records to meet the project requirement.

12. Example SQL Queries
The sql/example_queries.sql file contains queries demonstrating how to:

View a reservation with its passenger, booking agent, payments, and flight legs.
Find reservations associated with a particular flight leg.
Find payments linked to a reservation.
Find the applicable flight cost for a flight, aircraft type, and date.
Run the queries in MySQL Workbench and review the results.

13. Design Limitations
Shared payment links do not identify the exact amount allocated to each reservation.
Party size records the number of travelers but does not identify each traveler.
Normalization reduces duplicate information, but retrieving related data requires SQL joins.
Flight-cost validity periods need a policy to prevent overlapping periods.
Flight number is treated as a unique schedule identifier for this project. A production airline system may require a more detailed identifier for individual flight instances.
14. Project Deliverables
harborwing_air.mwb: Editable MySQL Workbench model.
database-diagram.pdf: Exported database diagram.
sql/: Schema creation, example queries, and record-count verification.
data-generation/: Python data-generation script and dependencies.
README.md: Project documentation and setup instructions.
explainer-video.mp4: Project explanation and demonstration.
15. Author Information
Student Name: Zorwinlyn Zambales
Course and Section: BSIT3
Subject: IT8
Project: HarborWing Air Database
