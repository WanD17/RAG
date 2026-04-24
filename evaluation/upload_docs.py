"""One-time setup: register/login + upload 13 law PDFs + wait until processed.

Saves JWT token and document list to evaluation/.config.json for reuse.
"""
import json
import sys
import time
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PDF_DIR = ROOT / "Law_docs"
CONFIG_FILE = HERE / ".config.json"
BACKEND = "http://localhost:8000"

EMAIL = "eval@example.com"
PASSWORD = "EvalPassword123!"


def get_token() -> str:
    """Login, or register then login."""
    try:
        r = httpx.post(f"{BACKEND}/auth/login",
                       json={"email": EMAIL, "password": PASSWORD}, timeout=30)
        if r.status_code == 200:
            print(f"[auth] logged in as {EMAIL}")
            return r.json()["access_token"]
    except httpx.HTTPError as e:
        sys.exit(f"[auth] Cannot reach backend at {BACKEND}: {e}")

    print(f"[auth] login failed ({r.status_code}), registering...")
    r = httpx.post(f"{BACKEND}/auth/register",
                   json={"email": EMAIL, "password": PASSWORD, "full_name": "Eval Bot"},
                   timeout=30)
    if r.status_code != 201:
        sys.exit(f"[auth] register failed: {r.status_code} {r.text}")
    data = r.json()
    # register response wraps the user+token
    token = data.get("access_token") or data.get("user", {}).get("access_token")
    if not token:
        r2 = httpx.post(f"{BACKEND}/auth/login",
                        json={"email": EMAIL, "password": PASSWORD}, timeout=30)
        token = r2.json()["access_token"]
    print(f"[auth] registered and logged in")
    return token


def list_existing_docs(token: str) -> dict[str, str]:
    r = httpx.get(f"{BACKEND}/documents",
                  headers={"Authorization": f"Bearer {token}"}, timeout=30)
    r.raise_for_status()
    data = r.json()
    docs = data.get("documents") if isinstance(data, dict) else data
    return {d["filename"]: d["id"] for d in docs}


def upload_one(token: str, pdf: Path) -> str:
    with pdf.open("rb") as f:
        r = httpx.post(f"{BACKEND}/documents/upload",
                       headers={"Authorization": f"Bearer {token}"},
                       files={"file": (pdf.name, f, "application/pdf")},
                       timeout=120)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"upload failed for {pdf.name}: {r.status_code} {r.text}")
    data = r.json()
    return data["document"]["id"] if "document" in data else data["id"]


def wait_processed(token: str, doc_ids: list[str], timeout_per_doc: int = 300) -> None:
    headers = {"Authorization": f"Bearer {token}"}
    deadline = time.time() + timeout_per_doc * len(doc_ids)
    pending = set(doc_ids)
    while pending and time.time() < deadline:
        time.sleep(3)
        still_pending = set()
        for did in pending:
            try:
                r = httpx.get(f"{BACKEND}/documents/{did}", headers=headers, timeout=15)
                status = r.json().get("status", "?")
            except Exception:
                still_pending.add(did); continue
            if status in ("pending", "processing"):
                still_pending.add(did)
            elif status == "failed":
                print(f"[processing] {did[:8]} FAILED")
            else:
                print(f"[processing] {did[:8]} -> {status}")
        pending = still_pending
        if pending:
            print(f"[processing] {len(pending)} still processing...")
    if pending:
        print(f"[warn] {len(pending)} docs still not completed after timeout")


def main():
    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    if len(pdfs) != 13:
        print(f"[warn] expected 13 PDFs in {PDF_DIR}, found {len(pdfs)}")

    token = get_token()
    existing = list_existing_docs(token)
    print(f"[docs] {len(existing)} documents already in backend")

    new_doc_ids = []
    uploaded_filenames = []
    for pdf in pdfs:
        if pdf.name in existing:
            print(f"[skip] {pdf.name} already uploaded")
            uploaded_filenames.append(pdf.name)
            continue
        print(f"[upload] {pdf.name}")
        doc_id = upload_one(token, pdf)
        new_doc_ids.append(doc_id)
        uploaded_filenames.append(pdf.name)

    if new_doc_ids:
        print(f"[processing] waiting for {len(new_doc_ids)} new docs to finish embedding...")
        wait_processed(token, new_doc_ids)

    final = list_existing_docs(token)
    CONFIG_FILE.write_text(json.dumps({
        "token": token, "email": EMAIL, "backend": BACKEND,
        "documents": final,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[done] {len(final)} docs ready. Config saved to {CONFIG_FILE}")


if __name__ == "__main__":
    main()
