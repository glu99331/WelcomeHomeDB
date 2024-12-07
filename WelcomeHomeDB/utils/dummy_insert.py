import mysql.connector
from werkzeug.security import generate_password_hash
from pathlib import Path


images = ["chair.jpeg", "table.jpeg", "laptop.jpg", "shirt.jpg", "book.jpg"]


def get_binary_image(image):
    return Path(f"images/{image}").read_bytes()


def insert_dummy_data():
    # Database connection
    db = mysql.connector.connect(
        host="localhost",
        user="welcomehomeadmin",
        password="1234",
        database="WelcomeHomeDB",
    )
    cursor = db.cursor(prepared=True)

    try:
        # Category inserts
        categories = [
            (
                "Furniture",
                "Chair",
                "Various types of chairs including office and dining chairs",
            ),
            ("Furniture", "Table", "Dining and work tables of different materials"),
            ("Electronics", "Laptop", "Various brands and configurations of laptops"),
            ("Clothing", "Shirts", "Casual and formal shirts for all genders"),
            ("Books", "Fiction", "Fictional novels and short stories"),
        ]
        cursor.executemany(
            "INSERT INTO Category (mainCategory, subCategory, catNotes) VALUES (?, ?, ?)",
            categories,
        )

        # Item inserts
        items = [
            (
                "Office Chair with wheels",
                "Black",
                get_binary_image(images[0]),
                True,
                False,
                "Plastic and Fabric",
                "Furniture",
                "Chair",
            ),
            (
                "Dining Table with 4 legs",
                "Brown",
                get_binary_image(images[1]),
                True,
                True,
                "Wood",
                "Furniture",
                "Table",
            ),
            (
                "HP EliteBook Laptop",
                "Silver",
                get_binary_image(images[2]),
                True,
                False,
                "Metal and Plastic",
                "Electronics",
                "Laptop",
            ),
            (
                "Men's Cotton Shirt",
                "Blue",
                get_binary_image(images[3]),
                True,
                False,
                "Cotton",
                "Clothing",
                "Shirts",
            ),
            (
                "Mystery Novel: The Lost Symbol",
                "N/A",
                get_binary_image(images[4]),
                False,
                False,
                "Paper",
                "Books",
                "Fiction",
            ),
        ]
        cursor.executemany(
            """INSERT INTO Item (iDescription, color, photo, isNew, hasPieces, material, 
               mainCategory, subCategory) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            items,
        )

        # Person inserts with hashed passwords
        persons = [
            (
                "johnDoe",
                generate_password_hash("password123"),
                "John",
                "Doe",
                "john.doe@example.com",
            ),
            (
                "janeSmith",
                generate_password_hash("password456"),
                "Jane",
                "Smith",
                "jane.smith@example.com",
            ),
            (
                "adminUser",
                generate_password_hash("adminPassword"),
                "Admin",
                "User",
                "admin@example.com",
            ),
        ]
        cursor.executemany(
            "INSERT INTO Person (userName, pwd, fname, lname, email) VALUES (?, ?, ?, ?, ?)",
            persons,
        )

        # PersonPhone inserts
        phones = [
            ("johnDoe", "123-456-7890"),
            ("janeSmith", "987-654-3210"),
            ("adminUser", "555-555-5555"),
        ]
        cursor.executemany(
            "INSERT INTO PersonPhone (userName, phone) VALUES (?, ?)", phones
        )

        # DonatedBy inserts
        donations = [(1, "johnDoe", "2024-11-01"), (2, "janeSmith", "2024-11-02")]
        cursor.executemany(
            "INSERT INTO DonatedBy (ItemID, userName, donateDate) VALUES (?, ?, ?)",
            donations,
        )

        # Role inserts
        roles = [
            ("Supervisor", "Oversees all operations and order assignments"),
            ("Client", "Recipient of items or services"),
            ("DeliveryPerson", "Handles item deliveries"),
            ("StaffMember", "General staff member with access to operational features"),
        ]
        cursor.executemany(
            "INSERT INTO Role (roleID, rDescription) VALUES (?, ?)", roles
        )

        # Act inserts
        acts = [
            ("johnDoe", "Supervisor"),
            ("janeSmith", "Client"),
            ("adminUser", "DeliveryPerson"),
        ]
        cursor.executemany("INSERT INTO Act (userName, roleID) VALUES (?, ?)", acts)

        # Location inserts
        locations = [
            (1, 1, "A1", "Shelf in Room 1, Section A"),
            (1, 2, "A2", "Shelf in Room 1, Section B"),
            (2, 1, "B1", "Shelf in Room 2, Section A"),
        ]
        cursor.executemany(
            "INSERT INTO Location (roomNum, shelfNum, shelf, shelfDescription) VALUES (?, ?, ?, ?)",
            locations,
        )


        pieces = [
            # Office Chair (Single Piece)
            (1, 1, "Complete Office Chair", 60, 60, 120, 1, 1, "Fully assembled chair"),
            # Dining Table (Multiple Pieces)
            (2, 1, "Table Top", 200, 100, 5, 1, 1, "Main surface"),
            (2, 2, "Table Leg 1", 10, 10, 73, 1, 2, "Front left leg"),
            (2, 3, "Table Leg 2", 10, 10, 73, 1, 2, "Front right leg"),
            (2, 4, "Table Leg 3", 10, 10, 73, 1, 2, "Back left leg"),
            (2, 5, "Table Leg 4", 10, 10, 73, 1, 2, "Back right leg"),
            # Laptop (Single Piece)
            (3, 1, "HP EliteBook Complete", 35, 25, 2, 2, 1, "With charger"),
            # Shirt (Single Piece)
            (4, 1, "Cotton Shirt", 30, 20, 1, 1, 2, "Freshly laundered"),
            # Book (Single Piece)
            (5, 1, "The Lost Symbol Book", 20, 15, 3, 2, 1, "Hardcover edition"),
        ]
        cursor.executemany(
            """INSERT INTO Piece (ItemID, pieceNum, pDescription, length, width, height, 
            roomNum, shelfNum, pNotes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            pieces,
        )

        # Ordered inserts
        orders = [
            (1, "2024-01-15", "Priority delivery needed", "johnDoe", "janeSmith"),
            (2, "2024-01-16", "Standard delivery", "johnDoe", "adminUser"),
            (3, "2024-01-17", "Multiple items order", "johnDoe", "janeSmith"),
        ]
        cursor.executemany(
            """INSERT INTO Ordered (orderID, orderDate, orderNotes, supervisor, client) 
            VALUES (?, ?, ?, ?, ?)""",
            orders,
        )

        # ItemIn inserts
        item_orders = [
            (1, 1, True),  # Chair in order 1, found
            (2, 1, False),  # Table in order 1, not found
            (3, 2, True),  # Laptop in order 2, found
            (4, 3, True),  # Shirt in order 3, found
            (5, 3, True),  # Book in order 3, found
        ]
        cursor.executemany(
            "INSERT INTO ItemIn (ItemID, orderID, found) VALUES (?, ?, ?)", item_orders
        )

        # Delivered inserts
        deliveries = [
            ("adminUser", 1, "Delivered", "2024-01-16"),
            ("adminUser", 2, "In Transit", "2024-01-17"),
            ("adminUser", 3, "Pending", "2024-01-17"),
        ]
        cursor.executemany(
            """INSERT INTO Delivered (userName, orderID, status, date) 
            VALUES (?, ?, ?, ?)""",
            deliveries,
        )

        db.commit()
        print("Data inserted successfully!")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        db.rollback()
    finally:
        cursor.close()
        db.close()


if __name__ == "__main__":
    insert_dummy_data()
