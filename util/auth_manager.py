# util/auth_manager.py

import streamlit as st
import yaml
from typing import Dict, Optional

class AuthManager:
    def __init__(self):
        self.users = self._load_config()

    def _load_config(self) -> Dict:
        """設定ファイルからユーザー情報を読み込む"""
        try:
            with open("configs/login.yaml", "r") as file:
                config = yaml.safe_load(file)
                return config["login"]["users"]
        except Exception as e:
            st.error(f"設定ファイルの読み込みに失敗しました: {str(e)}")
            return {}

    def validate_login(self, username: str, password: str) -> bool:
        """ログイン認証を行う"""
        for user in self.users:
            if user["username"] == username and user["password"] == password:
                return True
        return False

    def initialize_session_state(self):
        """セッション状態を初期化"""
        if "loggedin" not in st.session_state:
            st.session_state.loggedin = False
            st.session_state.username = None

    def login(self, username: str, password: str) -> bool:
        """ログイン処理"""
        if self.validate_login(username, password):
            st.session_state.loggedin = True
            st.session_state.username = username
            return True
        return False

    def logout(self):
        """ログアウト処理"""
        st.session_state.loggedin = False
        st.session_state.username = None
        st.rerun()  # experimental_rerunをrerunに変更

    @property
    def is_logged_in(self) -> bool:
        """ログイン状態を確認"""
        return st.session_state.get('loggedin', False)

    @property
    def current_user(self) -> Optional[str]:
        """現在のユーザー名を取得"""
        return st.session_state.get('username', None)