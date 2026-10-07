"""Render direction-aware shading columns without assuming TEASER group order."""
def modelica_column_matrix(zone, kind):
    model = zone.model_attr
    size = max(1, int(getattr(model, "n_outer" if kind == "wall" else "n_rt", 0)))
    rows = getattr(zone, f"geometric_shading_{kind}_columns", None)
    if rows is None:
        rows = [[2, 3, 4]] * size
    if len(rows) != size or any(len(row) != 3 or any(int(v) < 2 for v in row) for row in rows):
        raise ValueError(f"Invalid directional geometric shading columns for {zone.name}/{kind}")
    return "[" + "; ".join(", ".join(str(int(v)) for v in row) for row in rows) + "]"
