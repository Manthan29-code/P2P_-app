from __future__ import annotations

import secrets
import string
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict

import streamlit as st


CODE_LENGTH = 8
EXPIRY_MINUTES = 30
MAX_FILE_MB = 200
MAX_FILE_BYTES = MAX_FILE_MB * 1024 * 1024
CODE_ALPHABET = string.ascii_uppercase + string.digits


@dataclass
class RelayFile:
    file_name: str
    file_bytes: bytes
    mime_type: str
    created_at: datetime
    expires_at: datetime
    delete_after_download: bool


@dataclass
class SharedVault:
    files: Dict[str, RelayFile]
    lock: threading.Lock


@st.cache_resource
def get_shared_vault() -> SharedVault:
    return SharedVault(files={}, lock=threading.Lock())


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def generate_code(existing_codes: set[str]) -> str:
    while True:
        code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))
        if code not in existing_codes:
            return code


def cleanup_expired_files(vault: SharedVault) -> int:
    current_time = now_utc()
    with vault.lock:
        expired_codes = [
            code for code, relay_file in vault.files.items()
            if relay_file.expires_at <= current_time
        ]
        for code in expired_codes:
            del vault.files[code]
    return len(expired_codes)


def format_size(size_bytes: int) -> str:
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    if size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes} bytes"


def store_file(uploaded_file, delete_after_download: bool) -> str:
    file_bytes = uploaded_file.getvalue()
    if not file_bytes:
        raise ValueError("upload_missing")
    if len(file_bytes) > MAX_FILE_BYTES:
        raise ValueError("file_too_large")

    vault = get_shared_vault()
    cleanup_expired_files(vault)
    created_at = now_utc()
    expires_at = created_at + timedelta(minutes=EXPIRY_MINUTES)

    with vault.lock:
        code = generate_code(set(vault.files.keys()))
        vault.files[code] = RelayFile(
            file_name=uploaded_file.name or "download",
            file_bytes=file_bytes,
            mime_type=uploaded_file.type or "application/octet-stream",
            created_at=created_at,
            expires_at=expires_at,
            delete_after_download=delete_after_download,
        )
    return code


def get_file_for_code(code: str) -> tuple[RelayFile | None, str | None]:
    cleaned_code = code.strip().upper()
    if not cleaned_code:
        return None, "Enter a share code first."

    vault = get_shared_vault()
    cleanup_expired_files(vault)

    with vault.lock:
        relay_file = vault.files.get(cleaned_code)
        if relay_file is None:
            return None, "Invalid or expired code."
        if relay_file.expires_at <= now_utc():
            del vault.files[cleaned_code]
            return None, "This code has expired."
        return relay_file, None


def delete_code(code: str) -> None:
    cleaned_code = code.strip().upper()
    vault = get_shared_vault()
    with vault.lock:
        vault.files.pop(cleaned_code, None)


def mark_downloaded_and_delete(code: str) -> None:
    cleaned_code = code.strip().upper()
    st.session_state["downloaded_code"] = cleaned_code
    delete_code(cleaned_code)


def active_transfer_count() -> int:
    vault = get_shared_vault()
    cleanup_expired_files(vault)
    with vault.lock:
        return len(vault.files)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            :root {
                --ink: #111111;
                --soft-ink: #3f3f46;
                --line: #d4d4d8;
                --panel: #f4f4f5;
                --paper: #ffffff;
            }

            .stApp {
                background: var(--paper);
                color: var(--ink);
            }

            [data-testid="stHeader"] {
                background: rgba(255, 255, 255, 0.88);
                backdrop-filter: blur(10px);
            }

            .block-container {
                max-width: 980px;
                padding-top: 3rem;
                padding-bottom: 4rem;
            }

            h1, h2, h3, p, label, span {
                letter-spacing: 0;
            }

            h1 {
                font-size: clamp(2rem, 4vw, 3.75rem);
                font-weight: 800;
                color: var(--ink);
            }

            h2, h3 {
                color: var(--ink);
            }

            .hero-copy {
                color: var(--soft-ink);
                font-size: 1.05rem;
                line-height: 1.65;
                max-width: 720px;
            }

            .status-strip {
                border: 1px solid var(--line);
                background: var(--panel);
                color: var(--ink);
                padding: 0.85rem 1rem;
                border-radius: 8px;
                margin: 1.25rem 0 1.75rem;
                font-weight: 650;
            }

            .share-code {
                border: 2px solid var(--ink);
                background: var(--paper);
                color: var(--ink);
                padding: 1rem;
                border-radius: 8px;
                font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
                font-size: clamp(1.55rem, 6vw, 2.6rem);
                font-weight: 800;
                text-align: center;
                letter-spacing: 0.2rem;
            }

            div[data-testid="stFileUploader"] section {
                border: 1px dashed #71717a;
                background: #fafafa;
                border-radius: 8px;
            }

            .stButton > button,
            .stDownloadButton > button {
                background: var(--ink);
                color: var(--paper);
                border: 1px solid var(--ink);
                border-radius: 8px;
                min-height: 2.75rem;
                font-weight: 750;
                transition:
                    transform 120ms ease,
                    box-shadow 120ms ease,
                    background-color 120ms ease,
                    color 120ms ease;
                box-shadow: 0 6px 0 #9ca3af;
            }

            .stButton > button:hover,
            .stDownloadButton > button:hover {
                background: #2f2f33;
                color: var(--paper);
                border-color: #2f2f33;
                transform: translateY(-1px);
                box-shadow: 0 7px 0 #9ca3af;
            }

            .stButton > button:active,
            .stDownloadButton > button:active {
                transform: translateY(5px);
                box-shadow: 0 1px 0 #9ca3af;
            }

            .stTextInput input {
                border-radius: 8px;
                border: 1px solid var(--line);
                color: var(--ink);
                text-transform: uppercase;
            }

            .stCheckbox label {
                color: var(--ink);
            }

            div[data-testid="stMetric"] {
                border: 1px solid var(--line);
                background: var(--panel);
                border-radius: 8px;
                padding: 0.8rem 1rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sender() -> None:
    st.subheader("Send")
    uploaded_file = st.file_uploader(
        "Choose a file",
        help=f"Maximum supported file size is {MAX_FILE_MB} MB.",
    )
    delete_after_download = st.checkbox(
        "Delete after first download",
        value=True,
        help="Removes the file from server memory when the receiver clicks download.",
    )

    if uploaded_file is None:
        st.info("Upload a file to create a temporary share code.")
        return

    file_size = len(uploaded_file.getvalue())
    st.caption(f"Selected: {uploaded_file.name} - {format_size(file_size)}")

    if file_size > MAX_FILE_BYTES:
        st.error(f"File too large. This app accepts files up to {MAX_FILE_MB} MB.")
        return

    if st.button("Create share code", use_container_width=True):
        try:
            code = store_file(uploaded_file, delete_after_download)
        except ValueError as exc:
            if str(exc) == "file_too_large":
                st.error(f"File too large. This app accepts files up to {MAX_FILE_MB} MB.")
            else:
                st.error("Upload missing. Please choose a file before creating a code.")
            return
        st.session_state["latest_code"] = code

    latest_code = st.session_state.get("latest_code")
    if latest_code:
        relay_file, error = get_file_for_code(latest_code)
        if relay_file and not error:
            minutes_left = max(
                0,
                int((relay_file.expires_at - now_utc()).total_seconds() // 60),
            )
            st.success("Share code ready.")
            st.markdown(f'<div class="share-code">{latest_code}</div>', unsafe_allow_html=True)
            st.caption(f"Expires in about {minutes_left} minutes.")
        else:
            st.warning("Your previous share code is no longer active.")


def render_receiver() -> None:
    st.subheader("Receive")
    code = st.text_input(
        "Enter share code",
        max_chars=CODE_LENGTH,
        placeholder="AB12CD34",
    )

    if not code:
        st.info("Enter the sender's code to unlock the file.")
        return

    relay_file, error = get_file_for_code(code)
    if error:
        if st.session_state.get("downloaded_code") == code.strip().upper():
            st.success("Download started. The file was removed from memory.")
            st.caption("Enter a different code to receive another file.")
            return
        st.error(error)
        return

    assert relay_file is not None
    seconds_left = max(0, int((relay_file.expires_at - now_utc()).total_seconds()))
    st.success(f"File ready: {relay_file.file_name} ({format_size(len(relay_file.file_bytes))})")
    st.caption(f"Code expires in {seconds_left // 60} minutes {seconds_left % 60} seconds.")

    cleaned_code = code.strip().upper()
    if relay_file.delete_after_download:
        st.download_button(
            "Download file",
            data=relay_file.file_bytes,
            file_name=relay_file.file_name,
            mime=relay_file.mime_type,
            use_container_width=True,
            on_click=mark_downloaded_and_delete,
            args=(cleaned_code,),
        )
        st.caption("This file will be removed from memory after the download click.")
    else:
        st.download_button(
            "Download file",
            data=relay_file.file_bytes,
            file_name=relay_file.file_name,
            mime=relay_file.mime_type,
            use_container_width=True,
        )


def main() -> None:
    st.set_page_config(
        page_title="Cloud File Relay",
        page_icon="CF",
        layout="wide",
    )
    inject_styles()

    cleanup_count = cleanup_expired_files(get_shared_vault())

    st.title("Cloud File Relay")
    st.markdown(
        """
        <p class="hero-copy">
        Transfer a file between two devices through this Streamlit app. Files stay in
        temporary server memory, use hard-to-guess share codes, and expire automatically.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="status-strip">
            Active transfers: {active_transfer_count()} &nbsp; | &nbsp;
            Expiry: {EXPIRY_MINUTES} minutes &nbsp; | &nbsp;
            Max file: {MAX_FILE_MB} MB
            {"&nbsp; | &nbsp; Cleaned expired files: " + str(cleanup_count) if cleanup_count else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

    send_column, receive_column = st.columns(2, gap="large")
    with send_column:
        render_sender()
    with receive_column:
        render_receiver()


if __name__ == "__main__":
    main()
