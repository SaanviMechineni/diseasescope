"""Plain-language public-health awareness content (general information, not medical advice).

Wording follows the WHO fact sheets linked in SOURCES (checked 2026-10-25).
No helpline numbers or statistics are included on purpose.
"""

MOHFW = ("Ministry of Health and Family Welfare (MoHFW)", "https://www.mohfw.gov.in/")
NCVBDC = ("National Center for Vector Borne Diseases Control (NCVBDC)", "https://ncvbdc.mohfw.gov.in/")
WHO_INDIA = ("WHO India", "https://www.who.int/india")

SOURCES = {
    "Dengue": [("WHO fact sheet: Dengue and severe dengue", "https://www.who.int/news-room/fact-sheets/detail/dengue-and-severe-dengue"), NCVBDC, MOHFW],
    "Malaria": [("WHO fact sheet: Malaria", "https://www.who.int/news-room/fact-sheets/detail/malaria"), NCVBDC, MOHFW],
    "Acute Diarrheal Disease": [("WHO fact sheet: Diarrhoeal disease", "https://www.who.int/news-room/fact-sheets/detail/diarrhoeal-disease"), MOHFW],
    "Measles": [("WHO fact sheet: Measles", "https://www.who.int/news-room/fact-sheets/detail/measles"), MOHFW],
    "H1N1 (Seasonal Influenza-A)": [("WHO fact sheet: Influenza (seasonal)", "https://www.who.int/news-room/fact-sheets/detail/influenza-(seasonal)"), MOHFW],
}

ADVICE = {
    "Dengue": {
        "icon": "🦟",
        "spread": ["Bites of infected female Aedes mosquitoes (mainly Aedes aegypti).",
                   "These mosquitoes bite during the day.",
                   "They breed in clean standing water in containers, coolers, pots and tyres."],
        "symptoms": ["High fever, severe headache, pain behind the eyes.",
                     "Muscle and joint pain, nausea, vomiting, swollen glands, rash.",
                     "Usually starts 4–10 days after the bite; many people have mild illness."],
        "prevention": ["Empty, clean and cover water containers every week.",
                       "Wear clothing that covers arms and legs; use repellent and window screens.",
                       "Use mosquito nets for anyone sleeping during the day."],
        "doctor": ["Severe stomach pain, repeated vomiting, fast breathing.",
                   "Bleeding gums or nose, blood in vomit or stool.",
                   "Extreme tiredness, restlessness, pale cold skin — seek care immediately.",
                   "WHO advises against aspirin/ibuprofen for dengue because they can increase bleeding risk."],
    },
    "Malaria": {
        "icon": "🦟",
        "spread": ["Bites of infected female Anopheles mosquitoes.",
                   "These mosquitoes mostly bite from dusk to dawn.",
                   "Can also spread through blood transfusion or shared needles."],
        "symptoms": ["Fever, headache and chills.",
                     "Usually appear about 10–15 days after the bite.",
                     "Severe malaria: extreme tiredness, confusion, difficulty breathing."],
        "prevention": ["Sleep under a mosquito net, ideally insecticide-treated.",
                       "Use repellent and cover arms and legs after dusk; use window screens.",
                       "Do not let water collect around the home."],
        "doctor": ["Any fever in an area where malaria occurs — get tested early.",
                   "WHO recommends confirming every suspected case with a blood test.",
                   "Confusion, breathing difficulty or extreme weakness need emergency care."],
    },
    "Acute Diarrheal Disease": {
        "icon": "💧",
        "spread": ["Contaminated drinking water or food.",
                   "Person to person when hand hygiene is poor.",
                   "Poor sanitation and open defecation increase spread."],
        "symptoms": ["Three or more loose or watery stools in a day.",
                     "Stomach cramps, vomiting, sometimes fever.",
                     "The main danger is dehydration (loss of water and salts)."],
        "prevention": ["Drink safe water (boiled or treated) and store it covered.",
                       "Wash hands with soap after using the toilet and before eating or cooking.",
                       "Use a toilet; keep food covered and cook it well.",
                       "Exclusive breastfeeding for the first 6 months; rotavirus vaccination for infants."],
        "doctor": ["Signs of dehydration: very sleepy, sunken eyes, unable to drink, skin pinch goes back slowly.",
                   "Blood in the stool or diarrhoea lasting many days.",
                   "WHO recommends ORS (oral rehydration solution); zinc for children as advised by a health worker."],
    },
    "Measles": {
        "icon": "🧒",
        "spread": ["One of the most contagious diseases; spreads through coughs, sneezes and shared air.",
                   "The virus can stay in the air or on surfaces for up to 2 hours.",
                   "People are contagious from about 4 days before the rash appears."],
        "symptoms": ["Fever, runny nose, cough, red and watery eyes.",
                     "A rash appears 3–5 days later, usually starting on the face and neck.",
                     "Symptoms usually start 7–14 days after exposure."],
        "prevention": ["Two doses of measles-containing vaccine protect children.",
                       "Check your child's immunisation card and complete missed doses at a government health centre.",
                       "Keep a sick child away from others, especially babies."],
        "doctor": ["Any suspected measles — so it can be confirmed and others protected.",
                   "Breathing difficulty, severe diarrhoea, eye problems, fits or drowsiness.",
                   "Complications are more common in children under 5 and malnourished children."],
    },
    "H1N1 (Seasonal Influenza-A)": {
        "icon": "🤧",
        "spread": ["Droplets when an infected person coughs or sneezes.",
                   "Contaminated hands touching the nose, mouth or eyes.",
                   "Spreads easily in crowded indoor places."],
        "symptoms": ["Sudden fever, cough, sore throat.",
                     "Body aches, headache and tiredness."],
        "prevention": ["Vaccination is the best prevention (WHO); ask a doctor if you are in a high-risk group.",
                       "Wash hands regularly; cover your mouth and nose when coughing or sneezing.",
                       "Stay home when unwell."],
        "doctor": ["Difficulty breathing, chest pain, or fever that does not improve.",
                   "Higher-risk people should seek advice early: pregnant women, children under 5, older people, "
                   "and people with chronic illness or weak immunity."],
    },
}

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Indicative seasonal pattern (0 = lower, 1 = moderate, 2 = higher). This is a general
# awareness guide, NOT derived from this dataset (which is annual) and varies by state.
SEASONAL = {
    "Dengue":                      [0, 0, 0, 0, 0, 1, 1, 2, 2, 2, 2, 1],
    "Malaria":                     [0, 0, 0, 0, 1, 1, 2, 2, 2, 2, 1, 0],
    "Acute Diarrheal Disease":     [0, 0, 1, 1, 2, 2, 2, 2, 1, 1, 0, 0],
    "Measles":                     [1, 2, 2, 2, 1, 0, 0, 0, 0, 0, 0, 1],
    "H1N1 (Seasonal Influenza-A)": [2, 2, 1, 0, 0, 1, 1, 2, 1, 0, 0, 1],
}
SEASON_NOTE = {
    "Dengue": "Rises with monsoon rains and peaks in the post-monsoon months when water collects in containers.",
    "Malaria": "Linked to monsoon rainfall and stagnant water; in some forest and tribal areas it occurs year-round.",
    "Acute Diarrheal Disease": "Higher in hot summer months and during monsoon flooding when water gets contaminated.",
    "Measles": "Can occur at any time; outbreaks are often reported in late winter and spring.",
    "H1N1 (Seasonal Influenza-A)": "WHO notes flu in tropical regions can occur all year; in India peaks are often seen in winter and in the monsoon, varying by region.",
}

DISCLAIMER = ("**This is general health awareness information, not medical advice.** "
              "It does not replace a doctor or health worker. If you or someone else feels unwell, "
              "visit your nearest health centre. Seasonal patterns shown are indicative only and "
              "vary by state and year.")
