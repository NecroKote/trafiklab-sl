
def global_id_to_site_id(global_id: str) -> int:
    """
    Convert a global ID to a transport site ID.

    Function assumes the global ID is in the format "909100100xxxxxxx",
    """

    if len(global_id) != 16:
        raise ValueError(f"Invalid global ID length: {len(global_id)}. Expected 16 characters.")

    prefix = "909100100"
    if not global_id.startswith(prefix):
        raise ValueError(f"Invalid global ID prefix: {global_id[:9]}. Expected '{prefix}'.")

    return int(global_id.removeprefix(prefix))
