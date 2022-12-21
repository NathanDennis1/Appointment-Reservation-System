CREATE TABLE Caregivers (
    Username varchar(255),
    Salt BINARY(16),
    Hash BINARY(16),
    PRIMARY KEY (Username)
);

CREATE TABLE Availabilities (
    Time date,
    Username varchar(255) REFERENCES Caregivers,
    PRIMARY KEY (Time, Username)
);

CREATE TABLE Vaccines (
    Name varchar(255),
    Doses int,
    PRIMARY KEY (Name)
);

CREATE TABLE Patients (
    Username varchar(255),
    Salt BINARY(16),
    Hash BINARY(16),
    PRIMARY KEY (Username)
);

CREATE TABLE Appointments (
    app_ID INT IDENTITY(1, 1), --Unique appointment IDs
    app_date date, --Dates for appointments
    Pusername varchar(255) NOT NULL REFERENCES Patients(Username), --Patient username
    Cusername varchar(255) NOT NULL REFERENCES Caregivers(Username), --Caregiver username
    vaccine_name varchar(255) NOT NULL REFERENCES Vaccines(Name), --Vaccine name
    PRIMARY KEY (app_ID) 
);
