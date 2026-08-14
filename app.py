import streamlit as st
import primer3
import requests
import urllib.parse
import re
import time


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Primer Designer",
    page_icon="🧬",
    layout="centered"
)


# ============================================================
# NCBI BLAST SETTINGS
# ============================================================

NCBI_EMAIL = "architaj94@gmail.com"
NCBI_TOOL = "primer-design-app"


# ============================================================
# NCBI BLAST FUNCTION
# ============================================================

def submit_blast(primer_sequence):
    """
    Submit a primer sequence to NCBI nucleotide BLAST.
    Returns the BLAST Request ID (RID).
    """

    url = "https://blast.ncbi.nlm.nih.gov/Blast.cgi"

    params = {
        "CMD": "Put",
        "PROGRAM": "blastn",
        "DATABASE": "nt",
        "QUERY": primer_sequence,
        "SHORT_QUERY_ADJUST": "true",
        "HITLIST_SIZE": "10",
        "FORMAT_TYPE": "HTML",
        "TOOL": NCBI_TOOL,
        "EMAIL": NCBI_EMAIL
    }

    response = requests.post(
        url,
        data=params,
        timeout=30
    )

    response.raise_for_status()

    rid = None

    for line in response.text.splitlines():
        if "RID =" in line:
            rid = line.split("=", 1)[1].strip()
            break

    return rid


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_sequence(sequence):
    """
    Remove spaces, numbers and FASTA header lines.
    """

    lines = sequence.strip().splitlines()

    cleaned_lines = []

    for line in lines:
        line = line.strip()

        if not line.startswith(">"):
            cleaned_lines.append(line)

    sequence = "".join(cleaned_lines)

    sequence = re.sub(
        r"[^A-Za-z]",
        "",
        sequence
    )

    return sequence.upper()


def valid_dna(sequence):
    """
    Check whether sequence contains only A, T, G and C.
    """

    if not sequence:
        return False

    return all(
        base in "ATGC"
        for base in sequence
    )


# ============================================================
# TITLE
# ============================================================

st.title("🧬 Primer Designer")

st.write(
    "Design PCR primers from a DNA sequence using Primer3 "
    "and check primer specificity using NCBI BLAST."
)

st.divider()


# ============================================================
# DNA SEQUENCE INPUT
# ============================================================

st.subheader("1. Enter DNA Sequence")

sequence_input = st.text_area(
    "DNA sequence",
    placeholder=(
        "Paste your DNA sequence here.\n\n"
        "Example:\n"
        "ATGCGTACGATCGATCGATCGATCG..."
    ),
    height=180
)

sequence = clean_sequence(sequence_input)

if sequence:

    st.write(
        f"**Sequence length:** {len(sequence)} bp"
    )

    if valid_dna(sequence):

        st.success(
            "Valid DNA sequence detected."
        )

    else:

        st.error(
            "Invalid DNA sequence. Please use only A, T, G and C."
        )


# ============================================================
# PRIMER PARAMETERS
# ============================================================

st.divider()

st.subheader("2. Primer Parameters")

col1, col2 = st.columns(2)


with col1:

    min_length = st.number_input(
        "Minimum primer length",
        min_value=15,
        max_value=30,
        value=18,
        step=1
    )

    opt_length = st.number_input(
        "Optimal primer length",
        min_value=15,
        max_value=30,
        value=20,
        step=1
    )

    max_length = st.number_input(
        "Maximum primer length",
        min_value=15,
        max_value=35,
        value=25,
        step=1
    )


with col2:

    min_tm = st.number_input(
        "Minimum Tm (°C)",
        min_value=40.0,
        max_value=80.0,
        value=57.0,
        step=0.5
    )

    opt_tm = st.number_input(
        "Optimal Tm (°C)",
        min_value=40.0,
        max_value=80.0,
        value=60.0,
        step=0.5
    )

    max_tm = st.number_input(
        "Maximum Tm (°C)",
        min_value=40.0,
        max_value=80.0,
        value=63.0,
        step=0.5
    )


st.markdown("### GC Content")

gc_col1, gc_col2 = st.columns(2)


with gc_col1:

    min_gc = st.number_input(
        "Minimum GC %",
        min_value=20.0,
        max_value=80.0,
        value=40.0,
        step=1.0
    )


with gc_col2:

    max_gc = st.number_input(
        "Maximum GC %",
        min_value=20.0,
        max_value=80.0,
        value=60.0,
        step=1.0
    )


st.markdown("### PCR Product Size")

product_col1, product_col2 = st.columns(2)


with product_col1:

    product_min = st.number_input(
        "Minimum product size (bp)",
        min_value=50,
        max_value=2000,
        value=100,
        step=10
    )


with product_col2:

    product_max = st.number_input(
        "Maximum product size (bp)",
        min_value=50,
        max_value=5000,
        value=500,
        step=10
    )


# ============================================================
# DESIGN PRIMERS
# ============================================================

st.divider()

design_button = st.button(
    "🧬 Design Primers",
    type="primary",
    use_container_width=True
)


if design_button:

    if not sequence:

        st.error(
            "Please enter a DNA sequence first."
        )

    elif not valid_dna(sequence):

        st.error(
            "The sequence contains invalid characters. "
            "Please use only A, T, G and C."
        )

    elif len(sequence) < product_min:

        st.error(
            "The DNA sequence is shorter than the minimum "
            "PCR product size."
        )

    elif min_length > opt_length or opt_length > max_length:

        st.error(
            "Primer length settings must follow: "
            "minimum ≤ optimal ≤ maximum."
        )

    elif min_tm > opt_tm or opt_tm > max_tm:

        st.error(
            "Tm settings must follow: "
            "minimum ≤ optimal ≤ maximum."
        )

    elif min_gc > max_gc:

        st.error(
            "Minimum GC% cannot be greater than maximum GC%."
        )

    elif product_min > product_max:

        st.error(
            "Minimum product size cannot be greater than "
            "maximum product size."
        )

    else:

        try:

            with st.spinner(
                "Designing primers using Primer3..."
            ):

                results = primer3.bindings.design_primers(
                    {
                        "SEQUENCE_ID": "user_sequence",
                        "SEQUENCE_TEMPLATE": sequence
                    },
                    {
                        "PRIMER_TASK": "generic",
                        "PRIMER_PICK_LEFT_PRIMER": 1,
                        "PRIMER_PICK_INTERNAL_OLIGO": 0,
                        "PRIMER_PICK_RIGHT_PRIMER": 1,

                        "PRIMER_OPT_SIZE": int(opt_length),
                        "PRIMER_MIN_SIZE": int(min_length),
                        "PRIMER_MAX_SIZE": int(max_length),

                        "PRIMER_OPT_TM": float(opt_tm),
                        "PRIMER_MIN_TM": float(min_tm),
                        "PRIMER_MAX_TM": float(max_tm),

                        "PRIMER_MIN_GC": float(min_gc),
                        "PRIMER_MAX_GC": float(max_gc),

                        "PRIMER_PRODUCT_SIZE_RANGE": [
                            [
                                int(product_min),
                                int(product_max)
                            ]
                        ],

                        "PRIMER_NUM_RETURN": 5
                    }
                )


            pair_count = results.get(
                "PRIMER_PAIR_NUM_RETURNED",
                0
            )


            if pair_count == 0:

                st.warning(
                    "Primer3 could not find a suitable primer pair "
                    "with the selected parameters."
                )

                st.info(
                    "Try increasing the product-size range or "
                    "slightly relaxing the Tm, GC%, or primer-length "
                    "settings."
                )

            else:

                st.success(
                    f"Primer design successful! "
                    f"{pair_count} primer pair(s) found."
                )

                st.divider()

                st.subheader(
                    "3. Primer Results"
                )


                for i in range(pair_count):

                    forward = results.get(
                        f"PRIMER_LEFT_{i}_SEQUENCE",
                        ""
                    )

                    reverse = results.get(
                        f"PRIMER_RIGHT_{i}_SEQUENCE",
                        ""
                    )

                    forward_tm = results.get(
                        f"PRIMER_LEFT_{i}_TM",
                        "N/A"
                    )

                    reverse_tm = results.get(
                        f"PRIMER_RIGHT_{i}_TM",
                        "N/A"
                    )

                    forward_gc = results.get(
                        f"PRIMER_LEFT_{i}_GC_PERCENT",
                        "N/A"
                    )

                    reverse_gc = results.get(
                        f"PRIMER_RIGHT_{i}_GC_PERCENT",
                        "N/A"
                    )

                    product_size = results.get(
                        f"PRIMER_PAIR_{i}_PRODUCT_SIZE",
                        "N/A"
                    )


                    st.markdown(
                        f"## Primer Pair {i + 1}"
                    )


                    result_col1, result_col2 = st.columns(2)


                    # ====================================================
                    # FORWARD PRIMER RESULT
                    # ====================================================

                    with result_col1:

                        st.markdown(
                            "**Forward Primer**"
                        )

                        st.code(
                            forward
                        )

                        st.write(
                            f"**Length:** {len(forward)} bp"
                        )

                        if isinstance(
                            forward_tm,
                            (float, int)
                        ):

                            st.write(
                                f"**Tm:** {forward_tm:.2f} °C"
                            )

                        else:

                            st.write(
                                f"**Tm:** {forward_tm}"
                            )


                        if isinstance(
                            forward_gc,
                            (float, int)
                        ):

                            st.write(
                                f"**GC:** {forward_gc:.2f}%"
                            )

                        else:

                            st.write(
                                f"**GC:** {forward_gc}"
                            )


                    # ====================================================
                    # REVERSE PRIMER RESULT
                    # ====================================================

                    with result_col2:

                        st.markdown(
                            "**Reverse Primer**"
                        )

                        st.code(
                            reverse
                        )

                        st.write(
                            f"**Length:** {len(reverse)} bp"
                        )

                        if isinstance(
                            reverse_tm,
                            (float, int)
                        ):

                            st.write(
                                f"**Tm:** {reverse_tm:.2f} °C"
                            )

                        else:

                            st.write(
                                f"**Tm:** {reverse_tm}"
                            )


                        if isinstance(
                            reverse_gc,
                            (float, int)
                        ):

                            st.write(
                                f"**GC:** {reverse_gc:.2f}%"
                            )

                        else:

                            st.write(
                                f"**GC:** {reverse_gc}"
                            )


                    st.info(
                        f"Expected amplicon size: "
                        f"{product_size} bp"
                    )


                    # ====================================================
                    # BLAST SECTION
                    # ====================================================

                    st.markdown(
                        "### 🌐 Primer Specificity Analysis"
                    )

                    st.write(
                        "Check each primer against the NCBI "
                        "nucleotide database using BLAST."
                    )


                    blast_col1, blast_col2 = st.columns(2)


                    # ====================================================
                    # FORWARD BLAST
                    # ====================================================

                    with blast_col1:

                        if st.button(
                            "🔬 BLAST Forward Primer",
                            key=f"blast_forward_{i}"
                        ):

                            with st.spinner(
                                "Submitting forward primer "
                                "to NCBI BLAST..."
                            ):

                                try:

                                    rid = submit_blast(
                                        forward
                                    )

                                    if rid:

                                        blast_url = (
                                            "https://blast.ncbi.nlm.nih.gov/"
                                            "Blast.cgi?CMD=Get&RID="
                                            + urllib.parse.quote(
                                                rid
                                            )
                                        )

                                        st.success(
                                            "Forward primer submitted "
                                            "successfully!"
                                        )

                                        st.write(
                                            f"**BLAST Request ID:** {rid}"
                                        )

                                        st.link_button(
                                            "🌐 Open Forward BLAST Results",
                                            blast_url
                                        )

                                    else:

                                        st.error(
                                            "NCBI did not return a "
                                            "BLAST Request ID."
                                        )

                                except Exception as error:

                                    st.error(
                                        f"BLAST submission failed: "
                                        f"{error}"
                                    )


                    # ====================================================
                    # REVERSE BLAST
                    # ====================================================

                    with blast_col2:

                        if st.button(
                            "🔬 BLAST Reverse Primer",
                            key=f"blast_reverse_{i}"
                        ):

                            with st.spinner(
                                "Submitting reverse primer "
                                "to NCBI BLAST..."
                            ):

                                try:

                                    rid = submit_blast(
                                        reverse
                                    )

                                    if rid:

                                        blast_url = (
                                            "https://blast.ncbi.nlm.nih.gov/"
                                            "Blast.cgi?CMD=Get&RID="
                                            + urllib.parse.quote(
                                                rid
                                            )
                                        )

                                        st.success(
                                            "Reverse primer submitted "
                                            "successfully!"
                                        )

                                        st.write(
                                            f"**BLAST Request ID:** {rid}"
                                        )

                                        st.link_button(
                                            "🌐 Open Reverse BLAST Results",
                                            blast_url
                                        )

                                    else:

                                        st.error(
                                            "NCBI did not return a "
                                            "BLAST Request ID."
                                        )

                                except Exception as error:

                                    st.error(
                                        f"BLAST submission failed: "
                                        f"{error}"
                                    )


                    st.divider()


        except Exception as error:

            st.error(
                f"Primer design error: {error}"
            )


# ============================================================
# ABOUT APPLICATION
# ============================================================

st.subheader("ℹ️ About this Application")

st.write(
    "This application uses Primer3 for PCR primer design."
)

st.markdown(
    """
**Main features:**

- DNA sequence validation
- Primer length optimization
- Melting temperature (Tm) control
- GC content control
- PCR product-size selection
- Forward and reverse primer generation
- Primer3-based primer design
- NCBI BLAST specificity checking
"""
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Primer design powered by Primer3 | "
    "Specificity checking powered by NCBI BLAST"
)
