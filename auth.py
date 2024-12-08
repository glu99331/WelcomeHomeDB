import mysql.connector
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
    session,
    current_app,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    current_user,
    login_required,
)
from .db import get_db
import os
import io
import base64
from PIL import Image

# Define your User class that extends UserMixin
class User(UserMixin):
    def __init__(self, username, fname, roles, current_role=None):
        self.id = username
        self.firstname = fname
        self.roles = roles  # Store roles directly on the User object
        self.current_role = current_role  # Store current_role on the User object

def create_auth_blueprint(login_manager: LoginManager):
    bp = Blueprint("auth", __name__, url_prefix="/auth")

    @login_manager.user_loader
    def load_user(user_id):
        db = get_db()
        cursor = db.cursor(prepared=True)
        cursor.execute("SELECT * FROM Person WHERE userName = ?", (user_id,))
        columns = [column[0] for column in cursor.description]
        res = cursor.fetchone()
        if res is None:
            return None
        res_dict = dict(zip(columns, res))
        user_id = res_dict.get("userName")
        fname = res_dict.get("fname")

        # Fetch the user's roles and store them in the User object
        cursor.execute(
            "SELECT roleID FROM Act WHERE userName = ?", (user_id,)
        )
        
        roles = [row[0] for row in cursor.fetchall()]

        # Get the current_role from session, or None if not set
        current_role = session.get('current_role', None)
        print("current role is:", current_role)
        return User(user_id, fname, roles, current_role)

    @bp.route("/register", methods=("GET", "POST"))
    def register():
        db = get_db()
        # Retrieve all roles from Role Table
        cursor = db.cursor(prepared=True, dictionary=True)
        cursor.execute("SELECT roleID FROM Role")
        roles = cursor.fetchall()
        
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            first_name = request.form["first_name"]
            last_name = request.form["last_name"]
            email_address = request.form["email_address"]
            role = request.form["role"]
            phones = request.form.getlist("phones[]")  # Get all phone numbers as a list

            error = None
            cursor = db.cursor(prepared=True)
            cursor.execute("SELECT 1 FROM Person WHERE userName = ?", (username,))
            existing_user = cursor.fetchone()

            if not username:
                error = "Username is required."
            elif not password:
                error = "Password is required."
            elif (not first_name) or (not last_name):
                error = "Name is required."
            elif not email_address:
                error = "Email is required."
            elif not phones:
                error = "At least one phone number is required."
            elif existing_user:
                error = f"User {username} is already registered."
            
            if error is None:
                try:
                    # Insert into the Person table
                    cursor.execute(
                        "INSERT INTO Person (userName, pwd, fname, lname, email) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (
                            username,
                            generate_password_hash(password),
                            first_name,
                            last_name,
                            email_address,
                        ),  # already does salting
                    )
                    # Insert into Act table for the role
                    cursor.execute(
                        "INSERT INTO Act (userName, roleID) " "VALUES (?, ?)",
                        (username, role),
                    )
                    # Insert all phone numbers into PersonPhone table
                    for phone in phones:
                        cursor.execute(
                            "INSERT INTO PersonPhone (userName, phone) VALUES (?, ?)",
                            (username, phone),
                        )

                    db.commit()

                except mysql.connector.IntegrityError:
                    error = f"User {username} is already registered."
                else:
                    flash("User successfully registered! Please log in.", "success")
                    return redirect(url_for("auth.login"))

            flash(error)
        return render_template("auth/register.html", roles=roles)

    @bp.route("/login", methods=("GET", "POST"))
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("auth.index"))

        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            db = get_db()
            cursor = db.cursor(prepared=True)
            error = None
            cursor.execute("SELECT * FROM Person WHERE userName = ?", (username,))
            columns = [column[0] for column in cursor.description]
            user = cursor.fetchone()
            if user is None:
                error = "Non-existing username"
            elif not check_password_hash(user[1], password):
                error = "Incorrect password."

            if error is None:
                res_dict = dict(zip(columns, user))
                username = res_dict.get("userName")
                fname = res_dict.get("fname")

                # Fetch roles for the user
                cursor.execute("SELECT roleID FROM Act WHERE userName = ?", (username,))
                roles = [row[0] for row in cursor.fetchall()]
                print('roles:', roles)

                wrapped_user = User(username, fname, roles)
                login_user(wrapped_user)
                print(f"User roles assigned to wrapped_user: {wrapped_user.roles}")  # Debugging output
                return redirect(url_for("auth.index"))  # change to your main page here
            flash(error)

        return render_template("auth/login.html")

    @bp.route("/logout")
    def logout():
        logout_user()
        return redirect(url_for("auth.login"))

    @bp.route("/index", methods=("GET", "POST"))
    def index():
        if current_user.is_authenticated:
            # Use the helper function for role switching
            current_role, can_toggle_role = handle_role_switching(current_user)
            item_image = None
            return render_template(
                "auth/index.html",
                fname=current_user.firstname,
                roles=current_user.roles,
                current_role=current_role,  # Pass current_role to the template
                can_toggle_role=can_toggle_role,  # Pass boolean for enabling view toggle
                item_image=item_image
            )

        return redirect(url_for("auth.login"))

    # Q2
    @bp.route("/find_item", methods=["POST"])
    @login_required
    def find_item():
        item_id = request.form["itemID"]  # Get the itemID from the form
        db = get_db()
        cursor = db.cursor(prepared=True)

        # Query to find all locations of pieces for the given itemID
        cursor.execute(
            """
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
            """,
            (item_id,),
        )
        locations = cursor.fetchall()  # Fetch all matching locations
        
        # Fetch the photo for the item
        cursor.execute("SELECT photo FROM Item WHERE ItemID = %s", (item_id,))
        photo_data = cursor.fetchone()
        if photo_data and photo_data[0]:
            # Convert BLOB to image and encode as base64
            photo = photo_data[0]
            image = Image.open(io.BytesIO(photo))
            img_io = io.BytesIO()
            image.save(img_io, 'PNG')  # Save image as PNG
            img_io.seek(0)
            img_base64 = base64.b64encode(img_io.read()).decode('utf-8')
        else:
            img_base64 = None  # No photo available for this item

        # Use the helper function for role switching
        current_role, can_toggle_role = handle_role_switching(current_user)
        roles = current_user.roles  # Directly using roles from the user object
        
        # Render the template with locations and image
        return render_template(
            "auth/index.html", 
            locations=locations, 
            order_items=None, 
            roles=roles, 
            current_role=current_role, 
            can_toggle_role=can_toggle_role,
            item_image=img_base64,  # Pass the image data to the template
        )


    # Q3
    @bp.route("/find_order_items", methods=["POST"])
    @login_required
    def find_order_items():
        order_id = request.form["orderID"]  # Get the orderID from the form
        db = get_db()
        cursor = db.cursor(prepared=True)

        # Query to find all items and their locations for the given orderID
        cursor.execute(
            """
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
            """,
            (order_id,),
        )
        results = cursor.fetchall()

        # Organize results by ItemID and fetch the image (if available)
        order_items = {}
        for row in results:
            item_id = row[0]
            
            # Fetch the photo for the item
            cursor.execute("SELECT photo FROM Item WHERE ItemID = %s", (item_id,))
            photo_data = cursor.fetchone()
            print('Photo Data',photo_data)
            if photo_data and photo_data[0]:
                # Convert BLOB to image and encode as base64
                photo = photo_data[0]
                image = Image.open(io.BytesIO(photo))
                img_io = io.BytesIO()
                image.save(img_io, 'PNG')  # Save image as PNG
                img_io.seek(0)
                img_base64 = base64.b64encode(img_io.read()).decode('utf-8')
            else:
                img_base64 = None  # No photo available for this item
            
            # Organize the order items with the photo data
            if item_id not in order_items:
                order_items[item_id] = {
                    "itemID": item_id,
                    "photo": img_base64,  # Add photo data to the item
                    "pieces": []
                }

            order_items[item_id]["pieces"].append(
                {
                    "pieceNum": row[1],
                    "pDescription": row[2],
                    "roomNum": row[3],
                    "shelfNum": row[4],
                    "shelf": row[5],
                    "shelfDescription": row[6],
                }
            )

        # Use the helper function for role switching
        current_role, can_toggle_role = handle_role_switching(current_user)
        roles = current_user.roles  # Directly using roles from the user object

        return render_template(
            "auth/index.html",
            order_items=list(order_items.values()),
            locations=None,
            roles=roles,
            current_role=current_role,  # Pass current_role to the template
            can_toggle_role=can_toggle_role,  # Pass boolean for enabling view toggle
            item_image=img_base64
        )
    
    # Q4
    @bp.route("/accept_donation", methods=("GET", "POST"))
    @login_required
    def accept_donation():
        db = get_db()
        cursor = db.cursor(prepared=True)

        # The button only appears if the user is a supervisor or a staff member.
        cursor.execute("SELECT roomNum, shelfNum FROM Location")
        locations = cursor.fetchall()
        print('locations:', locations)

        # Fetch categories from the Category table
        cursor.execute("SELECT DISTINCT mainCategory FROM Category")
        main_categories = cursor.fetchall()

        # Fetch subcategories for each main category
        cursor.execute("SELECT mainCategory, subCategory FROM Category")
        sub_categories = cursor.fetchall()
        sub_category_dict = {}
        for main_category, sub_category in sub_categories:
            if main_category not in sub_category_dict:
                sub_category_dict[main_category] = []
            sub_category_dict[main_category].append(sub_category)
        # Deny access for GET requests if the user doesn't have permission. If the user tries to manually access the /accept_donation route, deny if non-staff member
        if request.method == "GET":
            if not ((len(current_user.roles) > 1 and current_user.current_role == 'AdminStaff') or 
                    (len(current_user.roles) == 1 and any(role in current_user.roles for role in ['Admin', 'StaffMember', 'Supervisor']))):
                flash("You don't have the required permissions to access that page as a Non-Staff user.", "error")
                return redirect(url_for("auth.index"))  # Redirect to the home page or an appropriate page
        
        if request.method == "POST":
            if ((len(current_user.roles) > 1 and current_user.current_role == 'AdminStaff') or (len(current_user.roles) == 1 and any(['Admin', 'StaffMember', 'Supervisor']) in current_user.roles)):
                print('current_user role is:', current_user.roles, current_user.current_role)
                donor_id = request.form.get("donorID")
                # Check if donorID is provided and valid
                if donor_id:
                    cursor.execute("SELECT 1 FROM Person WHERE userName = ?", (donor_id,))
                    donor_exists = cursor.fetchone()
                    if not donor_exists:
                        flash("Invalid Donor ID. Please try again.", "error")
                        return render_template("auth/accept_donation.html", step=1)

                    # Donor is valid, proceed to show the full form
                    if "step" in request.form and request.form["step"] == "2":
                        # Process the full form
                        
                        item_description = request.form["itemDescription"]
                        color = request.form["color"]
                        material = request.form["material"]
                        main_category = request.form["mainCategory"]
                        sub_category = request.form["subCategory"]
                        has_pieces = request.form["hasPieces"].lower() == "true"

                        pieces = []
                        piece_num = 1
                        while f"pieces[{piece_num}][description]" in request.form:
                            description = request.form.get(f"pieces[{piece_num}][description]")
                            length = request.form.get(f"pieces[{piece_num}][length]")
                            width = request.form.get(f"pieces[{piece_num}][width]")
                            height = request.form.get(f"pieces[{piece_num}][height]")
                            room_num = request.form.get(f"pieces[{piece_num}][roomNum]")
                            shelf_num = request.form.get(f"pieces[{piece_num}][shelfNum]")
                            pNotes = request.form.get(f"pieces[{piece_num}][pNotes]")
                            
                            # Add the piece data to the list
                            pieces.append({
                                "description": description,
                                "length": length,
                                "width": width,
                                "height": height,
                                "roomNum": room_num,
                                "shelfNum": shelf_num,
                                "pNotes": pNotes
                            })
                            piece_num += 1

                        print(pieces)  # Debugging: Check the collected pieces
                        image = request.files.get('itemPhoto')
                        photo_data = None
                        if image and allowed_file(image.filename):
                            filename = secure_filename(image.filename)
                            # Save the file to a predefined folder
                            image.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                            # Open the file and read it as binary
                            with open(os.path.join(current_app.config['UPLOAD_FOLDER'], filename), 'rb') as f:
                                photo_data = f.read()
                        try:
                            # Insert into the Item table
                            cursor.execute(
                                """
                                INSERT INTO Item (iDescription, photo, color, isNew, hasPieces, material, mainCategory, subCategory)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    item_description,
                                    photo_data,
                                    color,
                                    True,
                                    has_pieces,
                                    material,
                                    main_category,
                                    sub_category,
                                ),
                            )
                            db.commit()
                            item_id = cursor.lastrowid

                            # Insert pieces (if applicable)
                            if has_pieces:
                                for piece in pieces:
                                    p_description = piece['description']
                                    length = piece['length']
                                    width = piece['width']
                                    height = piece['height']
                                    room_num = piece['roomNum']
                                    shelf_num = piece['shelfNum']
                                    p_notes = piece['pNotes']

                                    cursor.execute(
                                        """
                                        INSERT INTO Piece (ItemID, pieceNum, pDescription, length, width, height, roomNum, shelfNum, pNotes)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                        """,
                                        (
                                            item_id,
                                            piece_num,
                                            p_description,
                                            length,
                                            width,
                                            height,
                                            room_num,
                                            shelf_num,
                                            p_notes
                                        ),
                                    )
                            else:
                                # Set pieceNum to 1, since an item itself is just one piece.
                                p_description = pieces[0]['description']
                                length = pieces[0]['length']
                                width = pieces[0]['width']
                                height = pieces[0]['height']
                                room_num = pieces[0]['roomNum']
                                shelf_num = pieces[0]['shelfNum']
                                p_notes = pieces[0]['pNotes']
                                # Insert a single default piece for items without pieces
                                cursor.execute(
                                    """
                                    INSERT INTO Piece (ItemID, pieceNum, pDescription, length, width, height, roomNum, shelfNum, pNotes)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """,
                                    (
                                        item_id,
                                        1,
                                        item_description,
                                        length,
                                        width,
                                        height,
                                        room_num,
                                        shelf_num,
                                        p_notes
                                    ),
                                )

                            # Insert into DonatedBy table
                            cursor.execute(
                                """
                                INSERT INTO DonatedBy (ItemID, userName, donateDate)
                                VALUES (?, ?, CURDATE())
                                """,
                                (item_id, donor_id),
                            )
                            db.commit()

                            flash("Donation successfully recorded!", "success")
                            return redirect(url_for("auth.index"))

                        except Exception as e:
                            db.rollback()
                            flash(f"An error occurred: {e}", "error")
                            # Check which part of the insertion caused the issue
                            if "INSERT INTO Item" in str(e):
                                flash("Error inserting into the Item table. Please check the values provided.", "error")
                            elif "INSERT INTO Piece" in str(e):
                                flash("Error inserting into the Piece table. Please check the piece data.", "error")
                            elif "INSERT INTO DonatedBy" in str(e):
                                flash("Error inserting into the DonatedBy table. Please check the donor and item link.", "error")
                            else:
                                flash("An unexpected error occurred.", "error")
                            # Provide detailed traceback for debugging purposes
                            import traceback
                            traceback.print_exc()  # This will print the full traceback of the erro
                            return render_template(
                                "auth/accept_donation.html",
                                step=2,
                                donor_id=donor_id,
                                locations=locations,
                                main_categories=main_categories,
                                sub_category_dict=sub_category_dict,
                            )

                return render_template(
                    "auth/accept_donation.html",
                    step=2,
                    donor_id=donor_id,
                    locations=locations,
                    main_categories=main_categories,
                    sub_category_dict=sub_category_dict,
                )

        return render_template(
            "auth/accept_donation.html",
            step=1,
        )
    


    # Feature no. 6
    @bp.route("/add_to_order", methods=["GET", "POST"])
    @login_required
    def add_to_order():
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        categories = []
        subcategories = []
        items = []
        error = None
        selected_category = None
        selected_subcategory = None

        try:
            # Fetch categories and subcategories for the dropdown
            cursor.execute("SELECT DISTINCT mainCategory FROM Item")
            categories = [row["mainCategory"] for row in cursor.fetchall()]
            print(f"Categories: {categories}")  # Debugging

            cursor.execute("SELECT DISTINCT subCategory FROM Item")
            subcategories = [row["subCategory"] for row in cursor.fetchall()]
            print(f"Subcategories: {subcategories}")  # Debugging
        except Exception as e:
            error = f"Error fetching categories or subcategories: {e}"
            print(f"Error: {error}")  # Debugging

        if request.method == "POST":
            selected_category = request.form.get("category")
            selected_subcategory = request.form.get("subcategory")
            print(f"Selected Category: {selected_category}, Subcategory: {selected_subcategory}")  # Debugging

            if "filter_items" in request.form:
                # Handle filtering items
                try:
                    print(f"Executing query with Category: {selected_category}, Subcategory: {selected_subcategory}")
                    cursor.execute(
                        """
                        SELECT i.ItemID, i.iDescription
                        FROM Item i
                        LEFT JOIN ItemIn ii ON i.ItemID = ii.ItemID
                        WHERE i.mainCategory = %s AND i.subCategory = %s AND ii.ItemID IS NULL
                        """,
                        (selected_category, selected_subcategory)
                    )
                    items = cursor.fetchall()
                    print(f"Fetched Items: {items}")  # Debugging
                except Exception as e:
                    error = f"Error fetching items: {e}"
                    print(f"Error: {error}")  # Debugging

            elif "add_to_order" in request.form:
                # Handle adding selected items to a new order
                selected_items = request.form.getlist("selected_items")
                print(f"Selected Items: {selected_items}")  # Debugging
                if not selected_items:
                    flash("No items selected.", "error")
                else:
                    try:
                        # Create a new order
                        print("Creating a new order...")  # Debugging
                        cursor.execute(
                            "INSERT INTO Ordered (client, supervisor, orderDate) "
                            "VALUES (%s, %s, CURDATE())",
                            (current_user.id, "ohmpatel47")  # Replace with actual supervisor logic
                        )
                        db.commit()
                        order_id = cursor.lastrowid
                        print(f"New Order ID: {order_id}")  # Debugging

                        # Add selected items to the new order
                        for item_id in selected_items:
                            cursor.execute(
                                "INSERT INTO ItemIn (ItemID, orderID) VALUES (%s, %s)",
                                (item_id, order_id)
                            )
                        db.commit()
                        flash("Selected items successfully added to your new order.", "success")
                    except Exception as e:
                        db.rollback()
                        error = f"Error adding items to the order: {e}"
                        print(f"Error: {error}")  # Debugging

                    # Redirect to avoid resubmission
                    return redirect(url_for("auth.add_to_order"))

        return render_template(
            "auth/add_to_order.html",
            categories=categories,
            subcategories=subcategories,
            items=items,
            error=error,
            selected_category=selected_category,
            selected_subcategory=selected_subcategory
        )





    return bp


# Helper function to handle role switching:
def handle_role_switching(current_user):
    # Handle the role switching
    if request.method == "POST":
        selected_view = request.form.get('view')
        
        # Ensure the user has both Admin/Staff and Client/Donor roles before switching
        if selected_view and ('Admin' in current_user.roles or 'StaffMember' in current_user.roles or 'Supervisor' in current_user.roles) and \
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
        if 'Admin' in current_user.roles or 'StaffMember' in current_user.roles or 'Supervisor' in current_user.roles:
            current_role = 'AdminStaff'  # Default to Admin if the user has admin/staff roles
        else:
            current_role = 'ClientDonor'  # Default to Client view if the user has Client/Donor roles

    # Check if user can toggle based on roles
    can_toggle_role = (
        ('Admin' in current_user.roles or 'StaffMember' in current_user.roles or 'Supervisor' in current_user.roles) and
        ('Client' in current_user.roles or 'Donor' in current_user.roles)
    )
    
    return current_role, can_toggle_role

# Define allowed file extensions function
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']
