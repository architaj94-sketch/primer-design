import streamlit as st
import primer3

st.set_page_config(
    page_title="Primer Designer",
    page_icon="🧬",
    layout="centered"
)

st.title("🧬 Primer Designer")
st.write("Design PCR primers from a DNA sequence using Primer3.")

st.subheader("1. Enter DNA sequence")

sequence = st.text_area(
    "DNA sequence",
    placeholder="Example: ATGCGTACGATCGATCGATCG...",
    height=180
)

st.subheader("2. Primer parameters")

col1, col2 = st.columns(2)

with col1:
    min_size = st.number_input(
        "Minimum primer length",
        min_value=15,
        max_value=30,
        value=18
    )

    optimal_size = st.number_input(
        "Optimal primer length",
        min_value=15,
        max_value=30,
        value=20
    )

    max_size = st.number_input(
        "Maximum primer length",
        min_value=15,
        max_value=35,
        value=25
    )

with col2:
    min_tm = st.number_input(
        "Minimum Tm (°C)",
        min_value=40.0,
        max_value=70.0,
        value=57.0
    )

    optimal_tm = st.number_input(
        "Optimal Tm (°C)",
        min_value=40.0,
        max_value=70.0,
        value=60.0
    )

    max_tm = st.number_input(
        "Maximum Tm (°C)",
        min_value=40.0,
        max_value=75.0,
        value=63.0
    )

min_gc = st.number_input(
    "Minimum GC (%)",
    min_value=0.0,
    max_value=100.0,
    value=40.0
)

max_gc = st.number_input(
    "Maximum GC (%)",
    min_value=0.0,
    max_value=100.0,
    value=60.0
)

product_min = st.number_input(
    "Minimum product size (bp)",
    min_value=50,
    max_value=5000,
    value=100
)

product_max = st.number_input(
    "Maximum product size (bp)",
    min_value=100,
    max_value=10000,
    value=300
)

st.divider()

if st.button("🔬 Design Primers", type="primary"):

    clean_sequence = (
        sequence.upper()
        .replace(" ", "")
        .replace("\n", "")
        .replace("\r", "")
    )

    if not clean_sequence:
        st.error("Please enter a DNA sequence.")

    elif any(base not in "ATGC" for base in clean_sequence):
        st.error(
            "Invalid DNA sequence. Please use only A, T, G and C."
        )

    elif len(clean_sequence) < 50:
        st.error(
            "The DNA sequence is too short for reliable primer design."
        )

    elif min_size > optimal_size or optimal_size > max_size:
        st.error(
            "Primer length settings are invalid. "
            "Use Minimum ≤ Optimal ≤ Maximum."
        )

    elif min_tm > optimal_tm or optimal_tm > max_tm:
        st.error(
            "Tm settings are invalid. "
            "Use Minimum ≤ Optimal ≤ Maximum."
        )

    elif min_gc > max_gc:
        st.error(
            "GC settings are invalid. "
            "Minimum GC must be lower than Maximum GC."
        )

    elif product_min >= product_max:
        st.error(
            "Product size settings are invalid."
        )

    else:

        sequence_args = {
            "SEQUENCE_ID": "target_sequence",
            "SEQUENCE_TEMPLATE": clean_sequence
        }

        primer_args = {
            "PRIMER_TASK": "generic",
            "PRIMER_PICK_LEFT_PRIMER": 1,
            "PRIMER_PICK_INTERNAL_OLIGO": 0,
            "PRIMER_PICK_RIGHT_PRIMER": 1,

            "PRIMER_OPT_SIZE": optimal_size,
            "PRIMER_MIN_SIZE": min_size,
            "PRIMER_MAX_SIZE": max_size,

            "PRIMER_OPT_TM": optimal_tm,
            "PRIMER_MIN_TM": min_tm,
            "PRIMER_MAX_TM": max_tm,

            "PRIMER_MIN_GC": min_gc,
            "PRIMER_MAX_GC": max_gc,

            "PRIMER_PRODUCT_SIZE_RANGE": [
                [product_min, product_max]
            ],

            "PRIMER_NUM_RETURN": 5
        }

        try:
            results = primer3.bindings.design_primers(
                sequence_args,
                primer_args
            )

            if results.get("PRIMER_PAIR_NUM_RETURNED", 0) == 0:
                st.warning(
                    "No suitable primer pair was found. "
                    "Try relaxing the Tm, GC%, or product-size settings."
                )

            else:
                st.success(
                    f"Found {results['PRIMER_PAIR_NUM_RETURNED']} "
                    "primer pair(s)."
                )

                for i in range(
                    results["PRIMER_PAIR_NUM_RETURNED"]
                ):
                    st.markdown(
                        f"### Primer Pair {i + 1}"
                    )

                    forward = results.get(
                        f"PRIMER_LEFT_{i}_SEQUENCE",
                        "Not available"
                    )

                    reverse = results.get(
                        f"PRIMER_RIGHT_{i}_SEQUENCE",
                        "Not available"
                    )

                    forward_tm = results.get(
                        f"PRIMER_LEFT_{i}_TM",
                        "Not available"
                    )

                    reverse_tm = results.get(
                        f"PRIMER_RIGHT_{i}_TM",
                        "Not available"
                    )

                    forward_gc = results.get(
                        f"PRIMER_LEFT_{i}_GC_PERCENT",
                        "Not available"
                    )

                    reverse_gc = results.get(
                        f"PRIMER_RIGHT_{i}_GC_PERCENT",
                        "Not available"
                    )

                    product_size = results.get(
                        f"PRIMER_PAIR_{i}_PRODUCT_SIZE",
                        "Not available"
                    )

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**Forward Primer**")
                        st.code(forward)

                        st.write(
                            f"Tm: {forward_tm:.2f} °C"
                            if isinstance(forward_tm, float)
                            else f"Tm: {forward_tm}"
                        )

                        st.write(
                            f"GC: {forward_gc:.2f}%"
                            if isinstance(forward_gc, float)
                            else f"GC: {forward_gc}"
                        )

                    with col2:
                        st.markdown("**Reverse Primer**")
                        st.code(reverse)

                        st.write(
                            f"Tm: {reverse_tm:.2f} °C"
                            if isinstance(reverse_tm, float)
                            else f"Tm: {reverse_tm}"
                        )

                        st.write(
                            f"GC: {reverse_gc:.2f}%"
                            if isinstance(reverse_gc, float)
                            else f"GC: {reverse_gc}"
                        )

                    st.write(
                        f"**Expected product size:** "
                        f"{product_size} bp"
                    )

                    st.divider()

        except Exception as error:
            st.error(
                f"Primer design error: {error}"
            )

st.caption(
    "Primer design powered by Primer3."
)
