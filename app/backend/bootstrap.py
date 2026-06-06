import subprocess
import sys

import streamlit as st


def start_services():
    print("START_SERVICES CALLED")
    # if (
    #     "services_started"
    #     in st.session_state
    # ):
    #     return

    services = [

        (
            "Solax Logger",
            "poller.solax.logger",
        ),

        (
            "Octopus Logger",
            "poller.octopus.logger",
        ),

        (
            "Account Sync",
            "poller.octopus.account_logger",
        ),

        (
            "Agreement Sync",
            "poller.octopus.agreement_logger",
        ),

    ]

    print(
        "\n=== STARTING SERVICES ==="
    )

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

            print(
                f"✓ {service_name}"
            )

        except Exception as e:

            print(
                f"✗ {service_name}"
                f" : {e}"
            )

    print(
        "=========================\n"
    )

    # st.session_state[
    #     "services_started"
    # ] = True