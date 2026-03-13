"""
chroma_utils.py — ChromaDB utilities for the Jan-Sahayak Fact Checker.

Handles document embedding, seeding, and retrieval against an
in-memory vector store of government schemes and news.
"""

import chromadb


client = chromadb.EphemeralClient()

COLLECTION_NAME = "govt_schemes"

SEED_DOCUMENTS = [
    {
        "id": "ayushman_bharat_1",
        "text": "Ayushman Bharat Pradhan Mantri Jan Arogya Yojana (PM-JAY) provides health insurance cover of Rs 5 lakh per family per year for secondary and tertiary care hospitalization. It covers over 10.74 crore poor and vulnerable families. The scheme is cashless and paperless at public and empanelled private hospitals.",
        "metadata": {"category": "health", "scheme": "Ayushman Bharat PM-JAY"},
    },
    {
        "id": "pm_kisan_1",
        "text": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi) provides income support of Rs 6,000 per year in three equal instalments to all landholding farmer families. The amount is directly transferred to the bank accounts of the beneficiaries. Over 11 crore farmers benefit from this scheme.",
        "metadata": {"category": "agriculture", "scheme": "PM-KISAN"},
    },
    {
        "id": "mgnrega_1",
        "text": "MGNREGA (Mahatma Gandhi National Rural Employment Guarantee Act) guarantees 100 days of wage employment per year to every rural household whose adult members volunteer to do unskilled manual work. The current wage rate varies by state, ranging from Rs 220 to Rs 333 per day.",
        "metadata": {"category": "employment", "scheme": "MGNREGA"},
    },
    {
        "id": "pm_ujjwala_1",
        "text": "Pradhan Mantri Ujjwala Yojana provides free LPG connections to women from Below Poverty Line (BPL) households. Under Ujjwala 2.0, migrant workers can also get connections with self-declaration. Over 9.6 crore LPG connections have been released.",
        "metadata": {"category": "energy", "scheme": "PM Ujjwala Yojana"},
    },
    {
        "id": "pm_awas_1",
        "text": "Pradhan Mantri Awas Yojana (PMAY) aims to provide affordable housing to the urban and rural poor. Under PMAY-Gramin, the assistance is Rs 1.20 lakh in plain areas and Rs 1.30 lakh in hilly areas. Under PMAY-Urban, the subsidy ranges from Rs 2.35 lakh to Rs 2.67 lakh.",
        "metadata": {"category": "housing", "scheme": "PM Awas Yojana"},
    },
    {
        "id": "jan_dhan_1",
        "text": "Pradhan Mantri Jan Dhan Yojana (PMJDY) is a financial inclusion program. Every unbanked adult gets a bank account with zero balance, a RuPay debit card, and Rs 2 lakh accident insurance cover. Over 50 crore accounts have been opened under this scheme.",
        "metadata": {"category": "finance", "scheme": "PM Jan Dhan Yojana"},
    },
    {
        "id": "sukanya_samriddhi_1",
        "text": "Sukanya Samriddhi Yojana is a savings scheme for the girl child. It offers an interest rate of 8.2% per annum (as of 2024). Minimum deposit is Rs 250 per year and maximum is Rs 1.5 lakh. The account matures after 21 years from the date of opening.",
        "metadata": {"category": "savings", "scheme": "Sukanya Samriddhi Yojana"},
    },
    {
        "id": "ration_card_1",
        "text": "Under the National Food Security Act (NFSA), eligible households receive subsidized food grains through the Public Distribution System (PDS). Antyodaya Anna Yojana (AAY) families get 35 kg per month. Priority Household (PHH) cards get 5 kg per person per month at Rs 1-3 per kg.",
        "metadata": {"category": "food", "scheme": "NFSA / Ration Card"},
    },
    {
        "id": "digital_india_1",
        "text": "Digital India programme aims to transform India into a digitally empowered society. Key initiatives include DigiLocker for document storage, UMANG app for government services, BharatNet for rural broadband, and Common Service Centres (CSCs) for digital access in villages.",
        "metadata": {"category": "technology", "scheme": "Digital India"},
    },
    {
        "id": "mudra_loan_1",
        "text": "Pradhan Mantri MUDRA Yojana provides loans up to Rs 10 lakh to non-corporate, non-farm small/micro enterprises. Three categories: Shishu (up to Rs 50,000), Kishore (Rs 50,001 to Rs 5 lakh), and Tarun (Rs 5,00,001 to Rs 10 lakh). No collateral is required.",
        "metadata": {"category": "finance", "scheme": "PM MUDRA Yojana"},
    },
    {
        "id": "swachh_bharat_1",
        "text": "Swachh Bharat Mission aims to achieve universal sanitation coverage. Under SBM-Gramin, a financial incentive of Rs 12,000 is given for construction of individual household latrines. Over 11 crore toilets have been built. India was declared Open Defecation Free (ODF) in 2019.",
        "metadata": {"category": "sanitation", "scheme": "Swachh Bharat Mission"},
    },
    {
        "id": "pm_fasal_bima_1",
        "text": "Pradhan Mantri Fasal Bima Yojana (PMFBY) provides crop insurance to farmers at very low premium rates: 2% for Kharif crops, 1.5% for Rabi crops, and 5% for commercial/horticultural crops. Claims are settled based on crop cutting experiments and remote sensing technology.",
        "metadata": {"category": "agriculture", "scheme": "PM Fasal Bima Yojana"},
    },
    {
        "id": "skill_india_1",
        "text": "Skill India Mission (PMKVY - Pradhan Mantri Kaushal Vikas Yojana) provides free skill training and certification. Training is available in over 300 job roles across 40 sectors. Trainees receive Rs 8,000 on average as financial reward on successful certification.",
        "metadata": {"category": "education", "scheme": "Skill India / PMKVY"},
    },
    {
        "id": "fake_news_1",
        "text": "FACT: The Indian government has NOT announced any scheme giving Rs 15 lakh to every citizen's bank account. This is a recurring hoax spread via WhatsApp. The government's PIB Fact Check unit regularly debunks such claims on their official Twitter handle @PIBFactCheck.",
        "metadata": {"category": "fact_check", "scheme": "PIB Fact Check"},
    },
    {
        "id": "fake_news_2",
        "text": "FACT: There is no government scheme offering free smartphones to all citizens. Some state governments have specific schemes like Rajasthan's Free Smartphone Scheme for women, but there is no nationwide free smartphone distribution scheme. Always verify on official government websites.",
        "metadata": {"category": "fact_check", "scheme": "PIB Fact Check"},
    },
    {
        "id": "fake_news_3",
        "text": "FACT: WhatsApp messages claiming that the government will cut off old Rs 500 and Rs 2000 notes again are FALSE. The Rs 2000 note was withdrawn from circulation in 2023 but remained legal tender for exchange at banks until a set deadline. Always check RBI official announcements.",
        "metadata": {"category": "fact_check", "scheme": "RBI / Currency"},
    },
]


def init_collection():
    """Get or create the government schemes collection."""
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Indian government schemes and fact-checks"},
    )
    return collection


def seed_data(collection=None):
    """Seed the vector store with government scheme data (idempotent)."""
    if collection is None:
        collection = init_collection()

    existing = collection.get()
    existing_ids = set(existing["ids"]) if existing and existing["ids"] else set()

    new_docs = [d for d in SEED_DOCUMENTS if d["id"] not in existing_ids]

    if not new_docs:
        print(f"[ChromaDB] Collection already seeded with {len(existing_ids)} documents.")
        return collection

    collection.add(
        ids=[d["id"] for d in new_docs],
        documents=[d["text"] for d in new_docs],
        metadatas=[d["metadata"] for d in new_docs],
    )
    print(f"[ChromaDB] Seeded {len(new_docs)} new documents (total: {len(existing_ids) + len(new_docs)}).")
    return collection


def query_facts(text, n_results=3, collection=None):
    """
    Query the vector store for facts related to the input text.
    Returns a list of dicts: {text, metadata, distance}.
    """
    if collection is None:
        collection = init_collection()

    results = collection.query(
        query_texts=[text],
        n_results=min(n_results, len(SEED_DOCUMENTS)),
    )

    matches = []
    if results and results["documents"] and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            distance = results["distances"][0][i] if results["distances"] else None
            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            # Convert distance to a 0-100 confidence score
            # ChromaDB uses L2 distance by default; lower = more similar
            confidence = max(0, round(100 * (1 / (1 + distance)), 1)) if distance is not None else 0
            matches.append({
                "text": doc,
                "metadata": metadata,
                "distance": distance,
                "confidence": confidence,
            })

    return matches
