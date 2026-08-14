import streamlit as st
import primer3
import requests
import time
import re

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="Primer Designer",
    page_icon="🧬",
    layout="centered"
)

# ---------------------------------------------------------
# TITLE
# ---------------------------------------------------------

st.title("🧬 Primer Designer")

st.write(
    "Design PCR primers from a DNA sequence using Primer3 "
    "and check primer specificity using NCBI BLAST."
)

st.divider()

# ---------------------------------------------------------
# DNA SEQUENCE INPUT
# ---------------------------------------------------------

st.subheader("1. Enter DNA Sequence")

sequence = st.text_area(
    "DNA sequence",
    placeholder="Example: ATGCGTACGATCGATCGATCG...",
    height=180
)

# Clean sequence
clean_sequence = re.sub(r"\s+", "", sequence).upper()

# ---------------------------------------------------------
# VALIDATE DNA
# ---------------------------------------------------------

if clean_sequence:

    invalid_bases = set(clean_sequence) - set("ATGC")

    if invalid_bases:
        st.error(
            "Invalid DNA sequence. Please use only A, T, G and C."
        )

    elif len(clean_sequence) < 50:
        st.warning(
            "The DNA sequence is very short. "
            "For reliable primer design, use a longer sequence."
        )

# ---------------------------------------------------------
# PRIMER PARAMETERS
# ---------------------------------------------------------

st.subheader("2. Primer Parameters")

col1, col2 = st.columns(2)

with col1:

    min_size = st.number_input(
        "Minimum primer length",
        min_value=15,
        max_value=30,
        value=18,
        step=1
    )

    opt_size = st.number_input(
        "Optimal primer length",
        min_value=15,
        max_value=30,
        value=20,
        step=1
    )

    max_size = st.number_input(
        "Maximum primer length",
        min_value=18,
        max_value=35,
        value=25,
        step=1
    )

    min_gc = st.number_input(
        "Minimum GC %",
        min_value=0.0,
        max_value=100.0,
        value=40.0,
        step=1.0
    )

    max_gc = st.number_input(
        "Maximum GC %",
        min_value=0.0,
        max_value=100.0,
        value=60.0,
        step=1.0
    )

with col2:

    min_tm = st.number_input(
        "Minimum Tm (°C)",
        min_value=40.0,
        max_value=70.0,
        value=57.0,
        step=0.5
    )

    opt_tm = st.number_input(
        "Optimal Tm (°C)",
        min_value=40.0,
        max_value=70.0,
        value=60.0,
        step=0.5
    )

    max_tm = st.number_input(
        "Maximum Tm (°C)",
        min_value=40.0,
        max_value=75.0,
        value=63.0,
        step=0.5
    )

    min_product = st.number_input(
        "Minimum product size",
        min_value=50,
        max_value=1000,
        value=100,
        step=10
    )

    max_product = st.number_input(
        "Maximum product size",
        min_value=100,
        max_value=2000,
        value=500,
        step=10
    )

st.divider()

# ---------------------------------------------------------
# PRIMER DESIGN FUNCTION
# ---------------------------------------------------------

def design_primers(dna_sequence):

    seq_args = {
        "SEQUENCE_ID": "Target_DNA",
        "SEQUENCE_TEMPLATE": dna_sequence
    }

    global_args = {
        "PRIMER_TASK": "generic",
        "PRIMER_PICK_LEFT_PRIMER": 1,
        "PRIMER_PICK_INTERNAL_OLIGO": 0,
        "PRIMER_PICK_RIGHT_PRIMER": 1,

        "PRIMER_MIN_SIZE": min_size,
        "PRIMER_OPT_SIZE": opt_size,
        "PRIMER_MAX_SIZE": max_size,

        "PRIMER_MIN_TM": min_tm,
        "PRIMER_OPT_TM": opt_tm,
        "PRIMER_MAX_TM": max_tm,

        "PRIMER_MIN_GC": min_gc,
        "PRIMER_MAX_GC": max_gc,

        "PRIMER_PRODUCT_SIZE_RANGE": [
            [min_product, max_product]
        ],

        "PRIMER_NUM_RETURN": 5
    }

    result = primer3.bindings.design_primers(
        seq_args,
        global_args
    )

    return result


# ---------------------------------------------------------
# NCBI BLAST FUNCTION
# ---------------------------------------------------------

def submit_blast(primer_sequence):

    url = "https://blast.ncbi.nlm.nih.gov/Blast.cgi"

    params = {
        "CMD": "Put",
        "PROGRAM": "blastn",
        "DATABASE": "nt",
        "QUERY": primer_sequence,
        "SHORT_QUERY_ADJUST": "true",
        "HITLIST_SIZE": "10",
        "FORMAT_TYPE": "Text",
        "TOOL": "primer-design-app",
        "EMAIL": "your_email@example.com"
    }

    response = requests.post(
        url,
        data=params,
        timeout=30
    )

    response.raise_for_status()

    # Find BLAST Request ID
    rid_match = re.search(
        r"RID = ([A-Z0-9-]+)",
        response.text
    )

    # Find estimated running time
    rtoe_match = re.search(
        r"RTOE = (\d+)",
        response.text
    )

    if not rid_match:
        return None, None

    rid = rid_match.group(1)

    rtoe = 10

    if rtoe_match:
        rtoe = int(rtoe_match.group(1))

    return rid, rtoe


# ---------------------------------------------------------
# GET BLAST RESULT
# ---------------------------------------------------------

def get_blast_result(rid):

    url = "https://blast.ncbi.nlm.nih.gov/Blast.cgi"

    params = {
        "CMD": "Get",
        "RID": rid,
        "FORMAT_TYPE": "Text"
    }

    for attempt in range(12):

        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        text = response.text

        if "Status=WAITING" in text:
            time.sleep(5)
            continue

        if "Status=READY" in text:
            return text

        if "Status=FAILED" in text:
            return "BLAST search failed."

        # Sometimes the status line is not returned
        if "BLASTN" in text or "Sequences producing significant alignments" in text:
            return text

        time.sleep(5)

    return "BLAST is taking longer than expected. Please open the NCBI BLAST result link."


# ---------------------------------------------------------
# BLAST DISPLAY
# ---------------------------------------------------------

def show_blast(primer_name, primer_sequence):

    st.write(f"**{primer_name}:** `{primer_sequence}`")

    if st.button(
        f"🔎 BLAST {primer_name}",
        key=f"blast_{primer_name}"
    ):

        with st.spinner(
            "Submitting primer sequence to NCBI BLAST..."
        ):

            try:

                rid, rtoe = submit_blast(primer_sequence)

                if not rid:

                    st.error(
                        "Could not obtain a BLAST Request ID."
                    )

                else:

                    st.success(
                        f"BLAST submitted successfully. Request ID: {rid}"
                    )

                    # NCBI BLAST result URL
                    blast_link = (
                        "https://blast.ncbi.nlm.nih.gov/Blast.cgi"
                        f"?CMD=Get&RID={rid}"
                    )

                    st.markdown(
                        f"[🌐 Open BLAST result on NCBI]({blast_link})"
                    )

                    # Wait before checking
                    time.sleep(max(rtoe, 5))

                    with st.spinner(
                        "Waiting for BLAST results..."
                    ):

                        result = get_blast_result(rid)

                    if result:

                        st.subheader(
                            f"BLAST Result — {primer_name}"
                        )

                        st.text_area(
                            "NCBI BLAST output",
                            result,
                            height=400,
                            key=f"result_{primer_name}"
                        )

            except requests.exceptions.RequestException as e:

                st.error(
                    "Unable to connect to NCBI BLAST. "
                    "Please check your internet connection."
                )

                st.caption(str(e))

            except Exception as e:

                st.error(
                    "An error occurred while running BLAST."
                )

                st.caption(str(e))


# ---------------------------------------------------------
# DESIGN BUTTON
# ---------------------------------------------------------

if st.button(
    "🧬 Design Primers",
    type="primary",
    use_container_width=True
):

    if not clean_sequence:

        st.error(
            "Please enter a DNA sequence first."
        )

    elif set(clean_sequence) - set("ATGC"):

        st.error(
            "DNA sequence contains invalid characters."
        )

    elif len(clean_sequence) < 50:

        st.error(
            "Please enter a longer DNA sequence."
        )

    else:

        with st.spinner(
            "Designing primers using Primer3..."
        ):

            try:

                results = design_primers(
                    clean_sequence
                )

                left_primer = results.get(
                    "PRIMER_LEFT_0_SEQUENCE"
                )

                right_primer = results.get(
                    "PRIMER_RIGHT_0_SEQUENCE"
                )

                left_tm = results.get(
                    "PRIMER_LEFT_0_TM"
                )

                right_tm = results.get(
                    "PRIMER_RIGHT_0_TM"
                )

                left_gc = results.get(
                    "PRIMER_LEFT_0_GC_PERCENT"
                )

                right_gc = results.get(
                    "PRIMER_RIGHT_0_GC_PERCENT"
                )

                product_size = results.get(
                    "PRIMER_PAIR_0_PRODUCT_SIZE"
                )

                # -------------------------------------------------
                # RESULTS
                # -------------------------------------------------

                st.success(
                    "Primer design completed successfully!"
                )

                st.subheader(
                    "3. Designed Primer Pair"
                )

                if left_primer and right_primer:

                    # Forward primer
                    st.markdown(
                        "### 🟢 Forward Primer"
                    )

                    st.code(
                        left_primer,
                        language="text"
                    )

                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric(
                            "Length",
                            f"{len(left_primer)} bp"
                        )

                    with col2:
                        st.metric(
                            "Tm",
                            f"{left_tm:.2f} °C"
                        )

                    st.write(
                        f"GC Content: **{left_gc:.2f}%**"
                    )

                    st.divider()

                    # Reverse primer
                    st.markdown(
                        "### 🔵 Reverse Primer"
                    )

                    st.code(
                        right_primer,
                        language="text"
                    )

                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric(
                            "Length",
                            f"{len(right_primer)} bp"
                        )

                    with col2:
                        st.metric(
                            "Tm",
                            f"{right_tm:.2f} °C"
                        )

                    st.write(
                        f"GC Content: **{right_gc:.2f}%**"
                    )

                    st.divider()

                    # Product size
                    st.markdown(
                        "### 🧪 PCR Product"
                    )

                    st.metric(
                        "Expected Product Size",
                        f"{product_size} bp"
                    )

                    st.divider()

                    # -------------------------------------------------
                    # BLAST SECTION
                    # -------------------------------------------------

                    st.subheader(
                        "4. Primer Specificity — NCBI BLAST"
                    )

                    st.info(
                        "Use BLAST to check whether the designed "
                        "primer sequence matches unintended regions "
                        "in nucleotide databases."
                    )

                    show_blast(
                        "Forward Primer",
                        left_primer
                    )

                    st.divider()

                    show_blast(
                        "Reverse Primer",
                        right_primer

                    )

                else:

                    st.warning(
                        "Primer3 could not find a suitable primer pair "
                        "with the selected parameters."
                    )

                    if results.get(
                        "PRIMER_WARNING"
                    ):

                        st.write(
                            results["PRIMER_WARNING"]
                        )

            except Exception as e:

                st.error(
                    "Primer design failed."
                )

                st.write(
                    "Error:",
                    str(e)
                )



st.divider()

st.subheader(
    "ℹ️ About this Application"
)

st.write(
    """
    This application uses Primer3 for PCR primer design.

    **Main features:**
    - DNA sequence validation
    - Primer length optimization
    - Melting temperature (Tm) control
    - GC content control
    - PCR product size selection
    - Forward and reverse primer design
    - NCBI BLAST-based primer specificity checking
    """
)

st.caption(
    "Primer Designer — Academic Project"
)
