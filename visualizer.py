"""
Matplotlib charts built from an Analytics snapshot and the live edge
servers. Kept separate from analytics.py so plotting concerns never
leak into data collection.
"""

import os

import matplotlib
matplotlib.use("Agg")  # headless: write PNGs directly, no display needed
import matplotlib.pyplot as plt

import config


def _ensure_chart_dir():
    os.makedirs(config.CHART_DIR, exist_ok=True)


def plot_cache_hit_vs_miss(analytics):
    _ensure_chart_dir()
    fig, ax = plt.subplots()
    ax.bar(["Hits", "Misses"], [analytics.cache_hits, analytics.cache_misses],
           color=["#2e7d32", "#c62828"])
    ax.set_ylabel("Requests")
    ax.set_title("Cache Hits vs Misses")
    fig.tight_layout()
    fig.savefig(os.path.join(config.CHART_DIR, "cache_hit_vs_miss.png"))
    plt.close(fig)


def plot_requests_per_server(analytics):
    _ensure_chart_dir()
    data = analytics.requests_per_server()
    fig, ax = plt.subplots()
    ax.bar(list(data.keys()), list(data.values()), color="#1565c0")
    ax.set_ylabel("Requests")
    ax.set_title("Requests Per Edge Server")
    fig.tight_layout()
    fig.savefig(os.path.join(config.CHART_DIR, "requests_per_server.png"))
    plt.close(fig)


def plot_latency_distribution(analytics):
    _ensure_chart_dir()
    fig, ax = plt.subplots()
    ax.hist(analytics.latencies, bins=20, color="#6a1b9a")
    ax.set_xlabel("Latency (ms)")
    ax.set_ylabel("Requests")
    ax.set_title("Latency Distribution")
    fig.tight_layout()
    fig.savefig(os.path.join(config.CHART_DIR, "latency_distribution.png"))
    plt.close(fig)


def plot_server_load(edge_servers):
    _ensure_chart_dir()
    names = list(edge_servers.keys())
    utilization_pct = [edge_servers[name].cache.utilization * 100 for name in names]

    fig, ax = plt.subplots()
    ax.bar(names, utilization_pct, color="#ef6c00")
    ax.set_ylabel("Cache utilization (%)")
    ax.set_ylim(0, 100)
    ax.set_title("Edge Server Cache Load")
    fig.tight_layout()
    fig.savefig(os.path.join(config.CHART_DIR, "server_load.png"))
    plt.close(fig)


def generate_all_charts(analytics, edge_servers):
    plot_cache_hit_vs_miss(analytics)
    plot_requests_per_server(analytics)
    plot_latency_distribution(analytics)
    plot_server_load(edge_servers)
