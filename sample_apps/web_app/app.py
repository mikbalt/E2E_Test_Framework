"""
Ankole Framework - Sample Web Application
==========================================
Flask app with session-based auth, members/roles/projects CRUD,
and multi-step project approval workflow.
"""

import os
from datetime import datetime, timezone

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

# ------------------------------------------------------------------ #
# App factory / config
# ------------------------------------------------------------------ #
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "ankole-dev-secret-key-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "postgresql://ankole:ankole@localhost:5432/ankole",
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "warning"

# ------------------------------------------------------------------ #
# Models
# ------------------------------------------------------------------ #

class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    permissions = db.Column(db.JSON, nullable=False, default=list)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    users = db.relationship("User", back_populates="role", lazy="dynamic")

    def __repr__(self):
        return f"<Role {self.name}>"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    role = db.relationship("Role", back_populates="users")
    projects = db.relationship("Project", back_populates="creator", lazy="dynamic")
    approvals = db.relationship("Approval", back_populates="approver", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role and self.role.name == "admin"

    @property
    def is_approver(self):
        return self.role and self.role.name in ("admin", "approver")

    def has_permission(self, perm):
        if self.role is None:
            return False
        return perm in (self.role.permissions or [])

    def __repr__(self):
        return f"<User {self.username}>"


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default="draft")
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    required_approvals = db.Column(db.Integer, nullable=False, default=3)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    creator = db.relationship("User", back_populates="projects")
    approvals = db.relationship("Approval", back_populates="project",
                                lazy="dynamic", order_by="Approval.step_number")

    # Valid transitions
    STATUS_OPTIONS = ["draft", "pending_approval", "approved", "rejected"]

    @property
    def approved_count(self):
        return self.approvals.filter_by(status="approved").count()

    @property
    def rejected_count(self):
        return self.approvals.filter_by(status="rejected").count()

    @property
    def current_step(self):
        """Return the next pending step number, or None if all decided."""
        pending = self.approvals.filter_by(status="pending").order_by(Approval.step_number).first()
        return pending.step_number if pending else None

    def __repr__(self):
        return f"<Project {self.name}>"


class Approval(db.Model):
    __tablename__ = "approvals"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    approver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    step_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    project = db.relationship("Project", back_populates="approvals")
    approver = db.relationship("User", back_populates="approvals")

    __table_args__ = (
        db.UniqueConstraint("project_id", "step_number", name="uq_approval_step"),
    )

    def __repr__(self):
        return f"<Approval project={self.project_id} step={self.step_number} status={self.status}>"


# ------------------------------------------------------------------ #
# Flask-Login loader
# ------------------------------------------------------------------ #

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ------------------------------------------------------------------ #
# Database initialisation helpers
# ------------------------------------------------------------------ #

def seed_database():
    """Create roles and seed users if they don't exist yet."""
    if Role.query.first() is not None:
        return  # already seeded

    # Roles
    admin_role = Role(
        name="admin",
        description="Full system administrator",
        permissions=["manage_users", "manage_roles", "manage_projects",
                     "approve_projects", "view_dashboard"],
    )
    approver_role = Role(
        name="approver",
        description="Can review and approve projects",
        permissions=["approve_projects", "view_dashboard", "view_projects"],
    )
    member_role = Role(
        name="member",
        description="Regular member who can create projects",
        permissions=["create_projects", "view_dashboard", "view_projects"],
    )
    db.session.add_all([admin_role, approver_role, member_role])
    db.session.flush()

    # Users
    seed_users = [
        ("admin",     "admin@ankole.local",     "admin123",    admin_role),
        ("approver1", "approver1@ankole.local",  "approver123", approver_role),
        ("approver2", "approver2@ankole.local",  "approver123", approver_role),
        ("approver3", "approver3@ankole.local",  "approver123", approver_role),
        ("member1",   "member1@ankole.local",    "member123",   member_role),
        ("member2",   "member2@ankole.local",    "member123",   member_role),
    ]
    for uname, email, pwd, role in seed_users:
        user = User(username=uname, email=email, role=role)
        user.set_password(pwd)
        db.session.add(user)

    db.session.commit()


# ------------------------------------------------------------------ #
# Routes - Auth
# ------------------------------------------------------------------ #

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash("Your account has been suspended.", "danger")
                return redirect(url_for("login"))
            login_user(user)
            flash("Logged in successfully.", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ------------------------------------------------------------------ #
# Routes - Dashboard
# ------------------------------------------------------------------ #

@app.route("/")
@login_required
def dashboard():
    total_members = User.query.count()
    active_members = User.query.filter_by(is_active=True).count()
    total_projects = Project.query.count()
    active_projects = Project.query.filter(
        Project.status.in_(["draft", "pending_approval"])
    ).count()
    pending_approvals = Approval.query.filter_by(status="pending").count()
    approved_projects = Project.query.filter_by(status="approved").count()

    return render_template(
        "dashboard.html",
        total_members=total_members,
        active_members=active_members,
        total_projects=total_projects,
        active_projects=active_projects,
        pending_approvals=pending_approvals,
        approved_projects=approved_projects,
    )


# ------------------------------------------------------------------ #
# Routes - Members CRUD
# ------------------------------------------------------------------ #

@app.route("/members")
@login_required
def members():
    users = User.query.order_by(User.id).all()
    return render_template("members.html", users=users)


@app.route("/members/create", methods=["GET", "POST"])
@login_required
def member_create():
    if not current_user.is_admin:
        flash("Permission denied.", "danger")
        return redirect(url_for("members"))

    roles = Role.query.order_by(Role.name).all()

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        role_id = request.form.get("role_id", type=int)

        # Validation
        errors = []
        if not username:
            errors.append("Username is required.")
        if not email:
            errors.append("Email is required.")
        if not password:
            errors.append("Password is required.")
        if User.query.filter_by(username=username).first():
            errors.append("Username already exists.")
        if User.query.filter_by(email=email).first():
            errors.append("Email already exists.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("member_form.html", roles=roles, editing=False)

        user = User(username=username, email=email, role_id=role_id)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash(f"Member '{username}' created successfully.", "success")
        return redirect(url_for("members"))

    return render_template("member_form.html", roles=roles, editing=False)


@app.route("/members/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def member_edit(user_id):
    if not current_user.is_admin:
        flash("Permission denied.", "danger")
        return redirect(url_for("members"))

    user = db.session.get(User, user_id)
    if not user:
        flash("Member not found.", "danger")
        return redirect(url_for("members"))

    roles = Role.query.order_by(Role.name).all()

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        role_id = request.form.get("role_id", type=int)

        errors = []
        if not username:
            errors.append("Username is required.")
        if not email:
            errors.append("Email is required.")
        existing = User.query.filter_by(username=username).first()
        if existing and existing.id != user.id:
            errors.append("Username already exists.")
        existing_email = User.query.filter_by(email=email).first()
        if existing_email and existing_email.id != user.id:
            errors.append("Email already exists.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("member_form.html", roles=roles, editing=True, user=user)

        user.username = username
        user.email = email
        user.role_id = role_id
        if password:
            user.set_password(password)
        db.session.commit()
        flash(f"Member '{username}' updated successfully.", "success")
        return redirect(url_for("members"))

    return render_template("member_form.html", roles=roles, editing=True, user=user)


@app.route("/members/<int:user_id>/suspend", methods=["POST"])
@login_required
def member_suspend(user_id):
    if not current_user.is_admin:
        flash("Permission denied.", "danger")
        return redirect(url_for("members"))

    user = db.session.get(User, user_id)
    if not user:
        flash("Member not found.", "danger")
        return redirect(url_for("members"))

    if user.id == current_user.id:
        flash("You cannot suspend yourself.", "warning")
        return redirect(url_for("members"))

    user.is_active = False
    db.session.commit()
    flash(f"Member '{user.username}' has been suspended.", "success")
    return redirect(url_for("members"))


@app.route("/members/<int:user_id>/reactivate", methods=["POST"])
@login_required
def member_reactivate(user_id):
    if not current_user.is_admin:
        flash("Permission denied.", "danger")
        return redirect(url_for("members"))

    user = db.session.get(User, user_id)
    if not user:
        flash("Member not found.", "danger")
        return redirect(url_for("members"))

    user.is_active = True
    db.session.commit()
    flash(f"Member '{user.username}' has been reactivated.", "success")
    return redirect(url_for("members"))


@app.route("/members/<int:user_id>/delete", methods=["POST"])
@login_required
def member_delete(user_id):
    if not current_user.is_admin:
        flash("Permission denied.", "danger")
        return redirect(url_for("members"))

    user = db.session.get(User, user_id)
    if not user:
        flash("Member not found.", "danger")
        return redirect(url_for("members"))

    if user.id == current_user.id:
        flash("You cannot delete yourself.", "warning")
        return redirect(url_for("members"))

    db.session.delete(user)
    db.session.commit()
    flash(f"Member '{user.username}' has been deleted.", "success")
    return redirect(url_for("members"))


# ------------------------------------------------------------------ #
# Routes - Roles CRUD
# ------------------------------------------------------------------ #

@app.route("/roles")
@login_required
def roles():
    if not current_user.is_admin:
        flash("Permission denied.", "danger")
        return redirect(url_for("dashboard"))

    all_roles = Role.query.order_by(Role.id).all()
    return render_template("roles.html", roles=all_roles)


@app.route("/roles/create", methods=["GET", "POST"])
@login_required
def role_create():
    if not current_user.is_admin:
        flash("Permission denied.", "danger")
        return redirect(url_for("roles"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        permissions_raw = request.form.get("permissions", "").strip()
        permissions = [p.strip() for p in permissions_raw.split(",") if p.strip()] if permissions_raw else []

        if not name:
            flash("Role name is required.", "danger")
            return render_template("role_form.html", editing=False)

        if Role.query.filter_by(name=name).first():
            flash("Role name already exists.", "danger")
            return render_template("role_form.html", editing=False)

        role = Role(name=name, description=description, permissions=permissions)
        db.session.add(role)
        db.session.commit()
        flash(f"Role '{name}' created successfully.", "success")
        return redirect(url_for("roles"))

    return render_template("role_form.html", editing=False)


@app.route("/roles/<int:role_id>/edit", methods=["GET", "POST"])
@login_required
def role_edit(role_id):
    if not current_user.is_admin:
        flash("Permission denied.", "danger")
        return redirect(url_for("roles"))

    role = db.session.get(Role, role_id)
    if not role:
        flash("Role not found.", "danger")
        return redirect(url_for("roles"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        permissions_raw = request.form.get("permissions", "").strip()
        permissions = [p.strip() for p in permissions_raw.split(",") if p.strip()] if permissions_raw else []

        if not name:
            flash("Role name is required.", "danger")
            return render_template("role_form.html", editing=True, role=role)

        existing = Role.query.filter_by(name=name).first()
        if existing and existing.id != role.id:
            flash("Role name already exists.", "danger")
            return render_template("role_form.html", editing=True, role=role)

        role.name = name
        role.description = description
        role.permissions = permissions
        db.session.commit()
        flash(f"Role '{name}' updated successfully.", "success")
        return redirect(url_for("roles"))

    return render_template("role_form.html", editing=True, role=role)


@app.route("/roles/<int:role_id>/delete", methods=["POST"])
@login_required
def role_delete(role_id):
    if not current_user.is_admin:
        flash("Permission denied.", "danger")
        return redirect(url_for("roles"))

    role = db.session.get(Role, role_id)
    if not role:
        flash("Role not found.", "danger")
        return redirect(url_for("roles"))

    if role.users.count() > 0:
        flash("Cannot delete a role that has users assigned.", "danger")
        return redirect(url_for("roles"))

    db.session.delete(role)
    db.session.commit()
    flash(f"Role '{role.name}' has been deleted.", "success")
    return redirect(url_for("roles"))


# ------------------------------------------------------------------ #
# Routes - Projects CRUD + Approval workflow
# ------------------------------------------------------------------ #

@app.route("/projects")
@login_required
def projects():
    all_projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template("projects.html", projects=all_projects)


@app.route("/projects/create", methods=["GET", "POST"])
@login_required
def project_create():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        required_approvals = request.form.get("required_approvals", 3, type=int)

        if not name:
            flash("Project name is required.", "danger")
            return render_template("project_form.html")

        project = Project(
            name=name,
            description=description,
            status="draft",
            created_by=current_user.id,
            required_approvals=required_approvals,
        )
        db.session.add(project)
        db.session.commit()
        flash(f"Project '{name}' created successfully.", "success")
        return redirect(url_for("project_detail", project_id=project.id))

    return render_template("project_form.html")


@app.route("/projects/<int:project_id>")
@login_required
def project_detail(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        flash("Project not found.", "danger")
        return redirect(url_for("projects"))

    approval_steps = project.approvals.order_by(Approval.step_number).all()
    return render_template("project_detail.html", project=project, approval_steps=approval_steps)


@app.route("/projects/<int:project_id>/submit", methods=["POST"])
@login_required
def project_submit(project_id):
    """Submit a draft project for approval - creates approval step rows."""
    project = db.session.get(Project, project_id)
    if not project:
        flash("Project not found.", "danger")
        return redirect(url_for("projects"))

    if project.status != "draft":
        flash("Only draft projects can be submitted for approval.", "warning")
        return redirect(url_for("project_detail", project_id=project.id))

    # Get available approvers
    approver_role = Role.query.filter_by(name="approver").first()
    admin_role = Role.query.filter_by(name="admin").first()
    approver_ids = []
    if approver_role:
        approver_ids.extend(
            [u.id for u in User.query.filter_by(role_id=approver_role.id, is_active=True).all()]
        )
    if admin_role:
        approver_ids.extend(
            [u.id for u in User.query.filter_by(role_id=admin_role.id, is_active=True).all()]
        )

    # Remove duplicates and the creator
    approver_ids = list(dict.fromkeys(approver_ids))
    approver_ids = [aid for aid in approver_ids if aid != project.created_by]

    needed = min(project.required_approvals, len(approver_ids))
    if needed == 0:
        flash("No approvers available.", "danger")
        return redirect(url_for("project_detail", project_id=project.id))

    # Create approval steps
    for step, approver_id in enumerate(approver_ids[:needed], start=1):
        approval = Approval(
            project_id=project.id,
            approver_id=approver_id,
            step_number=step,
            status="pending",
        )
        db.session.add(approval)

    project.status = "pending_approval"
    db.session.commit()
    flash("Project submitted for approval.", "success")
    return redirect(url_for("project_detail", project_id=project.id))


@app.route("/projects/<int:project_id>/approve/<int:approval_id>", methods=["POST"])
@login_required
def project_approve(project_id, approval_id):
    approval = db.session.get(Approval, approval_id)
    if not approval or approval.project_id != project_id:
        flash("Approval step not found.", "danger")
        return redirect(url_for("projects"))

    if approval.approver_id != current_user.id:
        flash("You are not assigned to this approval step.", "danger")
        return redirect(url_for("project_detail", project_id=project_id))

    if approval.status != "pending":
        flash("This step has already been decided.", "warning")
        return redirect(url_for("project_detail", project_id=project_id))

    comment = request.form.get("comment", "").strip()
    approval.status = "approved"
    approval.comment = comment if comment else None

    project = approval.project

    # Check if all required approvals are met
    approved_count = project.approvals.filter_by(status="approved").count()
    if approved_count >= project.required_approvals:
        project.status = "approved"

    db.session.commit()

    if project.status == "approved":
        flash("Project has been fully approved!", "success")
    else:
        flash("Approval step completed.", "success")

    return redirect(url_for("project_detail", project_id=project_id))


@app.route("/projects/<int:project_id>/reject/<int:approval_id>", methods=["POST"])
@login_required
def project_reject(project_id, approval_id):
    approval = db.session.get(Approval, approval_id)
    if not approval or approval.project_id != project_id:
        flash("Approval step not found.", "danger")
        return redirect(url_for("projects"))

    if approval.approver_id != current_user.id:
        flash("You are not assigned to this approval step.", "danger")
        return redirect(url_for("project_detail", project_id=project_id))

    if approval.status != "pending":
        flash("This step has already been decided.", "warning")
        return redirect(url_for("project_detail", project_id=project_id))

    comment = request.form.get("comment", "").strip()
    approval.status = "rejected"
    approval.comment = comment if comment else None

    project = approval.project
    project.status = "rejected"
    db.session.commit()

    flash("Project has been rejected.", "danger")
    return redirect(url_for("project_detail", project_id=project_id))


@app.route("/projects/<int:project_id>/delete", methods=["POST"])
@login_required
def project_delete(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        flash("Project not found.", "danger")
        return redirect(url_for("projects"))

    if project.created_by != current_user.id and not current_user.is_admin:
        flash("Permission denied.", "danger")
        return redirect(url_for("projects"))

    db.session.delete(project)
    db.session.commit()
    flash(f"Project '{project.name}' has been deleted.", "success")
    return redirect(url_for("projects"))


# ------------------------------------------------------------------ #
# Health endpoint
# ------------------------------------------------------------------ #

@app.route("/health")
def health():
    try:
        db.session.execute(db.text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    return {"status": "ok", "database": db_status}


# ------------------------------------------------------------------ #
# Startup
# ------------------------------------------------------------------ #

with app.app_context():
    db.create_all()
    seed_database()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
