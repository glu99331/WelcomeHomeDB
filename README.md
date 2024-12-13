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
1. Fetch the Photo for the Item:
This query retrieves the photo (if available) associated with the item using its `ItemID`.
```
SELECT photo FROM Item WHERE ItemID = %s;

```
This query fetches the photo column for the item with the specified ItemID from the Item table. The photo is stored as a BLOB (binary large object).

### Q3: Find Order Items:
1. Find all items and their locations for the given `orderID`
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
1. Fetch the photo for each item:
```
SELECT photo FROM Item WHERE ItemID = %s;
```
For each item in the order, another query is executed to fetch the item’s photo. If the photo is available, it is processed (converted from a BLOB to a base64-encoded string) so it can be displayed on the web page.

### Q4: Accept Donation:
1. Fetch locations from the Location table:
```
SELECT roomNum, shelfNum FROM Location;
```
This query ensures that the user can choose where the donated items (or their pieces) will be stored by showing all available locations for allocation.
2. Fetch the main categories from the Category table:
```
SELECT DISTINCT mainCategory FROM Category;
```
This query selects all unique (DISTINCT) mainCategory values from the Category table. It is used to present the user with available categories for classifying the donated items.
Categories help classify the items (e.g., furniture, electronics), and the main categories are required for the user to select the appropriate classification for the item.
3. Fetch subcategories from the Category table for each main category:
```
SELECT mainCategory, subCategory FROM Category;
```
4. Check if the donor exists by their userName:
```
SELECT 1 FROM Person WHERE userName = ?;
```
5. Insert a new item into the Item table
```
INSERT INTO Item (iDescription, photo, color, isNew, hasPieces, material, mainCategory, subCategory)
VALUES (?, ?, ?, ?, ?, ?, ?, ?);
```
6. Insert pieces into the Piece table (if the item has pieces):
```
INSERT INTO Piece (ItemID, pieceNum, pDescription, length, width, height, roomNum, shelfNum, pNotes)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
```
7. Insert into the DonatedBy table, linking the item and donor:
```
INSERT INTO DonatedBy (ItemID, userName, donateDate)
VALUES (?, ?, CURDATE());
```

### Q6: Add to current order (shopping)
1. Fetch Categories and Subcategories
```
SELECT DISTINCT mainCategory FROM Item
```
This query retrieves all distinct mainCategory values from the Item table. The goal is to populate the category dropdown menu with the available categories in the system.
```
SELECT DISTINCT subCategory FROM Item
```
This query retrieves all distinct subCategory values from the Item table. It's used to populate the subcategory dropdown menu based on the categories selected.
2. Filter Items Based on Selected Category and Subcategory
SQL to filter items:
```
SELECT i.ItemID, i.iDescription
FROM Item i
LEFT JOIN ItemIn ii ON i.ItemID = ii.ItemID
WHERE i.mainCategory = %s AND i.subCategory = %s AND ii.ItemID IS NULL
```
- SELECT i.ItemID, i.iDescription: This selects the ItemID and description of the items from the Item table.
- LEFT JOIN ItemIn ii ON i.ItemID = ii.ItemID: This performs a left join with the ItemIn table, which tracks which items are part of orders. The left join ensures that all items are returned, even if they don't have an entry in the ItemIn table.
- WHERE i.mainCategory = %s AND i.subCategory = %s: This filters the items based on the selected category (mainCategory) and subcategory (subCategory) from the user input.
- AND ii.ItemID IS NULL: This condition ensures that only items that are not yet ordered are selected. The ii.ItemID IS NULL condition filters out items that are already in the ItemIn table, indicating they have been ordered previously
3. Create a New Order
```
INSERT INTO Ordered (client, supervisor, orderDate) 
VALUES (%s, %s, CURDATE())
```
- INSERT INTO Ordered (client, supervisor, orderDate): This inserts a new record into the Ordered table, which tracks customer orders.
- VALUES (%s, %s, CURDATE()): The client is the logged-in user's ID (current_user.id), the supervisor is hardcoded as "ohmpatel47" in this example (it could be dynamic based on the logged-in supervisor), and the orderDate is set to the current date using CURDATE().

4. Add Items to the Order
```
INSERT INTO ItemIn (ItemID, orderID) 
VALUES (%s, %s)
```
- INSERT INTO ItemIn (ItemID, orderID): This inserts a record into the ItemIn table, which associates items with orders.
- VALUES (%s, %s): The ItemID is the ID of the item being added to the order, and the orderID is the ID of the newly created order (from the previous SQL query).

### Q7: Prepare order
1. Search for Orders Based on Order ID or Client Username
```
SELECT * FROM Ordered WHERE orderID = %s
```
- This query searches for a specific order in the Ordered table by its orderID.
- The user is prompted to search for an order by its ID. The orderID provided by the user is used to fetch the order details from the Ordered table.
```
SELECT * FROM Ordered WHERE client = %s
```
- This query searches for all orders associated with a specific client (userID).
- The user can also search for orders associated with a specific client (identified by their username). The query checks for orders where the client column matches the provided userID.

2. Fetch Items in the Selected Order
```
SELECT i.ItemID, i.iDescription, ii.found
FROM ItemIn ii
JOIN Item i ON ii.ItemID = i.ItemID
WHERE ii.orderID = %s
```
- This query retrieves all items associated with a particular order (orderID).
- The ItemIn table links items with orders, and this query fetches all the items for a specific orderID by joining the Item table to get item descriptions and their current found status (whether the item has been marked as found and ready for delivery).

3. Toggle the found Status of an Item in an Order (Mark Item Ready for Delivery)
```
UPDATE ItemIn SET found = NOT found WHERE ItemID = %s AND orderID = %s
```
- This query toggles the found status of an item. If the item is marked as found, it will be marked as not found, and vice versa. This is used to indicate whether the item is ready for delivery.
- When the user toggles the status of an item (e.g., marking it as found or ready for delivery), this query updates the found column in the ItemIn table for the specific ItemID and orderID.

4. Fetch the Updated found Status for the Item
```
SELECT found FROM ItemIn WHERE ItemID = %s AND orderID = %s
```
- After updating the found status, this query retrieves the updated status of the item to confirm the change.
- This query checks the found status of the specific item after the toggle operation to confirm whether the item is marked as "found" (ready for delivery).

### Q8: User’s tasks: Show all the orders the current user (the user who is logged in) has a relationship with (e.g. as a client, a volunteer working on the order, etc, along with some relevant details)
1. Orders where the user is the Supervisor:
```
SELECT 
    O.orderID, 
    O.orderDate, 
    O.orderNotes, 
    O.supervisor, 
    O.client, 
    D.status, 
    D.date AS deliveryDate,
    'Supervisor' AS role
FROM 
    Ordered O
LEFT JOIN 
    Delivered D ON O.orderID = D.orderID
WHERE 
    O.supervisor = ?;
```
- This part selects orders where the logged-in user is the Supervisor.
- The LEFT JOIN on the Delivered table is used to fetch delivery-related details (status, deliveryDate). If no delivery information is available, the LEFT JOIN ensures the query still returns the order data without errors.
2. Orders where the user is the Client:
```
SELECT 
    O.orderID, 
    O.orderDate, 
    O.orderNotes, 
    O.supervisor, 
    O.client, 
    D.status, 
    D.date AS deliveryDate,
    'Client' AS role
FROM 
    Ordered O
LEFT JOIN 
    Delivered D ON O.orderID = D.orderID
WHERE 
    O.client = ?;
```
- This part selects orders where the logged-in user is the Client.
- Again, the LEFT JOIN on the Delivered table ensures that delivery details (status, deliveryDate) are fetched if available.
3. Orders where the user is the DeliveryPerson:
```
SELECT 
    O.orderID, 
    O.orderDate, 
    O.orderNotes, 
    O.supervisor, 
    O.client, 
    D.status, 
    D.date AS deliveryDate,
    'DeliveryPerson' AS role
FROM 
    Ordered O
LEFT JOIN 
    Delivered D ON O.orderID = D.orderID
WHERE 
    D.userName = ?;
```
- This part selects orders where the logged-in user is the DeliveryPerson.
- The LEFT JOIN on the Delivered table is used to retrieve delivery details (status, deliveryDate).
4. Union of the Three Queries:
```
SELECT 
            O.orderID, 
            O.orderDate, 
            O.orderNotes, 
            O.supervisor, 
            O.client, 
            D.status, 
            D.date AS deliveryDate,
            'Supervisor' AS role
        FROM 
            Ordered O
        LEFT JOIN 
            Delivered D ON O.orderID = D.orderID
        WHERE 
            O.supervisor = ?
        UNION
        SELECT 
            O.orderID, 
            O.orderDate, 
            O.orderNotes, 
            O.supervisor, 
            O.client, 
            D.status, 
            D.date AS deliveryDate,
            'Client' AS role
        FROM 
            Ordered O
        LEFT JOIN 
            Delivered D ON O.orderID = D.orderID
        WHERE 
            O.client = ?
        UNION
        SELECT 
            O.orderID, 
            O.orderDate, 
            O.orderNotes, 
            O.supervisor, 
            O.client, 
            D.status, 
            D.date AS deliveryDate,
            'DeliveryPerson' AS role
        FROM 
            Ordered O
        LEFT JOIN 
            Delivered D ON O.orderID = D.orderID
        WHERE 
            D.userName = ?
        ORDER BY 
            orderDate DESC;
```
The query is a UNION of three parts, each selecting orders for a different role: Supervisor, Client, or DeliveryPerson. Each part of the query returns the same set of columns: order details such as orderID, orderDate, orderNotes, supervisor, client, delivery status (status), delivery date (deliveryDate), and the role of the user associated with the order.

### Q10: Update enabled! Check if the current user is delivering or supervising an order and, if so, allow him/her to change the status of the order
1. Query for Fetching User Orders (get_user_orders)
```
SELECT 
    O.orderID, 
    O.orderDate, 
    O.orderNotes, 
    O.supervisor, 
    O.client, 
    D.status, 
    D.date AS deliveryDate,
    'Supervisor' AS role
FROM 
    Ordered O
LEFT JOIN 
    Delivered D ON O.orderID = D.orderID
WHERE 
    O.supervisor = ?
UNION
SELECT 
    O.orderID, 
    O.orderDate, 
    O.orderNotes, 
    O.supervisor, 
    O.client, 
    D.status, 
    D.date AS deliveryDate,
    'DeliveryPerson' AS role
FROM 
    Ordered O
LEFT JOIN 
    Delivered D ON O.orderID = D.orderID
WHERE 
    D.userName = ?
ORDER BY 
    orderDate DESC;
```
- This query retrieves all orders where the logged-in user is either a supervisor or a delivery person.
- Supervisor check: The query selects orders where the logged-in user is the supervisor of the order by checking if O.supervisor = ? (where ? is replaced with current_user.id).
- DeliveryPerson check: The query also selects orders where the logged-in user is the delivery person for the order by checking if D.userName = ? (again replacing ? with current_user.id).
- The query combines both results using a UNION to include all relevant orders.
2. Query for Updating Order Status (update_order_status)
```
UPDATE Delivered SET status = ? WHERE orderID = ?
```
- This query updates the status of an order that the logged-in user is supervising or delivering. Only those users (supervisors and delivery persons) who are associated with the order can update its status.

### Q11: Prepare data for a year-end report with information like the number of clients served, the number of items of each category donated, and some summary data about how clients
were helped (the kind of information that you might want to include in a grant application)
1. Number of Clients Served
```
SELECT COUNT(DISTINCT userName) AS clients_served 
FROM DonatedBy;
```
- This query calculates the total number of unique clients who have made donations.
- COUNT(DISTINCT userName): This counts the distinct number of unique users (donors) in the DonatedBy table, ensuring that each donor is only counted once, even if they have donated multiple items.
- DonatedBy table: This table links items to donors, so by counting distinct usernames, we can determine how many unique donors (clients) have contributed to the system.
2. Number of Items Donated by Each Category
```
SELECT mainCategory, COUNT(ItemID) AS items_donated 
FROM Item 
GROUP BY mainCategory;
```
- This query groups the items by their main category and counts how many items belong to each category.
- COUNT(ItemID): This counts the number of items in each category by counting the ItemID for each mainCategory.
- GROUP BY mainCategory: This groups the results by mainCategory, allowing us to count items for each category (e.g., clothing, furniture, etc.).
- Item table: This table contains all the items in the system, so by grouping by category, we get the number of items donated in each category.
3. Number of Donations per Month
```
SELECT YEAR(donateDate) AS year, MONTH(donateDate) AS month, COUNT(*) AS donations_per_month
FROM DonatedBy
GROUP BY YEAR(donateDate), MONTH(donateDate)
ORDER BY year DESC, month DESC;
```
- This query calculates the number of donations made each month, grouped by year and month.
- YEAR(donateDate) and MONTH(donateDate): These functions extract the year and month from the donateDate column in the DonatedBy table.
- COUNT(*): This counts the total number of donations made in each month.
- GROUP BY YEAR(donateDate), MONTH(donateDate): This groups the results by year and month, so the total donations per month are calculated.
- ORDER BY year DESC, month DESC: This ensures the results are ordered with the most recent months appearing first.
4. Number of Items in Each Room and Shelf
```
SELECT L.roomNum, L.shelfNum, COUNT(P.pieceNum) AS items_in_shelf
FROM Piece P
JOIN Location L ON P.roomNum = L.roomNum AND P.shelfNum = L.shelfNum
GROUP BY L.roomNum, L.shelfNum;
```
- This query calculates the number of items stored in each room and shelf in the warehouse.
- COUNT(P.pieceNum): This counts the number of pieces in each room and shelf, where each piece corresponds to an item or part of an item.
- JOIN Location L ON P.roomNum = L.roomNum AND P.shelfNum = L.shelfNum: This joins the Piece table with the Location table based on matching roomNum and shelfNum. The Piece table contains information about the individual pieces of an item, and the Location table contains the storage locations (rooms and shelves).
- GROUP BY L.roomNum, L.shelfNum: This groups the results by room and shelf, so we get the count of items in each specific location.
- This helps track where the items are stored and how many items are in each room and shelf.

### Custom Question: Toggleable Role Menu based on Selection
Role switching is a feature that allows a user to switch between different views based on their roles. For example, a user might switch between the "Admin/Staff" view and the "Client/Donor" view based on their selected role.
```
def handle_role_switching(current_user):
    # Handle the role switching
    if request.method == "POST":
        selected_view = request.form.get('view')
        
        # Ensure the user has both Admin/Staff and Client/Donor roles before switching
        if selected_view and ('Admin' in current_user.roles or 'StaffMember' in current_user.roles or 'Supervisor' in current_user.roles or 'DeliveryPerson' in current_user.roles) and \
           ('Client' in current_user.roles or 'Donor' in current_user.roles):
            session['current_role'] = selected_view  # Store the selected view in the session
            current_user.current_role = selected_view  # Update the user object's current_role
            flash(f"Switched to {selected_view} view", "success")
        elif selected_view:  # If a view is selected but the user doesn't have permission
            flash("Invalid role selection or insufficient permissions.", "error")

    # Get the current role from the session, default to Admin/Staff if none selected
    current_role = session.get('current_role', None)

    if current_role is None:
        # Default to 'AdminStaff' if the user has Admin/Staff roles
        if 'Admin' in current_user.roles or 'StaffMember' in current_user.roles or 'Supervisor' in current_user.roles or 'DeliveryPerson' in current_user.roles:
            current_role = 'AdminStaff'  # Default to Admin if the user has admin/staff roles
        else:
            current_role = 'ClientDonor'  # Default to Client view if the user has Client/Donor roles

    # Check if user can toggle based on roles
    can_toggle_role = (
        ('Admin' in current_user.roles or 'StaffMember' in current_user.roles or 'Supervisor' in current_user.roles or 'DeliveryPerson' in current_user.roles) and
        ('Client' in current_user.roles or 'Donor' in current_user.roles)
    )
    
    return current_role, can_toggle_role
```
1. The function handles role switching by checking if the user has the appropriate roles to switch between different views (e.g., Admin/Staff vs Client/Donor).
2. It first checks if the user can switch to the selected role (selected_view) by verifying their current roles. If the user has both Admin/Staff and Client/Donor roles, they can switch.
3. If the selected view is valid, the current_role is updated both in the session and on the User object, which allows the view to be dynamically adjusted based on the user's selected role.
4. It also checks if the user has permission to toggle roles. The can_toggle_role variable is set to True if the user has both Admin/Staff and Client/Donor roles.

Loading User's Roles:
```
cursor.execute("SELECT roleID FROM Act WHERE userName = ?", (user_id,))
roles = [row[0] for row in cursor.fetchall()]
```
- This SQL query fetches the roles for a user from the Act table, which contains the roles associated with a specific user.
- The role switching process makes use of the session to store the current_role selected by the user, allowing them to maintain their role selection across different pages.
Handling Permissions for Access:
In the toggle_item_status route, access is restricted based on user roles:
```
allowed_roles = ['Supervisor', 'StaffMember', 'Admin']
if not any(role in current_user.roles for role in allowed_roles):
    return {"error": "You do not have permission to access this page."}, 403
```
- Before allowing the user to toggle the item status, the code checks if the user has one of the allowed roles: Supervisor, StaffMember, or Admin.
- If the user does not have one of these roles, a 403 (Forbidden) error is returned, and they are prevented from accessing the page.

## Difficulties encountered

1. **Database Integration and Query Optimization**:
   - Integrating the MySQL database with Flask and ensuring efficient query execution was challenging. Queries involving multiple joins, such as fetching item locations and generating reports, required careful optimization to avoid performance bottlenecks.

2. **User Authentication and Role Management**:
   - Implementing a robust authentication system with role-based access control was complex. Ensuring that only authorized users could access certain routes and perform specific actions required meticulous planning and testing.

3. **Dynamic Form Handling**:
   - Managing dynamic forms for adding pieces to items was challenging. Ensuring that the form data was correctly captured and processed on the server side, especially when dealing with multiple pieces, required careful handling of form inputs and validation.

4. **Error Handling and User Feedback**:
   - Providing meaningful error messages and feedback to users was essential for a good user experience. Handling exceptions gracefully and rolling back database transactions in case of errors required thorough testing and debugging.

5. **Responsive UI Design**:
   - Designing a responsive and user-friendly interface that worked well across different devices and screen sizes was challenging. Ensuring that dynamic elements, such as dropdowns and tables, were properly styled and functional required significant effort.


### Lessons Learned

1. **Importance of Database Design**:
   - A well-designed database schema is crucial for the performance and scalability of the application. Proper indexing and normalization can significantly improve query performance and data integrity.

2. **Effective Use of Flask Extensions**:
   - Leveraging Flask extensions, such as Flask-Login for authentication and Flask-WTF for form handling, can simplify the development process and provide robust solutions for common tasks.

3. **Thorough Testing and Debugging**:
   - Comprehensive testing, including unit tests and integration tests, is essential to ensure the reliability and correctness of the application. Debugging tools and logging can help identify and resolve issues quickly.

4. **User-Centric Design**:
   - Designing the application with the end-user in mind leads to a better user experience. Gathering feedback from users and iterating on the design can help create a more intuitive and efficient interface.

5. **Handling Dynamic Data**:
   - Managing dynamic data, such as form inputs and dropdowns, requires careful handling to ensure data integrity and a smooth user experience. JavaScript and AJAX can be used to enhance the interactivity of the application.

6. **Security Best Practices**:
   - Implementing security best practices, such as hashing passwords, validating user inputs, and managing file uploads securely, is crucial to protect the application and its users from potential threats.

By addressing these difficulties and learning from the challenges faced, the project team can improve their development practices and create more robust and user-friendly applications in the future.


## Contributions:
1. Gordon
- Produced the code for Q1-4, Q11 and the Custom Question.
- Also ensured that features were working by testing througly and provided some frontend.
- Contributed to project report.
- Contributed to Project Part 1, 2, 3

2. Satyam
- Added features 8 and 10 along with frontend and role management.
- Added and fixed code security by enforcing Prepared Statements to prevent SQL injection and identified and fixed XSS bug.
- Added helper scripts in SQL to improve the provided schema as an experiment, added indices to minimize retrieval latency, Database and Schema creation and removal and in Python to add dummy data with user's salted and hashed passwords (did not find it possible with just SQL i.e. hashing and salting with SQL) for easy testing and data manipulation and python script to load and verify the photos; uploaded to the database. 
- Added Project manager and dependency management to ensure easy project replication with easy project dependencies installation.
- Contributed to project report.
- Contributed to Project Part 1, 2, 3

3. Ohm
- Added features 6 and 7.