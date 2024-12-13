import mysql.connector
from werkzeug.security import generate_password_hash
from pathlib import Path

images = ["sofa.jpg", "bedframe.jpg", "tv.png", "microwave_oven.png", "dining_table.png"]


def get_binary_image(image):
    return Path(f"images/{image}").read_bytes()

def create_connection():
    return mysql.connector.connect(
        host="localhost",
        user="welcomehomeadmin",
        password="1234",
        database="WelcomeHomeDB",
    )


def insert_dummy_data():
    conn = create_connection()
    cursor = conn.cursor(prepared=True)

    try:
        # Insert Categories
        categories = [
            ("Furniture", "Sofa", "Living room furniture"),
            ("Furniture", "Bed", "Bedroom furniture"),
            ("Electronics", "TV", "Entertainment devices"),
            ("Kitchen", "Appliances", "Kitchen equipment"),
            ("Furniture", "Table", "Dining and study tables"),
            ("Decor", "Paintings", "Wall decorations"),
        ]
        cursor.executemany(
            "INSERT INTO Category (mainCategory, subCategory, catNotes) VALUES (?, ?, ?)",
            categories,
        )

        # Insert Persons with hashed passwords
        persons = [
            ("john_admin", "admin123", "John", "Smith", "john@example.com"),
            ("sarah_vol", "vol123", "Sarah", "Johnson", "sarah@example.com"),
            ("mike_client", "client123", "Mike", "Brown", "mike@example.com"),
            ("lisa_delivery", "delivery123", "Lisa", "Davis", "lisa@example.com"),
            ("tom_super", "super123", "Tom", "Wilson", "tom@example.com"),
            ("emma_donor", "donor123", "Emma", "Clark", "emma@example.com"),
            ("alex_staff", "staff123", "Alex", "Turner", "alex@example.com"),
            ("jane_multi", "multi123", "Jane", "Cooper", "jane@example.com"),
        ]
        for person in persons:
            hashed_pwd = generate_password_hash(person[1])
            cursor.execute(
                "INSERT INTO Person (userName, pwd, fname, lname, email) VALUES (?, ?, ?, ?, ?)",
                (person[0], hashed_pwd, person[2], person[3], person[4]),
            )

        # Insert Phone Numbers
        phones = [
            ("john_admin", "555-0101"),
            ("sarah_vol", "555-0102"),
            ("mike_client", "555-0103"),
            ("lisa_delivery", "555-0104"),
            ("tom_super", "555-0105"),
            ("emma_donor", "555-0106"),
            ("alex_staff", "555-0107"),
            ("jane_multi", "555-0108"),
        ]
        cursor.executemany(
            "INSERT INTO PersonPhone (userName, phone) VALUES (?, ?)", phones
        )

        # Insert Roles
        roles = [
            ("Admin", "System administrator"),
            ("Volunteer", "Helps with operations"),
            ("Client", "Receives furniture"),
            ("DeliveryPerson", "Handles deliveries"),
            ("Supervisor", "Oversees operations"),
            ("Donor", "Donates items"),
            ("Staff", "Regular employee"),
        ]
        cursor.executemany(
            "INSERT INTO Role (roleID, rDescription) VALUES (?, ?)", roles
        )

        # Insert Role Assignments
        acts = [
            ("john_admin", "Admin"),
            ("sarah_vol", "Volunteer"),
            ("mike_client", "Client"),
            ("lisa_delivery", "DeliveryPerson"),
            ("tom_super", "Supervisor"),
            ("emma_donor", "Donor"),
            ("alex_staff", "Staff"),
            ("jane_multi", "Admin"),
            ("jane_multi", "Client"),
        ]
        cursor.executemany("INSERT INTO Act (userName, roleID) VALUES (?, ?)", acts)

        # Insert Locations
        locations = [
            (1, 1, "A1", "Front storage"),
            (1, 2, "A2", "Back storage"),
            (2, 1, "B1", "Electronics section"),
            (2, 2, "B2", "Furniture section"),
            (3, 1, "C1", "Kitchen items"),
        ]
        cursor.executemany(
            "INSERT INTO Location (roomNum, shelfNum, shelf, shelfDescription) VALUES (?, ?, ?, ?)",
            locations,
        )

        # Insert Items
        items = [
            (
                "Modern 3-seater sofa",
                "Grey",
                False,
                True,
                "Fabric",
                "Furniture",
                "Sofa",
                get_binary_image(images[0])

            ),
            ("Queen size bed frame", "Brown", True, True, "Wood", "Furniture", "Bed", get_binary_image(images[1])),
            ("50-inch Smart TV", "Black", True, False, "Plastic", "Electronics", "TV", get_binary_image(images[2])),
            ("Microwave oven", "Silver", True, False, "Metal", "Kitchen", "Appliances", get_binary_image(images[3])),
            ("Dining table", "Oak", False, True, "Wood", "Furniture", "Table", get_binary_image(images[4])),
        ]
        cursor.executemany(
            "INSERT INTO Item (iDescription, color, isNew, hasPieces, material, mainCategory, subCategory, photo) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            items,
        )

        # Insert Pieces
        pieces = [
            (1, 1, "Sofa base", 200, 90, 85, 1, 1, "Main piece"),
            (1, 2, "Cushions", 60, 60, 15, 1, 2, "Set of 3"),
            (2, 1, "Headboard", 160, 10, 120, 2, 2, "Wooden"),
            (2, 2, "Bed frame", 200, 160, 30, 2, 2, "With slats"),
            (3, 1, '50-inch Smart TV Unit', 112, 71, 8, 2, 1, 'Complete unit'),
            (4, 1, 'Microwave oven Unit', 50, 40, 30, 3, 1, 'Complete unit'),
            (5, 1, "Table top", 150, 90, 5, 1, 2, "Solid wood"),
            (5, 2, "Table legs", 10, 10, 75, 1, 2, "Set of 4"),
        ]
        cursor.executemany(
            "INSERT INTO Piece (ItemID, pieceNum, pDescription, length, width, height, roomNum, shelfNum, pNotes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            pieces,
        )

        # Insert Donations
        donations = [
            (1, "emma_donor", "2024-01-15"),
            (2, "emma_donor", "2024-01-16"),
            (3, "jane_multi", "2024-01-17"),
            (4, "emma_donor", "2024-01-18"),
            (5, "jane_multi", "2024-01-19"),
        ]
        cursor.executemany(
            "INSERT INTO DonatedBy (ItemID, userName, donateDate) VALUES (?, ?, ?)",
            donations,
        )

        # Insert Orders
        orders = [
            ("2024-02-01", "Delivery after 5pm", "tom_super", "mike_client"),
            ("2024-02-02", "Weekend delivery", "tom_super", "jane_multi"),
        ]
        cursor.executemany(
            "INSERT INTO Ordered (orderDate, orderNotes, supervisor, client) VALUES (?, ?, ?, ?)",
            orders,
        )

        # Insert Items in Orders
        items_in_orders = [(1, 1, True), (2, 1, True), (3, 2, False), (4, 2, True)]
        cursor.executemany(
            "INSERT INTO ItemIn (ItemID, orderID, found) VALUES (?, ?, ?)",
            items_in_orders,
        )

        # Insert Deliveries
        deliveries = [
            ("lisa_delivery", 1, "Completed", "2024-02-03"),
            ("lisa_delivery", 2, "In Progress", "2024-02-04"),
        ]
        cursor.executemany(
            "INSERT INTO Delivered (userName, orderID, status, date) VALUES (?, ?, ?, ?)",
            deliveries,
        )

        # Commit the changes
        conn.commit()
        print("Dummy data inserted successfully!")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    insert_dummy_data()
