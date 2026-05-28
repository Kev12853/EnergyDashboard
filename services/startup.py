import subprocess
import sys

import streamlit as st


def start_services():

    if (
        "services_started"
        in st.session_state
    ):
        return

    services = [

        (
            "Solax Logger",
            "services.solax.logger",
        ),

        (
            "Octopus Logger",
            "services.octopus.logger",
        ),

        (
            "Account Sync",
            "services.octopus.account_logger",
        ),

        (
            "Agreement Sync",
            "services.octopus.agreement_logger",
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

    st.session_state[
        "services_started"
    ] = True