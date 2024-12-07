import mysql.connector
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
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


# Define your User class that extends UserMixin
class User(UserMixin):
    def __init__(self, username, fname):
        self.id = username
        self.firstname = fname


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
        print(user_id, fname)
        return User(user_id, fname)

    @bp.route("/register", methods=("GET", "POST"))
    def register():
        db = get_db()
        # Retrieve all roles from Role Table
        cursor = db.cursor(prepared=True, dictionary=True)
        cursor.execute("SELECT roleID FROM Role")
        roles = cursor.fetchall()
        print(roles)
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
                print("here")
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
            print(columns)
            user = cursor.fetchone()
            if user is None:
                error = "Non-existing username"
            elif not check_password_hash(user[1], password):
                error = "Incorrect password."

            if error is None:
                res_dict = dict(zip(columns, user))
                username = res_dict.get("userName")
                fname = res_dict.get("fname")
                wrapped_user = User(username, fname)
                login_user(wrapped_user)
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
            print(f"Current user: {current_user.firstname}")  # Debugging

            # Retrieve the user's roles
            db = get_db()
            cursor = db.cursor(prepared=True, dictionary=True)

            # Check the roles of the current user
            cursor.execute(
                "SELECT roleID FROM Act WHERE userName = ?", (current_user.id,)
            )
            roles = [row["roleID"] for row in cursor.fetchall()]
            return render_template(
                "auth/index.html",
                fname=current_user.firstname,
                locations=None,
                roles=roles,
            )
        return redirect(url_for("auth.login"))

    # Q2
    @bp.route("/find_item", methods=["POST"])
    @login_required
    def find_item():
        item_id = request.form["itemID"]  # Get the itemID from the form
        db = get_db()
        cursor = db.cursor(prepared=True, dictionary=True)

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
        # Retrieve the user's roles
        cursor.execute("SELECT roleID FROM Act WHERE userName = ?", (current_user.id,))
        roles = [row["roleID"] for row in cursor.fetchall()]
        # Pass the locations to the index.html template
        return render_template(
            "auth/index.html", locations=locations, order_items=None, roles=roles
        )

    # Q3
    @bp.route("/find_order_items", methods=["POST"])
    @login_required
    def find_order_items():
        order_id = request.form["orderID"]  # Get the orderID from the form
        db = get_db()
        cursor = db.cursor(prepared=True, dictionary=True)
        # Query to find all items and their locations for the given orderID
        cursor.execute(  # Should we get the name of the item as well to display better (just another join)
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
        print("Results from database:", results)  # Debugging: Check fetched rows
        # Organize results by ItemID
        order_items = {}
        for row in results:
            item_id = row["ItemID"]
            if item_id not in order_items:
                order_items[item_id] = {"itemID": item_id, "pieces": []}
            order_items[item_id]["pieces"].append(
                {
                    "pieceNum": row["pieceNum"],
                    "pDescription": row["pDescription"],
                    "roomNum": row["roomNum"],
                    "shelfNum": row["shelfNum"],
                    "shelf": row["shelf"],
                    "shelfDescription": row["shelfDescription"],
                }
            )
        # Retrieve the user's roles
        cursor.execute("SELECT roleID FROM Act WHERE userName = ?", (current_user.id,))
        roles = [row["roleID"] for row in cursor.fetchall()]
        # Pass the results to the index.html template
        return render_template(
            "auth/index.html",
            order_items=list(order_items.values()),
            locations=None,
            roles=roles,
        )

    # Q4
    @bp.route("/accept_donation", methods=("GET", "POST"))
    @login_required
    def accept_donation():
        db = get_db()
        cursor = db.cursor(prepared=True, dictionary=True)

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

    return bp
