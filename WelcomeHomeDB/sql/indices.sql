-- Select Database
USE WelcomeHomeDB;

-- Person Table
CREATE INDEX idx_person_email ON Person(email);

-- Item Table
CREATE INDEX idx_item_category ON Item(mainCategory, subCategory);

-- DonatedBy Table
CREATE INDEX idx_donated_item_date ON DonatedBy(ItemID, donateDate);

-- Act Table
CREATE INDEX idx_act_role ON Act(roleID);

-- Piece Table
CREATE INDEX idx_piece_location ON Piece(roomNum, shelfNum);
CREATE INDEX idx_piece_item ON Piece(ItemID);

-- Ordered Table
CREATE INDEX idx_order_supervisor_date ON Ordered(supervisor, orderDate);
CREATE INDEX idx_order_client_date ON Ordered(client, orderDate);

-- Delivered Table
CREATE INDEX idx_delivery_status_date ON Delivered(status, date);