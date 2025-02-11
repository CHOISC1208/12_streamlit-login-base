import streamlit as st
from streamlit_option_menu import option_menu
from util import *
from ui import *
from PIL import Image

def main():
    auth_manager = AuthManager()
    auth_manager.initialize_session_state()

    # カスタムCSS
    st.markdown("""
        <style>
        .sidebar-image {
            display: flex;
            justify-content: center;
            margin: 0 auto;
        }
        div[data-testid="stForm"] {
            max-width: 400px;
            margin: 0 auto;
        }
        </style>
    """, unsafe_allow_html=True)

    try:
        logo = Image.open("assets/images/logo.png")
    except FileNotFoundError:
        st.error("ロゴ画像が見つかりません")
        return

    if not auth_manager.is_logged_in:
        # ログイン画面のレイアウト
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.image(logo, width=100, use_column_width=True)
            
            # ログインフォーム
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True)
                
                if submitted:
                    if auth_manager.login(username, password):
                        st.success("ログインに成功しました")
                        st.rerun()
                    else:
                        st.error("ユーザー名またはパスワードが間違っています")
    else:
        # サイドバーのロゴ表示
        st.sidebar.markdown(
            f'<div class="sidebar-image">',
            unsafe_allow_html=True
        )
        st.sidebar.image(logo, width=100, use_column_width=True)
        st.sidebar.markdown('</div>', unsafe_allow_html=True)
        
        st.sidebar.title(f"ようこそ {auth_manager.current_user} さん")
        
        if st.sidebar.button("Logout"):
            auth_manager.logout()

        pages = [
            {"label": "01_page1", "icon": "cloud-sun", "function": page_01},
            {"label": "02_page2", "icon": "stars", "function": page_02},
            {"label": "03_page3", "icon": "palette", "function": page_03},
            {"label": "04_page4", "icon": "gem", "function": page_04},
            {"label": "05_page5", "icon": "flower2", "function": page_05},
        ]

        with st.sidebar:
            selected = option_menu(
                "Menu",
                [page["label"] for page in pages],
                icons=['house', 'gear', 'list-task', 'graph-up', 'person'],
                menu_icon="cast",
                default_index=0,
            )

        for page in pages:
            if selected == page["label"]:
                page["function"]()
                break

if __name__ == "__main__":
    main()
