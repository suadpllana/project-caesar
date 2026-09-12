def run(st):
    out = {}
    for nm, row in st.names.spare.items():
        if nm in st.names.firm or nm in st.names.soft:
            continue
        out[nm] = (row[1], row[0])
    return out
