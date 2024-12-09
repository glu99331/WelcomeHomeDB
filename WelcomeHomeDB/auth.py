import mysql.connector
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
    session,
    jsonify,
)
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    current_user,
    login_required,
)
from .db import get_db

from pprint import pprint


# Define your User class that extends UserMixin
class User(UserMixin):
    def __init__(self, username, fname, roles):
        self.id = username
        self.firstname = fname
        self.roles = roles  # Store roles directly on the User object


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
        cursor.execute("SELECT roleID FROM Act WHERE userName = ?", (user_id,))

        roles = [row[0] for row in cursor.fetchall()]
        return User(user_id, fname, roles)

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
                print("roles:", roles)

                wrapped_user = User(username, fname, roles)
                login_user(wrapped_user)
                print(
                    f"User roles assigned to wrapped_user: {wrapped_user.roles}"
                )  # Debugging output
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
            return render_template(
                "auth/index.html",
                fname=current_user.firstname,
                roles=current_user.roles,
                current_role=current_role,  # Pass current_role to the template
                can_toggle_role=can_toggle_role,  # Pass boolean for enabling view toggle
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
        # Use the helper function for role switching
        current_role, can_toggle_role = handle_role_switching(current_user)
        roles = current_user.roles  # Directly using roles from the user object
        return render_template(
            "auth/index.html",
            locations=locations,
            order_items=None,
            roles=roles,
            multiple_views=False,
            current_role=current_role,
            can_toggle_role=can_toggle_role,
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

        # Organize results by ItemID
        order_items = {}
        for row in results:
            item_id = row[0]
            if item_id not in order_items:
                order_items[item_id] = {"itemID": item_id, "pieces": []}
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

        if request.method == "POST":
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
                    pieces = request.form.getlist(
                        "pieces"
                    )  # Get pieces data from the form

                    try:
                        # Insert into the Item table
                        cursor.execute(
                            """
                            INSERT INTO Item (iDescription, color, isNew, hasPieces, material, mainCategory, subCategory)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                item_description,
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
                            for piece_data in pieces:
                                piece_num = piece_data.get("pieceNum")
                                p_description = piece_data.get("description")
                                length = piece_data.get("length")
                                width = piece_data.get("width")
                                height = piece_data.get("height")
                                room_num = piece_data.get("roomNum")
                                shelf_num = piece_data.get("shelfNum")

                                cursor.execute(
                                    """
                                    INSERT INTO Piece (ItemID, pieceNum, pDescription, length, width, height, roomNum, shelfNum)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
                                    ),
                                )
                        else:
                            # Insert a single default piece for items without pieces
                            cursor.execute(
                                """
                                INSERT INTO Piece (ItemID, pieceNum, pDescription, length, width, height, roomNum, shelfNum)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    item_id,
                                    1,
                                    item_description,
                                    None,
                                    None,
                                    None,
                                    None,
                                    None,
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
                        return render_template(
                            "auth/accept_donation.html",
                            step=2,
                            donor_id=donor_id,
                            locations=locations,
                        )

            return render_template(
                "auth/accept_donation.html",
                step=2,
                donor_id=donor_id,
                locations=locations,
            )

        return render_template(
            "auth/accept_donation.html",
            step=1,
        )

    # Q8
    @bp.route("/get_orders", methods=["GET"])
    @login_required
    def get_orders():
        db = get_db()
        cursor = db.cursor(prepared=True)
        cursor.execute(
            """SELECT 
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
    """,
            (current_user.id, current_user.id, current_user.id),
        )
        orders = cursor.fetchall()
        orders_list = [
            {
                "orderID": order[0],
                "orderDate": order[1],
                "orderNotes": order[2],
                "supervisor": order[3],
                "client": order[4],
                "status": order[5],
                "deliveryDate": order[6],
                "role": order[7]
            }
            for order in orders
        ]
        pprint(orders_list)

        return jsonify({"orders": orders_list})
    

    @bp.route("/get_user_orders", methods=["GET"])
    @login_required
    def get_user_orders():
        db = get_db()
        cursor = db.cursor(prepared=True)
        cursor.execute(
            """SELECT 
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
            """,
            (current_user.id, current_user.id),
        )
        orders = cursor.fetchall()
        orders_list = [
            {
                "orderID": order[0],
                "orderDate": order[1],
                "orderNotes": order[2],
                "supervisor": order[3],
                "client": order[4],
                "status": order[5],
                "deliveryDate": order[6],
                "role": order[7]
            }
            for order in orders
        ]
        return jsonify({"orders": orders_list})
    

    @bp.route("/update_order_status", methods=["POST"])
    @login_required
    def update_order_status():
        order_id = request.form["orderID"]
        new_status = request.form["status"]
        db = get_db()
        cursor = db.cursor(prepared=True)
        cursor.execute(
            "UPDATE Delivered SET status = ? WHERE orderID = ?",
            (new_status, order_id)
        )
        db.commit()
        return jsonify({"success": True})



    return bp


# Helper function to handle role switching:
def handle_role_switching(current_user):
    # Handle the role switching
    if request.method == "POST":
        selected_view = request.form.get("view")

        # Ensure the user has both Admin/Staff and Client/Donor roles before switching
        if (
            selected_view
            and (
                "Admin" in current_user.roles
                or "StaffMember" in current_user.roles
                or "Supervisor" in current_user.roles
            )
            and ("Client" in current_user.roles or "Donor" in current_user.roles)
        ):
            session["current_role"] = (
                selected_view  # Store the selected view in the session
            )
            flash(f"Switched to {selected_view} view", "success")
        elif (
            selected_view
        ):  # If a view is selected but the user doesn't have permission
            flash("Invalid role selection or insufficient permissions.", "error")

    # Get the current role from the session, default to Admin/Staff if none selected
    current_role = session.get("current_role", None)

    if current_role is None:
        # Default to 'AdminStaff' if the user has Admin/Staff roles
        if "Admin" in current_user.roles or "StaffMember" in current_user.roles:
            current_role = (
                "AdminStaff"  # Default to Admin if the user has admin/staff roles
            )
        else:
            current_role = "ClientDonor"  # Default to Client view if the user has Client/Donor roles

    # Check if user can toggle based on roles
    can_toggle_role = (
        "Admin" in current_user.roles
        or "StaffMember" in current_user.roles
        or "Supervisor" in current_user.roles
    ) and ("Client" in current_user.roles or "Donor" in current_user.roles)

    return current_role, can_toggle_role
