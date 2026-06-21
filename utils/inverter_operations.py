def determine_required_actions(
    desired_work_mode,
    desired_manual_mode,
    actual_work_mode,
    actual_manual_mode,
):
    """
    Return a list of actions required to move the inverter
    from its current state to the desired state.
    """

    actions = []

    MANUAL_MODE = 3

    #
    # Work mode first
    #

    if desired_work_mode != actual_work_mode:
        actions.append(
            ("work_mode", desired_work_mode)
        )

    #
    # Manual mode only relevant if Manual mode desired
    #

    if desired_work_mode == MANUAL_MODE:

        if desired_manual_mode != actual_manual_mode:
            actions.append(
                ("manual_mode", desired_manual_mode)
            )

    return actions