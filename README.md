# WelcomeHome Donation Management System

## Table of Contents
- [Project Overview](#project-overview)
- [Features](#features)
- [Getting Started](#getting-started)
- [Assumptions] (#assumptions)

---

## Project Overview

WelcomeHome Donation Management System is a web application that facilitates tracking and managing donations made to a charity organization. The system enables supervisors and staff members to manage items and donors, record donations, and ensure proper allocation and storage of donated items.

---

## Getting Started

### Setting up the Database
There are two files in the `sql/` folder in this directory:
1. `schema.sql` defines the tables necessary for this application.
2. `inserts.sql` is sample data to test the application.

Copy and paste these scripts into MySQL and run it as needed.

### Running the Flask Application

1. Set the Flask Environment Variables (MAC):
```
export FLASK_APP = WelcomeHomeDB
export FLASK_DEBUG = 1 # if developing
```
2. On Windows, replace the `export` with `set`
3. Ensure there is an `instance` folder outside of this directory. This is where the `config.py` will reside. The expected variables in `config.py` are:
```
MYSQL_HOST = ''
MYSQL_USER = ''
MYSQL_PASSWORD = ''
MYSQL_DB = 'WelcomeHomeDB'
UPLOAD_FOLDER = 'uploads/'
```
4. After verifying steps 1 - 3, run the following command (outside the directory):
```
flask run
```

## Features

- **User Authentication**:
  - Only authorized users can access the system.
  - Different roles (e.g., Supervisor, Staff, Client) with role-based access.
- **Donor Validation**:
  - Ensure donors are registered before recording donations.
- **Donation Tracking**:
  - Record details about donated items, including description, materials, and categorization.
  - Support for items with or without pieces.
- **Dynamic Storage Management**:
  - Validate and allocate `roomNum` and `shelfNum` based on available locations.
- **Responsive UI**:
  - Dynamic and interactive forms for managing items and pieces.
- **Error Handling**:
  - Provide user-friendly error messages for invalid inputs.
- **Submitting Donations**:
  - Toggle the visibility of a `Submit Donation` button based on the role of the current user.

## Assumptions
We make the following assumptions for this application:
1. The set of roles is predefined, and can be dynamic in the sense that new roles can be added to the existing set of roles
2. The combination of (shelfNum, roomNum) has no boundary in terms of items it can hold (though this is probably not a good one to make realistically).
- Location is UNIQUE.
3. There is only one of each item in the Database. That is, items will not appear again through donations.
4. If an item does not has pieces to it, the whole item itself is considered as a piece, with pieceNum = 1.
5. We assume that the Locations and Categories are pre-defined.
6. For a user to have a client and staff role, they must have been assigned a staff role beforehand, and then registered as client.
- We allow the user to register for only a single role, but the only case they can have two is if they were already in the DB beforehand from some sort of Super Admin.
7. We assume that all users can use the `Add to Cart` feature.

## Languages and Frameworks Used
Languages: Python, SQL
Frameworks: Flask
Database: MySQL
Additional Libraries: Flask-Login, Werkzeug, Pillow (for image handling)

## Main Queries Used:

### Q1:
#### Registering a User:
In the register route, users are able to create an account with their details, including username, password, name, email, phone numbers, and role.
1. Password Hashing:
Before storing the user's password in the Person table, it is hashed using the generate_password_hash function. This hashing function uses a cryptographic hash algorithm (usually bcrypt under the hood in Flask) to ensure the password is securely stored. Salt is added to the password before hashing, which is a security measure to prevent rainbow table attacks.

The hashed password is stored in the database:
```
INSERT INTO Person (userName, pwd, fname, lname, email)
VALUES (?, ?, ?, ?, ?);
```
This ensures that even if someone gains access to the database, they cannot retrieve the users' original passwords, as the passwords are stored as cryptographic hashes.

#### Logging In:
In the login route, the user attempts to log in by providing their username and password. The system checks if the provided username exists in the database and if the entered password matches the stored, hashed password.

1. Verify User Identity:
The system first checks if the username exists in the database:
```
SELECT * FROM Person WHERE userName = ?;
```
If the user exists, the system retrieves the user details, including the hashed password.

### Q2: Find Single Item:
#### Find all Locations of Pieces for the Given Item ID:
This query retrieves all the locations (room number, shelf number, shelf name, and shelf description) where the pieces of the specified item are stored.
```
SELECT 
    L.roomNum, 
    L.shelfNum, 
    L.shelf, 
    L.shelfDescription
FROM 
    Piece P
JOIN 
    Location L 
ON 
    P.roomNum = L.roomNum AND P.shelfNum = L.shelfNum
WHERE 
    P.ItemID = ?;

```
`P.roomNum` and `P.shelfNum` are the foreign keys in the Piece table that reference the Location table. The JOIN operation matches these columns to the corresponding roomNum and shelfNum in the Location table.
The query returns the room and shelf details (room number, shelf number, shelf name, shelf description) where the pieces of the item (identified by ItemID) are stored.
#### Fetch the Photo for the Item:
This query retrieves the photo (if available) associated with the item using its `ItemID`.
```
SELECT photo FROM Item WHERE ItemID = %s;

```
This query fetches the photo column for the item with the specified ItemID from the Item table. The photo is stored as a BLOB (binary large object).

### Q3: Find Order Items:
#### Find all items and their locations for the given `orderID`
```
SELECT 
    II.ItemID, 
    P.pieceNum, 
    P.pDescription, 
    L.roomNum, 
    L.shelfNum, 
    L.shelf, 
    L.shelfDescription
FROM 
    ItemIn II
JOIN 
    Piece P ON II.ItemID = P.ItemID
JOIN 
    Location L ON P.roomNum = L.roomNum AND P.shelfNum = L.shelfNum
WHERE 
    II.orderID = ?;
```
The first query is executed to get all pieces of each item and their corresponding locations in the warehouse (room and shelf numbers).
#### Fetch the photo for each item:
```
SELECT photo FROM Item WHERE ItemID = %s;
```
For each item in the order, another query is executed to fetch the item’s photo. If the photo is available, it is processed (converted from a BLOB to a base64-encoded string) so it can be displayed on the web page.

### Q4: Accept Donation:
#### Fetch locations from the Location table:
```
SELECT roomNum, shelfNum FROM Location;
```
This query ensures that the user can choose where the donated items (or their pieces) will be stored by showing all available locations for allocation.
#### Fetch the main categories from the Category table:
```
SELECT DISTINCT mainCategory FROM Category;
```
This query selects all unique (DISTINCT) mainCategory values from the Category table. It is used to present the user with available categories for classifying the donated items.
Categories help classify the items (e.g., furniture, electronics), and the main categories are required for the user to select the appropriate classification for the item.
#### Fetch subcategories from the Category table for each main category:
```
SELECT mainCategory, subCategory FROM Category;
```
#### Check if the donor exists by their userName:
```
SELECT 1 FROM Person WHERE userName = ?;
```
#### Insert a new item into the Item table
```
INSERT INTO Item (iDescription, photo, color, isNew, hasPieces, material, mainCategory, subCategory)
VALUES (?, ?, ?, ?, ?, ?, ?, ?);
```
#### Insert pieces into the Piece table (if the item has pieces):
```
INSERT INTO Piece (ItemID, pieceNum, pDescription, length, width, height, roomNum, shelfNum, pNotes)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
```
#### Insert into the DonatedBy table, linking the item and donor:
```
INSERT INTO DonatedBy (ItemID, userName, donateDate)
VALUES (?, ?, CURDATE());
```