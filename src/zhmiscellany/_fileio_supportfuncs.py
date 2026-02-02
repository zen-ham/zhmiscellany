def is_junction(entry):
    import sys
    if sys.platform != "win32":
        return False
    try:
        st = entry.stat(follow_symlinks=False)
        # On Windows, st_file_attributes is available.
        # FILE_ATTRIBUTE_REPARSE_POINT (0x400) indicates a reparse point (e.g. junction).
        return hasattr(st, "st_file_attributes") and bool(st.st_file_attributes & 0x400)
    except Exception:
        return False
