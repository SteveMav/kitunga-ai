from __future__ import annotations

import argparse
import io
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk

import requests

from api_client import api_url, finish_basket, get_basket, start_basket
from config import API_BASE_URL, API_TIMEOUT_SECONDS, BASKET_CODE, BASKET_CODE_FILE, DEVICE_ID

QR_DISPLAY_SIZE = 260

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None


class BasketScreenApp:
    def __init__(self, root: tk.Tk, args: argparse.Namespace):
        self.root = root
        self.args = args
        self.api_base_url = args.api_base_url
        self.poll_interval_ms = int(args.poll_interval * 1000)
        self.qr_image = None
        self.current_basket = None
        self.loading = False

        self.basket_code_file = Path(args.basket_code_file) if args.basket_code_file else None
        self.basket_code_var = tk.StringVar(value=self.read_shared_basket_code(args.basket_code))
        self.status_var = tk.StringVar(value="offline")
        self.total_var = tk.StringVar(value="0.00 USD")
        self.message_var = tk.StringVar(value="En attente du backend Kitunga AI")
        self.checkout_var = tk.StringVar(value="")

        self.configure_window()
        self.build_ui()
        self.refresh_async()
        self.schedule_refresh()

    def configure_window(self) -> None:
        self.root.title("Kitunga AI - Ecran client")
        self.root.geometry(self.args.geometry)
        self.root.minsize(720, 420)
        if self.args.fullscreen:
            self.root.attributes("-fullscreen", True)
        self.root.bind("<Escape>", lambda _event: self.root.attributes("-fullscreen", False))

    def build_ui(self) -> None:
        self.root.configure(bg="#eef6f2")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", rowheight=34, font=("Segoe UI", 11))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        shell = tk.Frame(self.root, bg="#eef6f2", padx=20, pady=16)
        shell.pack(fill="both", expand=True)

        header = tk.Frame(shell, bg="#eef6f2")
        header.pack(fill="x")

        title = tk.Label(
            header,
            text="Kitunga AI",
            bg="#eef6f2",
            fg="#071b16",
            font=("Segoe UI", 28, "bold"),
        )
        title.pack(side="left")

        status = tk.Label(
            header,
            textvariable=self.status_var,
            bg="#dff2e8",
            fg="#0c5f3f",
            padx=14,
            pady=7,
            font=("Segoe UI", 11, "bold"),
        )
        status.pack(side="right")

        controls = tk.Frame(shell, bg="#eef6f2", pady=12)
        controls.pack(fill="x")

        tk.Label(controls, text="Panier", bg="#eef6f2", fg="#36544b", font=("Segoe UI", 10, "bold")).pack(side="left")
        basket_entry = tk.Entry(controls, textvariable=self.basket_code_var, width=14, font=("Segoe UI", 13))
        basket_entry.pack(side="left", padx=(8, 10))

        tk.Button(controls, text="Rafraichir", command=self.refresh_async, font=("Segoe UI", 11, "bold")).pack(
            side="left", padx=4
        )
        tk.Button(controls, text="Nouvelle session", command=self.start_session_async, font=("Segoe UI", 11, "bold")).pack(
            side="left", padx=4
        )
        tk.Button(controls, text="Terminer le panier", command=self.finish_session_async, font=("Segoe UI", 11, "bold")).pack(
            side="left", padx=4
        )

        body = tk.Frame(shell, bg="#eef6f2")
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg="#ffffff", padx=12, pady=12, highlightthickness=1, highlightbackground="#c4d8d0")
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        tk.Label(left, text="Objets detectes", bg="#ffffff", fg="#064d34", font=("Segoe UI", 13, "bold")).pack(
            anchor="w"
        )

        columns = ("product", "quantity", "unit_price", "subtotal")
        self.items_tree = ttk.Treeview(left, columns=columns, show="headings", height=8)
        self.items_tree.heading("product", text="Produit")
        self.items_tree.heading("quantity", text="Qte")
        self.items_tree.heading("unit_price", text="Prix")
        self.items_tree.heading("subtotal", text="Sous-total")
        self.items_tree.column("product", width=270)
        self.items_tree.column("quantity", width=70, anchor="center")
        self.items_tree.column("unit_price", width=90, anchor="e")
        self.items_tree.column("subtotal", width=110, anchor="e")
        self.items_tree.pack(fill="both", expand=True, pady=(10, 0))

        right = tk.Frame(body, bg="#ffffff", padx=14, pady=14, highlightthickness=1, highlightbackground="#c4d8d0")
        right.pack(side="right", fill="y")

        tk.Label(right, text="Total", bg="#ffffff", fg="#064d34", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        tk.Label(right, textvariable=self.total_var, bg="#ffffff", fg="#071b16", font=("Segoe UI", 28, "bold")).pack(
            anchor="w", pady=(4, 16)
        )

        self.qr_frame = tk.Frame(
            right,
            bg="#f3faf7",
            width=QR_DISPLAY_SIZE,
            height=QR_DISPLAY_SIZE,
            highlightthickness=1,
            highlightbackground="#d6e5df",
        )
        self.qr_frame.pack(anchor="center")
        self.qr_frame.pack_propagate(False)
        self.qr_label = tk.Label(
            self.qr_frame,
            text="QR code apres finalisation",
            bg="#f3faf7",
            fg="#526a62",
            wraplength=220,
            justify="center",
        )
        self.qr_label.pack(fill="both", expand=True)

        tk.Label(
            right,
            textvariable=self.checkout_var,
            bg="#ffffff",
            fg="#36544b",
            wraplength=250,
            justify="left",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(10, 0))

        footer = tk.Label(
            shell,
            textvariable=self.message_var,
            bg="#eef6f2",
            fg="#36544b",
            font=("Segoe UI", 10),
            anchor="w",
        )
        footer.pack(fill="x", pady=(12, 0))

    def schedule_refresh(self) -> None:
        self.root.after(self.poll_interval_ms, self.poll)

    def poll(self) -> None:
        self.refresh_async()
        self.schedule_refresh()

    def refresh_async(self) -> None:
        if self.loading:
            return
        self.loading = True
        threading.Thread(target=self.refresh_worker, daemon=True).start()

    def refresh_worker(self) -> None:
        basket_code = self.basket_code_var.get().strip()
        basket = get_basket(basket_code, api_base_url=self.api_base_url)
        self.root.after(0, lambda: self.apply_basket_response(basket))

    def start_session_async(self) -> None:
        threading.Thread(target=self.start_session_worker, daemon=True).start()

    def start_session_worker(self) -> None:
        basket = start_basket(api_base_url=self.api_base_url, device_id=self.args.device_id)
        self.root.after(0, lambda: self.apply_started_basket(basket))

    def read_shared_basket_code(self, default_code: str) -> str:
        if not self.basket_code_file:
            return default_code
        try:
            value = self.basket_code_file.read_text(encoding="utf-8").strip()
        except OSError:
            return default_code
        return value or default_code

    def write_shared_basket_code(self, basket_code: str) -> None:
        if not self.basket_code_file:
            return
        self.basket_code_file.parent.mkdir(parents=True, exist_ok=True)
        self.basket_code_file.write_text(f"{basket_code}\n", encoding="utf-8")

    def finish_session_async(self) -> None:
        threading.Thread(target=self.finish_session_worker, daemon=True).start()

    def finish_session_worker(self) -> None:
        basket_code = self.basket_code_var.get().strip()
        payload = finish_basket(basket_code, api_base_url=self.api_base_url)
        basket = payload.get("basket") if payload else None
        self.root.after(0, lambda: self.apply_basket_response(basket, action="finish"))

    def apply_started_basket(self, basket: dict | None) -> None:
        if basket is None:
            self.message_var.set("Impossible de creer une session panier.")
            return
        self.basket_code_var.set(basket["code"])
        self.write_shared_basket_code(basket["code"])
        self.apply_basket_response(basket, action="start")

    def apply_basket_response(self, basket: dict | None, action: str = "refresh") -> None:
        self.loading = False
        if basket is None:
            self.status_var.set("offline")
            self.message_var.set("Backend indisponible ou panier introuvable.")
            return

        self.current_basket = basket
        self.status_var.set(basket.get("status", "unknown"))
        self.total_var.set(f"{basket.get('total_amount', '0.00')} USD")
        self.checkout_var.set(basket.get("checkout_url") or "")
        self.render_items(basket.get("items", []))
        self.render_qr(basket)

        if action == "start":
            self.message_var.set(f"Nouvelle session creee: {basket['code']}")
        elif action == "finish":
            self.message_var.set("Panier finalise. Le QR code de caisse est pret.")
        else:
            self.message_var.set(f"Derniere mise a jour du panier {basket.get('code')}")

    def render_items(self, items: list[dict]) -> None:
        for item_id in self.items_tree.get_children():
            self.items_tree.delete(item_id)

        for item in items:
            self.items_tree.insert(
                "",
                "end",
                values=(
                    item.get("product_name"),
                    item.get("quantity"),
                    f"{item.get('unit_price')} {item.get('currency', 'USD')}",
                    f"{item.get('subtotal')} {item.get('currency', 'USD')}",
                ),
            )

    def render_qr(self, basket: dict) -> None:
        qr_url = basket.get("qr_code_url")
        if not qr_url:
            self.qr_image = None
            self.qr_label.configure(image="", text="QR code apres finalisation", bg="#f3faf7")
            return

        if Image is None or ImageTk is None:
            self.qr_label.configure(image="", text="QR: voir URL caisse", bg="#f3faf7")
            return

        try:
            response = requests.get(api_url(self.api_base_url, qr_url), timeout=API_TIMEOUT_SECONDS)
            response.raise_for_status()
            resampling = getattr(getattr(Image, "Resampling", Image), "NEAREST")
            image = (
                Image.open(io.BytesIO(response.content))
                .convert("RGB")
                .resize((QR_DISPLAY_SIZE, QR_DISPLAY_SIZE), resampling)
            )
            self.qr_image = ImageTk.PhotoImage(image)
            self.qr_label.configure(image=self.qr_image, text="", bg="#ffffff")
        except requests.RequestException:
            self.qr_label.configure(image="", text="QR indisponible", bg="#f3faf7")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Kitunga AI Tkinter basket screen")
    parser.add_argument("--api-base-url", default=API_BASE_URL)
    parser.add_argument("--basket-code", default=BASKET_CODE)
    parser.add_argument("--basket-code-file", default=str(BASKET_CODE_FILE))
    parser.add_argument("--device-id", default=DEVICE_ID)
    parser.add_argument("--poll-interval", type=float, default=1.0)
    parser.add_argument("--geometry", default="900x520")
    parser.add_argument("--fullscreen", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = tk.Tk()
    BasketScreenApp(root, args)
    root.mainloop()


if __name__ == "__main__":
    main()
