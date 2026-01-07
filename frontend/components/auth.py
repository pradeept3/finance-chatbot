# ============================================================================
# frontend/components/auth.py - Login Authentication System
# ============================================================================

import streamlit as st
import hashlib
import json
import os
from datetime import datetime
import base64

def load_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# User database file path
USER_DB_PATH = "user_database.json"

image_path = os.path.join(os.path.dirname(__file__), "..", "static", "Santa Clara University.png")
# Default users (Admin and some students)
DEFAULT_USERS = {
    "admin": {
        "password": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "admin",
        "name": "Administrator",
        "email": "admin@financechatbot.com"
    },
    "student1": {
        "password": hashlib.sha256("student123".encode()).hexdigest(),
        "role": "student",
        "name": "John Doe",
        "email": "john@student.com"
    },
    "student2": {
        "password": hashlib.sha256("student123".encode()).hexdigest(),
        "role": "student",
        "name": "Jane Smith",
        "email": "jane@student.com"
    }
}


def init_user_database():
    """Initialize user database if it doesn't exist"""
    if not os.path.exists(USER_DB_PATH):
        with open(USER_DB_PATH, 'w') as f:
            json.dump(DEFAULT_USERS, f, indent=4)
        print(f"[Auth] Created user database at {USER_DB_PATH}")
    return load_user_database()


def load_user_database():
    """Load user database from JSON file"""
    try:
        with open(USER_DB_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[Auth] Error loading user database: {e}")
        return DEFAULT_USERS


def save_user_database(users):
    """Save user database to JSON file"""
    try:
        with open(USER_DB_PATH, 'w') as f:
            json.dump(users, f, indent=4)
        return True
    except Exception as e:
        print(f"[Auth] Error saving user database: {e}")
        return False


def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate_user(username, password):
    """Authenticate user credentials"""
    users = load_user_database()
    
    if username in users:
        hashed_password = hash_password(password)
        if users[username]["password"] == hashed_password:
            return {
                "username": username,
                "role": users[username]["role"],
                "name": users[username]["name"],
                "email": users[username]["email"]
            }
    return None


def add_new_user(username, password, role, name, email):
    """Add new user to database (Admin only)"""
    users = load_user_database()
    
    if username in users:
        return False, "Username already exists"
    
    users[username] = {
        "password": hash_password(password),
        "role": role,
        "name": name,
        "email": email
    }
    
    if save_user_database(users):
        return True, "User added successfully"
    return False, "Failed to save user"


def delete_user(username):
    """Delete user from database (Admin only)"""
    if username == "admin":
        return False, "Cannot delete admin account"
    
    users = load_user_database()
    
    if username not in users:
        return False, "User not found"
    
    del users[username]
    
    if save_user_database(users):
        return True, "User deleted successfully"
    return False, "Failed to delete user"


def change_password(username, old_password, new_password):
    """Change user password"""
    users = load_user_database()
    
    if username not in users:
        return False, "User not found"
    
    if users[username]["password"] != hash_password(old_password):
        return False, "Incorrect old password"
    
    users[username]["password"] = hash_password(new_password)
    
    if save_user_database(users):
        return True, "Password changed successfully"
    return False, "Failed to change password"


def login_page():
    """Display login page"""
    image_file = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "static", "scu_logo.png")
    )

    encoded_image = load_base64_image(image_file)

    st.markdown(
        f"""
        <div style="text-align: center; padding: 2rem 0;">
            <h1 style="font-size: 3rem; margin-bottom: 0.5rem;">
                <img src="data:image/png;base64,{encoded_image}" 
                     style="height: 3rem;">
            </h1>
            <h2 style="color: #667eea; margin-bottom: 0.5rem;">Finance Chatbot Login</h2>
            <p style="color: #64748b; font-size: 1.1rem;">Please sign in to continue</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Create centered login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(
            """
            <div style="background: #b30738; padding: 2rem; border-radius: 16px; 
                        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1); border: 2px solid #e0e7ff;">
            </div>
            """,
            unsafe_allow_html=True
        )
        
        with st.form("login_form", clear_on_submit=False):
            st.markdown("### 👤 Sign In")
            
            username = st.text_input(
                "Username",
                placeholder="Enter your username",
                key="login_username"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password"
            )
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                submit = st.form_submit_button(
                    "🚀 Login",
                    use_container_width=True,
                    type="primary"
                )
            
            with col_b:
                guest = st.form_submit_button(
                    "👤 Guest Mode",
                    use_container_width=True
                )
            
            if submit:
                if not username or not password:
                    st.error("⚠️ Please enter both username and password")
                else:
                    user = authenticate_user(username, password)
                    
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.session_state.login_time = datetime.now()
                        st.success(f"✅ Welcome back, {user['name']}!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
            
            if guest:
                st.session_state.authenticated = True
                st.session_state.user = {
                    "username": "guest",
                    "role": "student",
                    "name": "Guest User",
                    "email": "guest@example.com"
                }
                st.session_state.login_time = datetime.now()
                st.info("ℹ️ Logged in as Guest (Student Mode)")
                st.rerun()
        
        # Login hints
        with st.expander("🔑 Login Credentials (Demo)"):
            st.markdown("""
            **Admin Account:**
            - Username: `admin`
            - Password: `admin123`
            
            **Student Accounts:**
            - Username: `student1` | Password: `student123`
            - Username: `student2` | Password: `student123`
            
            **Or use Guest Mode for quick access**
            """)


def logout():
    """Logout current user"""
    if "user" in st.session_state:
        username = st.session_state.user.get("name", "User")
        del st.session_state.authenticated
        del st.session_state.user
        if "login_time" in st.session_state:
            del st.session_state.login_time
        st.success(f"👋 Goodbye, {username}!")
        st.rerun()


def user_profile_sidebar():
    """Display user profile in sidebar"""
    if not st.session_state.get("authenticated", False):
        return
    
    user = st.session_state.user
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 👤 User Profile")
    
    # User info card
    role_icon = "👑" if user["role"] == "admin" else "🎓"
    role_color = "#667eea" if user["role"] == "admin" else "#22c55e"
    
    st.sidebar.markdown(
        f"""
        <div style="background: linear-gradient(135deg, {role_color}15 0%, {role_color}05 100%);
                    padding: 1rem; border-radius: 12px; border-left: 4px solid {role_color};
                    margin-bottom: 1rem;">
            <div style="font-size: 2rem; text-align: center; margin-bottom: 0.5rem;">{role_icon}</div>
            <div style="text-align: center;">
                <strong style="font-size: 1.1rem;">{user['name']}</strong><br>
                <span style="color: #64748b; font-size: 0.9rem;">{user['email']}</span><br>
                <span style="background: {role_color}; color: white; padding: 0.25rem 0.75rem;
                       border-radius: 999px; font-size: 0.8rem; font-weight: 600;
                       display: inline-block; margin-top: 0.5rem;">
                    {user['role'].upper()}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Session info
    if "login_time" in st.session_state:
        login_time = st.session_state.login_time
        st.sidebar.caption(f"🕒 Logged in: {login_time.strftime('%I:%M %p')}")
    
    # Logout button
    if st.sidebar.button("🚪 Logout", use_container_width=True, type="primary"):
        logout()


def admin_user_management():
    """Admin panel for user management"""
    # st.markdown("### 👥 User Management")
    
    users = load_user_database()
    
    # Statistics
    col1, col2, col3 = st.columns(3)
    
    admin_count = sum(1 for u in users.values() if u["role"] == "admin")
    student_count = sum(1 for u in users.values() if u["role"] == "student")
    
    with col1:
        st.metric("Total Users", len(users))
    with col2:
        st.metric("Admins", admin_count)
    with col3:
        st.metric("Students", student_count)
    
    st.markdown("---")
    
    # Tabs for different operations
    tab1, tab2, tab3 = st.tabs(["📋 View Users", "➕ Add User", "🔐 Change Password"])
    
    with tab1:
        st.markdown("#### 📋 All Users")
        
        for username, user_data in users.items():
            role_icon = "👑" if user_data["role"] == "admin" else "🎓"
            role_color = "#667eea" if user_data["role"] == "admin" else "#22c55e"
            
            col_a, col_b = st.columns([4, 1])
            
            with col_a:
                st.markdown(
                    f"""
                    <div style="background: white; padding: 1rem; border-radius: 12px;
                                border-left: 4px solid {role_color}; margin-bottom: 0.5rem;">
                        {role_icon} <strong>{user_data['name']}</strong> (@{username})<br>
                        <span style="color: #64748b; font-size: 0.9rem;">
                            📧 {user_data['email']} | 
                            <span style="background: {role_color}; color: white; padding: 0.2rem 0.6rem;
                                   border-radius: 999px; font-size: 0.75rem;">
                                {user_data['role'].upper()}
                            </span>
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            with col_b:
                if username != "admin" and username != st.session_state.user["username"]:
                    if st.button("🗑️", key=f"del_{username}", help=f"Delete {username}"):
                        success, message = delete_user(username)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
    
    with tab2:
        st.markdown("#### ➕ Add New User")
        
        with st.form("add_user_form"):
            new_username = st.text_input("Username", placeholder="student3")
            new_name = st.text_input("Full Name", placeholder="John Doe")
            new_email = st.text_input("Email", placeholder="john@student.com")
            new_password = st.text_input("Password", type="password", placeholder="********")
            new_role = st.selectbox("Role", ["student", "admin"])
            
            submit = st.form_submit_button("➕ Add User", type="primary")
            
            if submit:
                if not all([new_username, new_name, new_email, new_password]):
                    st.error("⚠️ Please fill in all fields")
                else:
                    success, message = add_new_user(
                        new_username, new_password, new_role, new_name, new_email
                    )
                    if success:
                        st.success(f"✅ {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
    
    with tab3:
        st.markdown("#### 🔐 Change Password")
        
        with st.form("change_password_form"):
            current_user = st.session_state.user["username"]
            
            st.info(f"Changing password for: **{current_user}**")
            
            old_pwd = st.text_input("Current Password", type="password")
            new_pwd = st.text_input("New Password", type="password")
            confirm_pwd = st.text_input("Confirm New Password", type="password")
            
            submit = st.form_submit_button("🔐 Change Password", type="primary")
            
            if submit:
                if not all([old_pwd, new_pwd, confirm_pwd]):
                    st.error("⚠️ Please fill in all fields")
                elif new_pwd != confirm_pwd:
                    st.error("❌ New passwords don't match")
                elif len(new_pwd) < 6:
                    st.error("❌ Password must be at least 6 characters")
                else:
                    success, message = change_password(current_user, old_pwd, new_pwd)
                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")


def check_authentication():
    """Check if user is authenticated"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        login_page()
        st.stop()


def is_admin():
    """Check if current user is admin"""
    if not st.session_state.get("authenticated", False):
        return False
    return st.session_state.user.get("role") == "admin"


def is_student():
    """Check if current user is student"""
    if not st.session_state.get("authenticated", False):
        return False
    return st.session_state.user.get("role") == "student"


# Initialize user database on import
init_user_database()