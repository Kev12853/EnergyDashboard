import subprocess
import sys

import streamlit as st


def start_services():
    print("START_SERVICES CALLED")

    services = [
        (
            "Solax Logger",
            "app.backend.services.solax_service",
        ),
        (
            "Octopus Logger",
            "app.backend.services.octopus_service",
        ),
        (
            "Account Sync",
            "app.octopus.account_logger",
        ),
        (
            "Agreement Sync",
            "app.octopus.agreement_logger",
        ),
    ]

    print("\n=== STARTING SERVICES ===")

    for (
        service_name,
        module,
    ) in services:
        try:
            subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    module,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            print(f"✓ {service_name}")

        except Exception as e:
            print(f"✗ {service_name} : {e}")

    print("=========================\n")

    # st.session_state[
    #     "services_started"
    # ] = True
