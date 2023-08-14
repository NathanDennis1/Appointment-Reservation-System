# SQL-and-Python-Database-Project-Assignment

Python and SQL Database project for CSE414 at UW. Created a vaccine scheduler which was connected to a Microsoft Azure Database. Caregivers and Patients create accounts, where they both have different functions. Caregivers are able to upload their availability, show their appointments, and revise vaccine counts. Patients can reserve or cancel appointments, search the caregivers schedule and show their appointments. All reservations made by patients, all availabilites made by caregivers, and all vaccines and doses are in the Azure database.

- Caregiver.py: Data model for caregivers
- Patient.py: Data model for users
- Vaccine.py: Data model for vaccines
- Scheduler.py: Main runner for command-line interface, contains many functions allowing users/caregivers to create accounts and login, then search for schedules and reserve if available.
- create.sql: SQL statements to create the tables for the database
- ConnectionManager.py: Connections for database

