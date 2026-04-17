#!/usr/bin/env python3
"""
Label-Selector-Lab: selector.py
────────────────────────────────
Demonstrates Kubernetes label selectors using the official Python client.

Usage (interactive menu):
    python selector.py

Usage (one-shot via CLI flags):
    python selector.py --selector "env=prod"
    python selector.py --selector "env=prod,tier=frontend"
    python selector.py --selector "team=alpha"
    python selector.py --all

The script connects to whichever cluster your current kubeconfig points to
and filters pods in the `label-selector-lab` namespace.
"""

import argparse
import sys
from typing import Optional

try:
    from kubernetes import client, config
    from kubernetes.client.exceptions import ApiException
except ImportError:
    print("ERROR: 'kubernetes' package not found.")
    print("       Run: pip install kubernetes")
    sys.exit(1)


NAMESPACE = "label-selector-lab"

# ANSI colours for terminal output
RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[32m"
CYAN   = "\033[36m"
YELLOW = "\033[33m"
RED    = "\033[31m"
GREY   = "\033[90m"


# ──────────────────────────────────────────────────────────────────────────────
# Core query function
# ──────────────────────────────────────────────────────────────────────────────

def list_pods(label_selector: Optional[str] = None) -> None:
    """
    Fetch and display pods from the label-selector-lab namespace.

    Args:
        label_selector: A comma-separated label selector string, e.g.
                        "env=prod,tier=frontend"
                        If None, all pods in the namespace are returned.
    """
    v1 = client.CoreV1Api()

    try:
        pods = v1.list_namespaced_pod(
            namespace=NAMESPACE,
            label_selector=label_selector,
        )
    except ApiException as e:
        if e.status == 404:
            print(f"{RED}Namespace '{NAMESPACE}' not found.{RESET}")
            print("  → Have you run: kubectl apply -f k8s/deployments.yaml ?")
        else:
            print(f"{RED}Kubernetes API error: {e}{RESET}")
        return

    selector_display = label_selector if label_selector else "(all pods)"
    print(f"\n{BOLD}{CYAN}Namespace:{RESET} {NAMESPACE}")
    print(f"{BOLD}{CYAN}Selector :{RESET} {selector_display}")
    print(f"{BOLD}{CYAN}Found    :{RESET} {len(pods.items)} pod(s)\n")

    if not pods.items:
        print(f"{YELLOW}  No pods match this selector.{RESET}\n")
        return

    # Table header
    header = f"{'POD NAME':<50} {'STATUS':<12} {'env':<8} {'tier':<12} {'team':<8} {'NODE'}"
    print(BOLD + header + RESET)
    print(GREY + "─" * len(header) + RESET)

    for pod in pods.items:
        labels = pod.metadata.labels or {}
        phase  = pod.status.phase or "Unknown"
        node   = pod.spec.node_name or "Pending"

        # Colour the status
        if phase == "Running":
            status_str = GREEN + phase + RESET
        elif phase in ("Pending", "ContainerCreating"):
            status_str = YELLOW + phase + RESET
        else:
            status_str = RED + phase + RESET

        print(
            f"{pod.metadata.name:<50} "
            f"{status_str:<20} "        # extra width due to ANSI codes
            f"{labels.get('env',  '-'):<8} "
            f"{labels.get('tier', '-'):<12} "
            f"{labels.get('team', '-'):<8} "
            f"{node}"
        )

    print()


# ──────────────────────────────────────────────────────────────────────────────
# Interactive menu
# ──────────────────────────────────────────────────────────────────────────────

MENU_OPTIONS = [
    ("All pods in namespace",                    None),
    ("env=prod  (all production pods)",          "env=prod"),
    ("env=dev   (all development pods)",         "env=dev"),
    ("tier=frontend  (all frontend pods)",       "tier=frontend"),
    ("tier=backend   (all backend pods)",        "tier=backend"),
    ("team=alpha  (Team Alpha pods)",            "team=alpha"),
    ("team=beta   (Team Beta pods)",             "team=beta"),
    ("env=prod,tier=frontend  (prod-frontend)",  "env=prod,tier=frontend"),
    ("env=prod,tier=backend   (prod-backend)",   "env=prod,tier=backend"),
    ("env=dev,tier=frontend   (dev-frontend)",   "env=dev,tier=frontend"),
    ("env=dev,tier=backend    (dev-backend)",    "env=dev,tier=backend"),
    ("Custom selector (type your own)",          "CUSTOM"),
]


def interactive_menu() -> None:
    print(f"\n{BOLD}{'═'*60}")
    print("  ☸️  Label-Selector-Lab  —  Pod Filter Demo")
    print(f"{'═'*60}{RESET}")

    while True:
        print(f"\n{BOLD}Choose a label selector:{RESET}")
        for i, (label, _) in enumerate(MENU_OPTIONS, 1):
            print(f"  {CYAN}{i:>2}{RESET}. {label}")
        print(f"  {CYAN} 0{RESET}. Exit\n")

        choice = input("Enter number: ").strip()

        if choice == "0":
            print("Bye! 👋\n")
            break

        if not choice.isdigit() or not (1 <= int(choice) <= len(MENU_OPTIONS)):
            print(f"{RED}Invalid choice. Please enter a number between 0 and {len(MENU_OPTIONS)}.{RESET}")
            continue

        _, selector = MENU_OPTIONS[int(choice) - 1]

        if selector == "CUSTOM":
            selector = input("  Enter label selector (e.g. env=prod,team=alpha): ").strip() or None

        list_pods(selector)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Query Kubernetes pods by label selector."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--selector", "-s",
        metavar="SELECTOR",
        help='Label selector string, e.g. "env=prod,tier=frontend"',
    )
    group.add_argument(
        "--all", "-a",
        action="store_true",
        help="List all pods in the namespace (no filter)",
    )
    args = parser.parse_args()

    # Load kubeconfig (falls back to in-cluster config if running inside a pod)
    try:
        config.load_kube_config()
    except Exception:
        try:
            config.load_incluster_config()
        except Exception:
            print(f"{RED}Could not load kubeconfig or in-cluster config.{RESET}")
            sys.exit(1)

    if args.selector:
        list_pods(args.selector)
    elif args.all:
        list_pods(None)
    else:
        interactive_menu()


if __name__ == "__main__":
    main()
