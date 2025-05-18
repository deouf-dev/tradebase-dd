import tkinter as tk
import requests
import matplotlib.pyplot as plt # type: ignore
from io import BytesIO
from PIL import Image, ImageTk
from datetime import datetime

def showgraph(interface, crypto):
    root = interface.root

    periods = {
        "1y": ("1d", 365), "6m": ("1d", 180), "3m": ("1d", 90),
        "1m": ("4h", 30), "1w": ("1h", 7*24), "1d": ("5m", 24*12)
    }

    window = tk.Toplevel(root)
    window.title(f"Graphique {crypto}")
    window.geometry("550x500")
    window.config(bg="#222222")

    frame = tk.Frame(window, bg="#222222")
    frame.pack(pady=10)

    graph_label = tk.Label(window, bg="#222222")
    graph_label.pack(pady=10)

    buttons = {}

    def update_graph(period):
        for p in buttons:
            buttons[p].config(bg="white", fg="black", state="normal")
        buttons[period].config(bg="gold", fg="black", state="disabled")

        interval, limit = periods[period]
        fetchCryptoAndCreateGraph(graph_label, crypto, interval, limit)

    for p in periods:
        buttons[p] = tk.Button(frame, text=p, width=5,
                               command=lambda p=p: update_graph(p),
                               bg="white", fg="black", state="normal")
        buttons[p].pack(side="left", padx=5)

    update_graph("1m")

def fetchCryptoAndCreateGraph(graph_label, crypto, interval, limit):
    url = f"https://api.binance.com/api/v3/klines?symbol={crypto}&interval={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()

    if not data or "code" in data:
        return

    timestamps = [datetime.fromtimestamp(entry[0] / 1000).strftime('%Y-%m-%d %H:%M') for entry in data]
    prices = [float(entry[4]) for entry in data]

    fig, ax = plt.subplots(figsize=(5, 3))
    ax.plot(timestamps, prices, color="gold", linewidth=2)
    ax.set_facecolor("#222222")
    fig.patch.set_facecolor("#222222")
    ax.tick_params(colors="white")
    ax.set_xticks(timestamps[::len(timestamps)//5])
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")

    buffer = BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight", facecolor="#222222")
    buffer.seek(0)
    img = Image.open(buffer)
    img = ImageTk.PhotoImage(img)

    graph_label.config(image=img)
    graph_label.image = img
