-- Insert into Category table 
INSERT INTO
    Category (mainCategory, subCategory, catNotes)
VALUES
    (
        'Furniture',
        'Chair',
        'Various types of chairs including office and dining chairs'
    ),
    (
        'Furniture',
        'Table',
        'Dining and work tables of different materials'
    ),
    (
        'Electronics',
        'Laptop',
        'Various brands and configurations of laptops'
    ),
    (
        'Clothing',
        'Shirts',
        'Casual and formal shirts for all genders'
    ),
    (
        'Books',
        'Fiction',
        'Fictional novels and short stories'
    );

-- Insert into Item table
INSERT INTO
    Item (
        iDescription,
        color,
        photo,
        isNew,
        hasPieces,
        material,
        mainCategory,
        subCategory
    )
VALUES
    (
        'Office Chair with wheels',
        'Black',
        LOAD_FILE("/var/lib/mysql-files/chair.jpg"),
        TRUE,
        FALSE,
        'Plastic and Fabric',
        'Furniture',
        'Chair'
    ),
    (
        'Dining Table with 4 legs',
        'Brown',
        LOAD_FILE('/var/lib/mysql-files/table.jpg'),
        TRUE,
        TRUE,
        'Wood',
        'Furniture',
        'Table'
    ),
    (
        'HP EliteBook Laptop',
        'Silver',
        LOAD_FILE('/var/lib/mysql-files/laptop.jpg'),
        TRUE,
        FALSE,
        'Metal and Plastic',
        'Electronics',
        'Laptop'
    ),
    (
        "Men's Cotton Shirt",
        'Blue',
        LOAD_FILE('/var/lib/mysql-files/shirt.jpg'),
        TRUE,
        FALSE,
        'Cotton',
        'Clothing',
        'Shirts'
    ),
    (
        'Mystery Novel: The Lost Symbol',
        "N/A",
        LOAD_FILE('/var/lib/mysql-files/book.jpg'),
        FALSE,
        FALSE,
        'Paper',
        'Books',
        'Fiction'
    );

-- Insert into Person table
INSERT INTO
    Person (userName, pwd, fname, lname, email)
VALUES
    (
        'johnDoe',
        'password123',
        'John',
        'Doe',
        'john.doe@example.com'
    ),
    (
        'janeSmith',
        'password456',
        'Jane',
        'Smith',
        'jane.smith@example.com'
    ),
    (
        'adminUser',
        'adminPassword',
        'Admin',
        'User',
        'admin@example.com'
    );

-- Insert into PersonPhone table
INSERT INTO
    PersonPhone (userName, phone)
VALUES
    ('johnDoe', '123-456-7890'),
    ('janeSmith', '987-654-3210'),
    ('adminUser', '555-555-5555');

-- Insert into DonatedBy table
INSERT INTO
    DonatedBy (ItemID, userName, donateDate)
VALUES
    (1, 'johnDoe', '2024-11-01'),
    (2, 'janeSmith', '2024-11-02');

-- Insert into Role table
INSERT INTO
    Role (roleID, rDescription)
VALUES
    (
        'Supervisor',
        'Oversees all operations and order assignments'
    ),
    ('Client', 'Recipient of items or services'),
    ('DeliveryPerson', 'Handles item deliveries'),
    (
        'StaffMember',
        'General staff member with access to operational features'
    );

-- Insert into Act table
INSERT INTO
    Act (userName, roleID)
VALUES
    ('johnDoe', 'Supervisor'),
    ('janeSmith', 'Client'),
    ('adminUser', 'DeliveryPerson');

-- Insert into Location table
INSERT INTO
    Location (roomNum, shelfNum, shelf, shelfDescription)
VALUES
    (1, 1, 'A1', 'Shelf in Room 1, Section A'),
    (1, 2, 'A2', 'Shelf in Room 1, Section B'),
    (2, 1, 'B1', 'Shelf in Room 2, Section A');

-- Insert into Piece table
-- Insert into Piece table
-- Adding pieces for all items, even for those that logically don't have multiple pieces
-- Item 1: Office Chair (Single Piece)
INSERT INTO
    Piece (
        ItemID,
        pieceNum,
        pDescription,
        length,
        width,
        height,
        roomNum,
        shelfNum,
        pNotes
    )
VALUES
    (
        1,
        1,
        'Office Chair (Complete)',
        60,
        60,
        120,
        1,
        1,
        'Fully assembled chair'
    );

-- Item 2: Dining Table (Multiple Pieces)
INSERT INTO
    Piece (
        ItemID,
        pieceNum,
        pDescription,
        length,
        width,
        height,
        roomNum,
        shelfNum,
        pNotes
    )
VALUES
    (
        2,
        1,
        'Dining table top',
        200,
        100,
        5,
        1,
        1,
        'Main surface of the table'
    ),
    (
        2,
        2,
        'Dining table leg',
        10,
        10,
        100,
        1,
        1,
        'Leg support for the table'
    ),
    (
        2,
        3,
        'Dining table screw set',
        1,
        1,
        1,
        1,
        2,
        'Hardware for assembly'
    );

-- Item 3: Laptop (Single Piece)
INSERT INTO
    Piece (
        ItemID,
        pieceNum,
        pDescription,
        length,
        width,
        height,
        roomNum,
        shelfNum,
        pNotes
    )
VALUES
    (
        3,
        1,
        'HP EliteBook Laptop',
        35,
        25,
        2,
        1,
        1,
        'Fully assembled laptop'
    );

-- Item 4: Men\'s Cotton Shirt (Single Piece)
INSERT INTO
    Piece (
        ItemID,
        pieceNum,
        pDescription,
        length,
        width,
        height,
        roomNum,
        shelfNum,
        pNotes
    )
VALUES
    (
        4,
        1,
        'Men\'s Cotton Shirt',
        0,
        0,
        0,
        1,
        1,
        'Folded shirt on shelf'
    );

-- Item 5: Mystery Novel (Single Piece)
INSERT INTO
    Piece (
        ItemID,
        pieceNum,
        pDescription,
        length,
        width,
        height,
        roomNum,
        shelfNum,
        pNotes
    )
VALUES
    (
        5,
        1,
        'Mystery Novel: The Lost Symbol',
        15,
        10,
        2,
        1,
        2,
        'Book on shelf'
    );

-- Insert into Ordered table
INSERT INTO
    Ordered (orderDate, orderNotes, supervisor, client)
VALUES
    (
        '2024-11-15',
        'Urgent delivery for client Jane Smith',
        'johnDoe',
        'janeSmith'
    ),
    (
        '2024-11-16',
        'Routine order for restocking office supplies',
        'johnDoe',
        'adminUser'
    );

-- Insert into ItemIn table
INSERT INTO
    ItemIn (ItemID, orderID, found)
VALUES
    (1, 1, TRUE),
    (2, 1, FALSE),
    (3, 2, TRUE);

-- Insert into Delivered table
INSERT INTO
    Delivered (userName, orderID, status, date)
VALUES
    ('adminUser', 1, 'Delivered', '2024-11-16'),
    ('adminUser', 2, 'Pending', '2024-11-17');