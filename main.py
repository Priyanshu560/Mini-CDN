"""
Command-line entry point for MiniCDN. Wires the origin server, edge
servers, and router together, then offers a menu for interactive
requests, batch simulation, analytics, and charts.

Usage:
    python main.py            interactive menu
    python main.py 500        run 500 simulated requests and exit
"""

import sys

import config
from analytics import Analytics
from edge_server import EdgeServer
from logger import RequestLogger
from models import Client
from origin_server import OriginServer
from router import Router
from simulator import Simulator


def build_system():
    origin = OriginServer(config.DATA_DIR)

    edge_servers = {}
    for name, settings in config.EDGE_SERVERS.items():
        edge_servers[name] = EdgeServer(
            name=name,
            coordinates=settings["coordinates"],
            base_latency_ms=settings["base_latency_ms"],
            bandwidth_mbps=settings["bandwidth_mbps"],
            cache_capacity_bytes=settings["cache_capacity_bytes"],
            origin=origin,
        )

    router = Router(edge_servers)
    logger = RequestLogger(config.LOG_FILE)
    analytics = Analytics()
    simulator = Simulator(origin, router, logger=logger, analytics=analytics)
    return origin, simulator


def prompt_single_request(simulator):
    location = input(f"Client location {list(config.CLIENT_CITIES.keys())}: ").strip()
    file_name = input("Requested file: ").strip()

    client = Client(location=location)
    record = simulator.process_request(client, file_name)

    print(f"\nServer selected : {record.server_name}")
    print(f"Cache status    : {record.cache_status}")
    print(f"Latency         : {record.latency_ms:.2f} ms")
    print(f"Status          : {record.status}\n")


def prompt_batch_simulation(simulator):
    raw_count = input("Number of requests to simulate: ").strip()
    try:
        num_requests = int(raw_count)
    except ValueError:
        print("Please enter a whole number.\n")
        return

    _, elapsed_seconds = simulator.run_batch(num_requests)
    print(f"\nProcessed {num_requests} requests in {elapsed_seconds:.3f}s of real time.\n")
    print(simulator.analytics.report())
    print()


def generate_charts(simulator):
    from visualizer import generate_all_charts  # imported lazily: matplotlib only needed here
    generate_all_charts(simulator.analytics, simulator.router.edge_servers)
    print(f"\nCharts written to {config.CHART_DIR}\n")


def run_non_interactive(simulator, requested_count):
    try:
        num_requests = int(requested_count)
    except ValueError:
        print(f"Invalid request count: '{requested_count}'")
        return

    _, elapsed_seconds = simulator.run_batch(num_requests)
    print(f"Processed {num_requests} requests in {elapsed_seconds:.3f}s of real time.\n")
    print(simulator.analytics.report())
    generate_charts(simulator)


def main():
    _, simulator = build_system()

    if len(sys.argv) > 1:
        run_non_interactive(simulator, sys.argv[1])
        return

    menu = """
MiniCDN - Content Delivery Network Simulator
1. Send a single client request
2. Run a batch simulation
3. Show analytics report
4. Generate charts
5. Exit
"""
    while True:
        print(menu)
        choice = input("Choose an option: ").strip()

        if choice == "1":
            prompt_single_request(simulator)
        elif choice == "2":
            prompt_batch_simulation(simulator)
        elif choice == "3":
            print(simulator.analytics.report())
        elif choice == "4":
            generate_charts(simulator)
        elif choice == "5":
            print("Goodbye.")
            break
        else:
            print("Invalid option, try again.")


if __name__ == "__main__":
    main()
