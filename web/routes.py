from datetime import datetime
import os

from flask import flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from config.settings import ADMIN_ID
from database.mongodb import get_db

ADMIN_PASSWORD = os.getenv("WEB_ADMIN_PASSWORD", "admin123")


def _display_name(user):
    if not user:
        return "Mehmon"
    username = user.get("username")
    if username and username != "NoUsername":
        return f"@{username}"
    return user.get("first_name") or str(user.get("user_id"))


def _current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    if session.get("role") == "admin" and user_id == ADMIN_ID:
        return {"user_id": ADMIN_ID, "username": "admin", "first_name": "Admin", "role": "admin", "approved": True}
    return get_db().get_user(int(user_id))


def _role(user):
    if not user:
        return None
    if int(user.get("user_id", 0)) == ADMIN_ID:
        return "admin"
    return user.get("role") or "customer"


def _login_required(roles=None):
    user = _current_user()
    if not user:
        return None, redirect(url_for("web_login"))
    role = _role(user)
    if roles and role not in roles:
        flash("Bu sahifaga kirish huquqingiz yo'q.", "error")
        return None, redirect(url_for("web_dashboard"))
    return user, None


def _base_context(user=None):
    db = get_db()
    user = user or _current_user()
    warehouses = db.get_all_warehouses()
    selected_warehouse = request.args.get("warehouse") or (warehouses[0]["name"] if warehouses else None)
    return {
        "user": user,
        "role": _role(user),
        "display_name": _display_name(user),
        "warehouses": warehouses,
        "selected_warehouse": selected_warehouse,
        "year": datetime.utcnow().year,
    }


def register_web_routes(app):
    app.secret_key = os.getenv("SECRET_KEY", os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me"))

    @app.get("/login")
    def web_login():
        return render_template("login.html", **_base_context())

    @app.post("/login")
    def web_login_post():
        login = request.form.get("login", "").strip()
        password = request.form.get("password", "")
        if not login or not password:
            flash("Username yoki user_id va parol kiriting.", "error")
            return redirect(url_for("web_login"))

        if login in {str(ADMIN_ID), "admin"} and password == ADMIN_PASSWORD:
            session.clear()
            session.update({"user_id": ADMIN_ID, "role": "admin"})
            return redirect(url_for("web_dashboard"))

        db = get_db()
        user = db.find_user_for_login(login)
        if not user or not user.get("approved"):
            flash("Foydalanuvchi topilmadi yoki admin tasdiqlamagan.", "error")
            return redirect(url_for("web_login"))
        password_hash = user.get("password_hash")
        if not password_hash or not check_password_hash(password_hash, password):
            flash("Parol noto'g'ri. Parol keyinroq bot orqali beriladi.", "error")
            return redirect(url_for("web_login"))
        session.clear()
        session.update({"user_id": user["user_id"], "role": _role(user)})
        return redirect(url_for("web_dashboard"))

    @app.get("/logout")
    def web_logout():
        session.clear()
        flash("Tizimdan chiqdingiz.", "success")
        return redirect(url_for("web_login"))

    @app.get("/dashboard")
    def web_dashboard():
        user, response = _login_required()
        if response:
            return response
        db = get_db()
        ctx = _base_context(user)
        stats = db.get_order_stats()
        inventory = db.get_inventory_by_warehouse(ctx["selected_warehouse"]) if ctx["selected_warehouse"] else []
        if ctx["role"] == "admin":
            orders = db.get_orders(limit=8)
        elif ctx["role"] == "employee":
            orders = db.get_orders(employee_view=True, limit=8)
        else:
            orders = db.get_orders(customer_id=user["user_id"], limit=8)
        return render_template("dashboard.html", **ctx, stats=stats, orders=orders, inventory=inventory[:8])

    @app.get("/products")
    def web_products():
        user, response = _login_required(["admin", "employee"])
        if response:
            return response
        db = get_db()
        ctx = _base_context(user)
        warehouse = ctx["selected_warehouse"]
        branches = db.get_all_branches(warehouse) if warehouse else []
        product_types = []
        products = []
        if warehouse:
            for branch in branches + [{"name": "common"}]:
                for ptype in db.get_all_product_types(warehouse, branch["name"]):
                    product_types.append({**ptype, "branch": branch["name"]})
                    products.extend(db.get_products_by_type(warehouse, branch["name"], ptype["name"]))
        return render_template("products.html", **ctx, branches=branches, product_types=product_types, products=products)

    @app.post("/products/warehouse")
    def web_add_warehouse():
        user, response = _login_required(["admin"])
        if response:
            return response
        name = request.form.get("name", "").strip()
        if name and get_db().add_warehouse(name):
            flash("Sklad qo'shildi.", "success")
        else:
            flash("Sklad nomi bo'sh yoki mavjud.", "error")
        return redirect(url_for("web_products", warehouse=name))

    @app.post("/products/branch")
    def web_add_branch():
        user, response = _login_required(["admin"])
        if response:
            return response
        warehouse = request.form.get("warehouse")
        name = request.form.get("name", "").strip()
        if warehouse and name and get_db().add_branch(name, warehouse):
            flash("Filial qo'shildi.", "success")
        else:
            flash("Filial nomi bo'sh yoki mavjud.", "error")
        return redirect(url_for("web_products", warehouse=warehouse))

    @app.post("/products/type")
    def web_add_type():
        user, response = _login_required(["admin"])
        if response:
            return response
        warehouse = request.form.get("warehouse")
        branch = request.form.get("branch") or "common"
        name = request.form.get("name", "").strip()
        if warehouse and name and get_db().add_product_type(name, warehouse=warehouse, branch=branch):
            flash("Mahsulot turi qo'shildi.", "success")
        else:
            flash("Mahsulot turi bo'sh yoki mavjud.", "error")
        return redirect(url_for("web_products", warehouse=warehouse))

    @app.post("/products/item")
    def web_add_product():
        user, response = _login_required(["admin"])
        if response:
            return response
        db = get_db()
        warehouse = request.form.get("warehouse")
        branch = request.form.get("branch") or "common"
        product_type = request.form.get("product_type")
        name = request.form.get("name", "").strip()
        code = request.form.get("code", "").strip()
        unit = request.form.get("unit", "dona").strip() or "dona"
        if warehouse and product_type and name and db.add_product(name, code, product_type, warehouse=warehouse, branch=branch, unit=unit):
            flash("Mahsulot qo'shildi.", "success")
        else:
            flash("Mahsulot ma'lumotlari to'liq emas yoki mavjud.", "error")
        return redirect(url_for("web_products", warehouse=warehouse))

    @app.get("/orders")
    def web_orders():
        user, response = _login_required()
        if response:
            return response
        db = get_db()
        ctx = _base_context(user)
        if ctx["role"] == "admin":
            orders = db.get_orders()
        elif ctx["role"] == "employee":
            orders = db.get_orders(employee_view=True)
        else:
            orders = db.get_orders(customer_id=user["user_id"])
        return render_template("orders.html", **ctx, orders=orders)

    @app.post("/orders")
    def web_create_order():
        user, response = _login_required(["customer", "admin"])
        if response:
            return response
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        warehouse = request.form.get("warehouse") or None
        branch = request.form.get("branch") or None
        if not title or not description:
            flash("Buyurtma nomi va izohini yozing.", "error")
        else:
            get_db().create_order(user["user_id"], _display_name(user), title, description, warehouse, branch)
            flash("Buyurtma yuborildi. Admin tasdiqlasa xodimlarga ko'rinadi.", "success")
        return redirect(url_for("web_orders"))

    @app.post("/orders/<order_id>/status")
    def web_update_order(order_id):
        user, response = _login_required(["admin", "employee"])
        if response:
            return response
        status = request.form.get("status")
        allowed = {"admin": {"approved", "rejected", "done"}, "employee": {"in_progress", "done"}}
        role = _role(user)
        if status not in allowed[role]:
            flash("Bu statusni qo'yish huquqi yo'q.", "error")
            return redirect(url_for("web_orders"))
        note = request.form.get("note") or f"Status: {status}"
        assigned_to = user["user_id"] if role == "employee" and status == "in_progress" else None
        get_db().update_order_status(order_id, status, _display_name(user), note=note, assigned_to=assigned_to)
        flash("Buyurtma statusi yangilandi.", "success")
        return redirect(url_for("web_orders"))

    @app.get("/inventory")
    def web_inventory():
        user, response = _login_required(["admin", "employee"])
        if response:
            return response
        db = get_db()
        ctx = _base_context(user)
        inventory = db.get_inventory_by_warehouse(ctx["selected_warehouse"]) if ctx["selected_warehouse"] else []
        return render_template("inventory.html", **ctx, inventory=inventory)

    @app.get("/reports")
    def web_reports():
        user, response = _login_required(["admin"])
        if response:
            return response
        ctx = _base_context(user)
        stats = get_db().get_order_stats()
        return render_template("reports.html", **ctx, stats=stats)

    @app.get("/management")
    def web_management():
        user, response = _login_required(["admin"])
        if response:
            return response
        db = get_db()
        ctx = _base_context(user)
        users = db.get_all_users()
        return render_template("management.html", **ctx, users=users)

    @app.post("/management/users/<int:user_id>")
    def web_update_user(user_id):
        user, response = _login_required(["admin"])
        if response:
            return response
        role = request.form.get("role")
        password = request.form.get("password", "").strip()
        approved = request.form.get("approved") == "on"
        password_hash = generate_password_hash(password) if password else None
        get_db().update_user_access(user_id, role=role, password_hash=password_hash, approved=approved)
        flash("Foydalanuvchi yangilandi.", "success")
        return redirect(url_for("web_management"))
