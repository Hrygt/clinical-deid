# medical_whitelist.py - Clinical terms that should NOT be de-identified
# These are medical terms that pattern-match as names (Title Case two-word phrases)
# but are actually clinical terminology that must be preserved.
#
# Usage: from medical_whitelist import MEDICAL_WHITELIST
#        if detected_text in MEDICAL_WHITELIST:
#            skip_replacement()
#
# Last Updated: December 8, 2025
# Maintainer: Gary Riggs, MD | RIGGSMED LLC

MEDICAL_WHITELIST = {
    # === ROLE WORDS / ABBREVIATIONS THE NER MISREADS AS NAMES ===
    # e.g. "Pt reports..." (= patient) was being surrogate-replaced with a fake
    # first name like "Patricia". These are never real patient names.
    "Pt",
    "Pts",
    "Patient",
    "Patients",
    "Mom",
    "Dad",
    "Wife",
    "Husband",
    "Spouse",
    "Mother",
    "Father",
    "Son",
    "Daughter",
    # === MEDICAL EPONYM SURNAMES (clinical terms that are also surnames) ===
    # ULTRA-DISTINCTIVE eponyms ONLY: names essentially never a real US patient
    # surname, so whitelisting carries ~zero leak risk. Measured 2026-06: the NER
    # already preserves the plausible-surname eponyms (Parkinson, Cushing, Crohn,
    # Hodgkin, Glasgow, Gleason, Sjogren, Raynaud, Charcot, Murphy...), so those are
    # DELIBERATELY EXCLUDED — whitelisting them would only add leak risk for a patient
    # actually named that, with no benefit. This narrow set fixes the rare residual
    # garble (e.g. "Homan sign" -> a fake name) with no downside. Gazetteer stays off.
    "Babinski", "Kernig", "Brudzinski", "Wernicke", "Korsakoff", "Boerhaave",
    "Dupuytren", "Chvostek", "Trousseau", "Rovsing", "Kehr", "Phalen", "Tinel",
    "McBurney", "Lhermitte", "Courvoisier", "Kussmaul", "Buerger", "Henoch",
    "Schonlein", "Alport", "DeQuervain", "Duchenne", "Marfan", "Ehlers", "Danlos",
    "Klinefelter", "DiGeorge", "Pancoast", "Wegener", "Goodpasture", "Caprini",
    "Krukenberg", "Takayasu", "Behcet", "Marjolin", "Troisier", "Kartagener",
    "Wenckebach", "Brugada", "Prinzmetal", "Eisenmenger", "Zollinger", "Friderichsen",
    "Crigler", "Najjar", "Bartter", "Gitelman", "Liddle", "Caroli", "Wallenberg",
    "Homans", "Homan",
    # === LAB VALUES & CHEMISTRY ===
    "Anion Gap",
    "Base Excess",
    "Base Deficit",
    "Blood Gas",
    "Blood Gases",
    "Carbon Dioxide",
    "Direct Bilirubin",
    "Indirect Bilirubin",
    "Total Bilirubin",
    "Conjugated Bilirubin",
    "Unconjugated Bilirubin",
    "Blood Urea",
    "Urea Nitrogen",
    "Lactic Acid",
    "Uric Acid",
    "Folic Acid",
    "Ascorbic Acid",
    "Fatty Acids",
    "Amino Acids",
    "Nucleic Acids",
    "Bile Acids",
    "Vanillylmandelic Acid",
    "Homovanillic Acid",
    "Delta Aminolevulinic Acid",
    
    # === HEMATOLOGY ===
    "White Blood",
    "Red Blood",
    "White Count",
    "Red Count",
    "Platelet Count",
    "Blood Count",
    "Mean Corpuscular",
    "Mean Platelet",
    "Red Cell",
    "White Cell",
    "Packed Cell",
    "Reticulocyte Count",
    "Absolute Neutrophil",
    "Absolute Lymphocyte",
    "Absolute Monocyte",
    "Absolute Eosinophil",
    "Absolute Basophil",
    "Band Neutrophils",
    "Segmented Neutrophils",
    "Atypical Lymphocytes",
    "Nucleated Red",
    "Immature Granulocytes",
    "Immature Platelet",
    
    # === COAGULATION ===
    "Partial Thromboplastin",
    "Prothrombin Time",
    "Bleeding Time",
    "Clotting Time",
    "Thrombin Time",
    "Fibrin Degradation",
    "Fibrin Split",
    "Clot Retraction",
    
    # === CARDIAC MARKERS ===
    "Brain Natriuretic",
    "Troponin Level",
    "Cardiac Enzymes",
    "Creatine Kinase",
    "Lactate Dehydrogenase",
    "Myocardial Infarction",
    
    # === RENAL FUNCTION ===
    "Glomerular Filtration",
    "Creatinine Clearance",
    "Urine Output",
    "Urine Osmolality",
    "Serum Osmolality",
    "Fractional Excretion",
    "Tubular Reabsorption",
    
    # === LIVER FUNCTION ===
    "Alkaline Phosphatase",
    "Gamma Glutamyl",
    "Alanine Aminotransferase",
    "Aspartate Aminotransferase",
    "Liver Function",
    "Hepatic Function",
    "Hepatic Panel",
    "Liver Panel",
    "Liver Enzymes",
    
    # === THYROID ===
    "Thyroid Stimulating",
    "Free Thyroxine",
    "Total Thyroxine",
    "Free Triiodothyronine",
    "Thyroid Peroxidase",
    "Thyroid Function",
    "Thyroid Panel",
    "Thyroglobulin Antibodies",
    
    # === LIPID PANEL ===
    "Total Cholesterol",
    "Triglyceride Level",
    "Lipid Panel",
    "Lipid Profile",
    "Lipoprotein Panel",
    "Apolipoprotein Panel",
    
    # === URINALYSIS ===
    "Urine Culture",
    "Urine Protein",
    "Urine Glucose",
    "Urine Ketones",
    "Urine Bilirubin",
    "Urine Urobilinogen",
    "Urine Specific",
    "Specific Gravity",
    "Urine Sediment",
    "Urine Microscopy",
    "Urine Analysis",
    "Clean Catch",
    "Midstream Urine",
    
    # === MICROBIOLOGY ===
    "Blood Culture",
    "Wound Culture",
    "Sputum Culture",
    "Throat Culture",
    "Stool Culture",
    "Cerebrospinal Fluid",
    "Gram Stain",
    "Acid Fast",
    "Colony Count",
    "Sensitivity Testing",
    "Minimum Inhibitory",
    "Bacterial Culture",
    "Fungal Culture",
    "Viral Culture",
    
    # === IMAGING TERMS ===
    "Chest Xray",
    "Chest Film",
    "Portable Chest",
    "Lateral Decubitus",
    "Computed Tomography",
    "Magnetic Resonance",
    "Nuclear Medicine",
    "Positron Emission",
    "Bone Scan",
    "Gallium Scan",
    "Ventilation Perfusion",
    "Contrast Enhanced",
    "Non Contrast",
    "With Contrast",
    "Without Contrast",
    
    # === VITAL SIGNS ===
    "Blood Pressure",
    "Heart Rate",
    "Pulse Rate",
    "Respiratory Rate",
    "Oxygen Saturation",
    "Pulse Oximetry",
    "Temperature Oral",
    "Temperature Rectal",
    "Temperature Axillary",
    "Temperature Tympanic",
    "Pain Scale",
    "Pain Score",
    "Body Mass",
    "Body Weight",
    "Body Temperature",
    
    # === ANATOMY (commonly misidentified) ===
    "Left Atrium",
    "Right Atrium",
    "Left Ventricle",
    "Right Ventricle",
    "Left Arm",
    "Right Arm",
    "Left Leg",
    "Right Leg",
    "Left Eye",
    "Right Eye",
    "Left Ear",
    "Right Ear",
    "Left Lung",
    "Right Lung",
    "Left Kidney",
    "Right Kidney",
    "Upper Extremity",
    "Lower Extremity",
    "Upper Lobe",
    "Lower Lobe",
    "Middle Lobe",
    "Frontal Lobe",
    "Parietal Lobe",
    "Temporal Lobe",
    "Occipital Lobe",
    "Spinal Cord",
    "Brain Stem",
    "Lymph Node",
    "Lymph Nodes",
    
    # === EPONYMOUS CONDITIONS (named after people but are diagnoses) ===
    "Bells Palsy",
    "Bell Palsy",
    "Cushings Syndrome",
    "Cushing Syndrome",
    "Addisons Disease",
    "Addison Disease",
    "Parkinsons Disease",
    "Parkinson Disease",
    "Alzheimers Disease",
    "Alzheimer Disease",
    "Hodgkins Lymphoma",
    "Hodgkin Lymphoma",
    "Non Hodgkins",
    "Non Hodgkin",
    "Graves Disease",
    "Hashimotos Thyroiditis",
    "Hashimoto Thyroiditis",
    "Crohns Disease",
    "Crohn Disease",
    "Barretts Esophagus",
    "Barrett Esophagus",
    "Raynauds Phenomenon",
    "Raynaud Phenomenon",
    "Dupuytrens Contracture",
    "Dupuytren Contracture",
    "Marfan Syndrome",
    "Ehlers Danlos",
    "Down Syndrome",
    "Turner Syndrome",
    "Klinefelter Syndrome",
    "Gilbert Syndrome",
    "Dubin Johnson",
    "Rotor Syndrome",
    "Crigler Najjar",
    "Wilson Disease",
    "Meniere Disease",
    "Menieres Disease",
    "Lou Gehrig",
    "Lou Gehrigs",
    "Guillain Barre",
    "Reye Syndrome",
    "Reyes Syndrome",
    "Stevens Johnson",
    "Kawasaki Disease",
    "Wegener Granulomatosis",
    "Wegeners Granulomatosis",
    "Sjogren Syndrome",
    "Sjogrens Syndrome",
    "Behcet Disease",
    "Behcets Disease",
    "Paget Disease",
    "Pagets Disease",
    "Hirschsprung Disease",
    "Hirschsprungs Disease",
    "Henoch Schonlein",
    "Felty Syndrome",
    "Feltys Syndrome",
    "Still Disease",
    "Stills Disease",
    "Wolff Parkinson",
    "Brugada Syndrome",
    "Osler Weber",
    "Von Willebrand",
    "Christmas Disease",
    "Bernard Soulier",
    "Wiskott Aldrich",
    "Chediak Higashi",
    "Job Syndrome",
    "Jobs Syndrome",
    "DiGeorge Syndrome",
    "Bruton Agammaglobulinemia",
    "Brutons Agammaglobulinemia",
    
    # === CLINICAL SCALES & SCORES ===
    "Glasgow Coma",
    "Apache Score",
    "Apache II",
    "Apache III",
    "Sofa Score",
    "Wells Score",
    "Wells Criteria",
    "Ranson Criteria",
    "Ransons Criteria",
    "Child Pugh",
    "Child Turcotte",
    "Meld Score",
    "Bishop Score",
    "Apgar Score",
    "Braden Scale",
    "Norton Scale",
    "Morse Fall",
    "Karnofsky Score",
    "Karnofsky Performance",
    "Eastern Cooperative",
    "Framingham Risk",
    "Killip Class",
    "Killip Classification",
    "New York Heart",
    
    # === PROCEDURES & TESTS ===
    "Lumbar Puncture",
    "Spinal Tap",
    "Bone Marrow",
    "Fine Needle",
    "Core Biopsy",
    "Open Biopsy",
    "Incision Drainage",
    "Central Line",
    "Arterial Line",
    "Peripheral Line",
    "Foley Catheter",
    "Nasogastric Tube",
    "Endotracheal Tube",
    "Chest Tube",
    "Peg Tube",
    "Tracheostomy Tube",
    
    # === MEDICATION ROUTES ===
    "By Mouth",
    "Per Oral",
    "Per Rectum",
    "Per Vagina",
    "Intravenous Push",
    "Intravenous Drip",
    "Intramuscular Injection",
    "Subcutaneous Injection",
    "Topical Application",

    # === CONTROLLED-SUBSTANCE DRUG NAMES (full-word NER name-FP fix) ===
    # Short, name-like medication tokens (esp. brands at a clause boundary) get mis-tagged
    # FIRST_NAME/LAST_NAME and surrogated to fake names BEFORE the grader sees them
    # (Ativan->William, Versed->Amanda, Valium->a fake name, Dolophine->a fake name),
    # which defeats the downstream parenteral-controlled IM-adjudicate detector. The
    # exact-match filter (filter_whitelisted_entities) drops these pre-surrogation.
    # SCOPE: prophylactic — the full controlled-substance lexicon (brands + generics); EVERY
    # token surname-checked against the faker first/last-name lists (0 collisions; none is a
    # plausible US patient surname, consistent with the eponym-exclusion discipline above).
    # CASE: MEDICAL_WHITELIST_LOWER handles all casings.
    # BOUNDARY: this CANNOT catch the SUBWORD mode (Valium->"Val", methadone->"m"/"meth") —
    # that is the NER span-sanity guard's job (a separate fix). Do NOT trim the "survive in
    # one context" tokens: the FP is context-sensitive, so they are forward defense.
    # -- opioids (CII; butorphanol is a CIV mixed agonist-antagonist) --
    "morphine", "hydromorphone", "fentanyl", "oxymorphone", "meperidine", "methadone",
    "sufentanil", "remifentanil", "butorphanol",
    # -- benzodiazepines (CIV) --
    "lorazepam", "midazolam", "diazepam", "chlordiazepoxide",
    # -- other (ketamine CIII; barbiturates CII/CIV) --
    "ketamine", "secobarbital", "phenobarbital",
    # -- brand names (the dominant full-word failers) --
    "Ativan", "Versed", "Valium", "Dilaudid", "Sublimaze", "Demerol", "Dolophine", "Luminal",

    # === NAME-FRAGMENT REPAIR WITNESSES (fix/name-span-fragment-repair) ===
    # The span repair (_repair_name_span_fragments) DROPS a *_NAME fragment whose full
    # surrounding word is in this whitelist — otherwise it EXPANDS and surrogates the whole
    # word. This list is therefore LOAD-BEARING for grading fidelity: a fragment-FP on a
    # non-whitelisted drug over-scrubs it and silently under-credits Risk. Fix any observed
    # drug loss by ADDING the drug here, never by weakening the repair. Surname-collision
    # discipline as above (neither is a plausible US surname).
    "cefepime", "clozapine",
    # 2026-07-19 (fix/name-span-newline-boundary, grader note 466697e91ec0): the
    # title-recall newline sweep ate line-leading "Propranolol" after "See Dr Tracy" —
    # structural fix is the horizontal-whitespace separators in _TITLE_RE/_CRED_RE;
    # these entries are belt-and-suspenders for the witnessed clinical victims.
    # "Will"/"Present" deliberately NOT added (plausible real name / PHI asymmetry).
    "propranolol", "bradycardia",

    # === SPECIALTY / SERVICE NOUNS (fix/specialty-whitelist, grader report d75ee47a6443) ===
    # Witness: "The case was discussed with podiatry." -> "...discussed with Patricia."
    # The trigger is the name-likely frame ("discussed with <Capitalized>", "<Specialty>
    # consulted"), and before this block the file held ZERO specialty words, so nothing
    # could veto. A specialty token de-id has already deleted is UNRECOVERABLE by any
    # downstream grader vocabulary (corpus/README.md cat3-podiatry-token) — the Cat 3
    # externality axis reads exactly these words.
    # CENSUS (2026-07-27, read-only over gold 918 + reports 77 + accuracy 425): 58 distinct
    # specialty tokens in ~330 discussion-frame hits; "Podiatry" was Title-cased in 8/8
    # occurrences — Title case is the vulnerable shape, and the model tags it FIRST_NAME.
    # ADMISSION RULE — nouns only, and NOTHING that is a plausible person name (PHI
    # ASYMMETRY: a whitelisted token survives redaction EVERYWHERE, so a patient with that
    # surname would leak). Every token below was checked against the faker first/last-name
    # lists (0 collisions) AND judged by hand.
    # DELIBERATELY EXCLUDED, with reasons:
    #   "endo"  — Endo is a common Japanese surname (leak vector), despite 0 faker hits;
    #   "cards" — the Card/Cards surname family, and a common English word;
    #   ALL 2-3 letter abbreviations (ID, GI, PA, PT, OT, CM, IR, RD, RT, SLP, PCP, CTS,
    #     ENT, NP, RN) — patient-initials shaped; the census recommends gating those on the
    #     FRAME, which this context-free exact-match filter cannot express. Parked.
    #   "family"/"patient"/"daughter" — role words, already covered above, and not specialties.
    # -- full specialty nouns --
    "podiatry", "podiatrist",
    "cardiology", "cardiologist", "cardiothoracic", "electrophysiology",
    "nephrology", "nephrologist", "renal",
    "pulmonology", "pulmonologist",
    "urology", "urologist",
    "neurology", "neurologist", "neurosurgery", "neurosurgeon",
    "psychiatry", "psychiatrist",
    "oncology", "oncologist", "hematology", "hematologist",
    "endocrinology", "endocrinologist",
    "gastroenterology", "gastroenterologist",
    "rheumatology", "rheumatologist",
    "dermatology", "dermatologist",
    "radiology", "pathology", "ophthalmology", "otolaryngology",
    "anesthesia", "anesthesiology", "anesthesiologist",
    "orthopedics", "orthopaedics", "orthopedic",
    "physiatry", "physiatrist",
    "hospitalist", "intensivist", "infectious", "interventional", "vascular", "surgery",
    "nursing", "nutrition", "dietitian", "pharmacy", "pharmacist",
    "palliative", "hospice",
    # -- clipped service forms actually witnessed in the census (none is a surname) --
    "neuro", "nephro", "pulm", "psych", "ortho", "heme", "onc",
    # -- service bigrams (the adjacent-name-pair path in filter_whitelisted_entities
    #    handles these, as does a single span whose text is the whole bigram) --
    "Wound Care", "Case Management", "Care Management", "Infectious Disease",
    "General Surgery", "Vascular Surgery", "Cardiothoracic Surgery", "Palliative Care",
    "Interventional Radiology", "Pain Management", "Critical Care", "Speech Therapy",
    "Physical Therapy", "Occupational Therapy", "Respiratory Therapy", "Social Work",

    # === ORGANISM VOCABULARY (same mechanism as the specialty block) ===
    # Witness: "Enterobacter cloacae" -> "Enterobacter gonzalez" (gold 87a23c58a070 /
    # report 87c3e2001703); also "Proteus mirabilis" -> "Eric Terry" (reproduced live
    # 2026-07-27), "Morganella morganii" -> "Morganella morbolton". The NER reads a
    # binomial as First+Last and surrogates the species epithet (and sometimes the genus)
    # as a person name — the culture result is destroyed for the Data axis.
    # Same admission rule. EXCLUDED: "candida" (Cándida is a real Spanish/Italian given
    # name) and "providencia" (likewise) — their EPITHETS are still whitelisted below, so
    # "Candida albicans" degrades to a surrogated genus rather than a garbled binomial.
    # NOT CLOSED BY THIS: sub-token glueing ("Klebsiella pneumoniajones",
    # "Streptococcus viridCWNP") is the NER span-fragment problem, not a vocabulary gap.
    # -- genera --
    "enterobacter", "escherichia", "klebsiella", "pseudomonas", "staphylococcus",
    "streptococcus", "enterococcus", "proteus", "serratia", "citrobacter",
    "acinetobacter", "clostridium", "clostridioides", "haemophilus", "moraxella",
    "morganella", "stenotrophomonas", "bacteroides", "corynebacterium",
    # -- species epithets (census-present + the common siblings) --
    "aureus", "pneumoniae", "coli", "cloacae", "cloaca", "oxytoca", "aeruginosa",
    "epidermidis", "faecalis", "faecium", "mirabilis", "marcescens", "freundii",
    "baumannii", "albicans", "glabrata", "difficile", "influenzae", "catarrhalis",
    "morganii", "stuartii", "maltophilia", "fragilis", "vulgaris", "raffinosus",
    "viridans", "constellatus", "parapsilosis", "agalactiae", "capitis", "avium",
    "dysgalactiae", "vestibularis", "lutetiensis", "mucogenicum", "phocaicum",
    "planticola", "striatum", "tropicalis", "krusei", "anginosus", "pyogenes",
    "saprophyticus", "haemolyticus", "lugdunensis",

    # === CLINICAL STATUS ===
    "Present On",
    "Present Illness",
    "History Of",
    "Chief Complaint",
    "Review Of",
    "Physical Examination",
    "Assessment Plan",
    "Differential Diagnosis",
    "Working Diagnosis",
    "Final Diagnosis",
    "Discharge Diagnosis",
    "Admission Diagnosis",
    "Primary Diagnosis",
    "Secondary Diagnosis",
    "Hospital Course",
    "Clinical Course",
    "Follow Up",
    "Follow-Up",
    
    # === COMMON FALSE POSITIVES FROM LAB SYSTEMS ===
    "Order Status",
    "Order Completed",
    "Order Canceled",
    "Order Cancelled",
    "Order Pending",
    "Specimen Blood",
    "Specimen Urine",
    "Specimen Type",
    "Collection Date",
    "Collection Time",
    "Result Date",
    "Result Time",
    "Reference Range",
    "Critical Value",
    "Critical High",
    "Critical Low",
    "Normal Range",
    "Updated Date",
    "Collected Date",
    "Procedure Name",
    "Component Name",
    "Test Name",
    "Lab Name",
    
    # === EHR TEMPLATE TERMS ===
    "Gen Alert",
    "Gen Appearance",
    "Pertinent Exam",
    "Pertinent Findings",
    "Pertinent Labs",
    "Pertinent History",
    "Pertinent Positives",
    "Pertinent Negatives",
    "Review Systems",
    "Social History",
    "Family History",
    "Past Medical",
    "Past Surgical",
    "Medication List",
    "Allergy List",
    "Problem List",
    "Active Problems",
    "Resolved Problems",
    "Discharge Summary",
    "Progress Note",
    "Admission Note",
    "Consult Note",
    "Operative Note",
    "Procedure Note",
}

# Lowercase version for case-insensitive matching
MEDICAL_WHITELIST_LOWER = {term.lower() for term in MEDICAL_WHITELIST}

def is_medical_term(text: str) -> bool:
    """Check if text is a whitelisted medical term (case-insensitive)."""
    return text.lower() in MEDICAL_WHITELIST_LOWER

def is_medical_term_exact(text: str) -> bool:
    """Check if text is a whitelisted medical term (exact case match)."""
    return text in MEDICAL_WHITELIST
