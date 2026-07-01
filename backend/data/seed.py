"""Self-contained synthetic talent pool.

Resumes are written as numbered lines so every screening claim can cite an exact
line (the evidence anchor). Languages are mixed on purpose so the router has to
route by language, not just difficulty. A few candidates carry skills the resume
does *not* support, so the verifier has something real to bounce.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from karya.core.models import Candidate, Job, Language, ResumeLine

DATA_DIR = Path(__file__).resolve().parent


def _c(
    cid: str,
    name: str,
    headline: str,
    location: str,
    language: str,
    years: float,
    skills: list[str],
    lines: list[str],
) -> Candidate:
    return Candidate(
        id=cid,
        name=name,
        headline=headline,
        location=location,
        language=Language(language),
        years_experience=years,
        skills=skills,
        resume=[ResumeLine(n=i + 1, text=t) for i, t in enumerate(lines)],
    )


# Hand-authored "hero" candidates that drive the demo narrative.
HERO_CANDIDATES: list[Candidate] = [
    _c(
        "cand_arya", "Arya Kulkarni",
        "Senior Backend Engineer", "Pune", "en", 8,
        ["Python", "Go", "Kubernetes", "PostgreSQL", "AWS", "payments"],
        [
            "Senior Backend Engineer based in Pune with 8 years of experience.",
            "Built high-throughput payment APIs in Python and Go at scale.",
            "Operated production Kubernetes clusters on AWS EKS for 4 years.",
            "Led the payments platform team at Razorpay handling UPI settlements.",
            "Designed PostgreSQL sharding for 12k transactions per second.",
        ],
    ),
    _c(
        "cand_rohit", "Rohit Deshmukh",
        "Backend Engineer", "Pune", "mr", 6,
        ["Java", "Spring", "Kafka", "MySQL", "microservices"],
        [
            "पुण्यात राहणारा बॅकएंड अभियंता, ६ वर्षांचा अनुभव.",  # Backend engineer in Pune, 6 yrs
            "Java आणि Spring Boot वापरून मायक्रोसर्व्हिसेस तयार केले.",  # built microservices
            "Kafka वर रिअल-टाइम इव्हेंट पाइपलाइन हाताळली.",  # handled Kafka pipelines
            "MySQL डेटाबेस ऑप्टिमायझेशनवर काम केले.",  # worked on MySQL optimization
        ],
    ),
    _c(
        "cand_lakshmi", "Lakshmi Reddy",
        "Backend Engineer", "Pune", "te", 5,
        ["Python", "Django", "Redis", "Docker", "REST"],
        [
            "పూణేలో ఉంటున్న బ్యాకెండ్ ఇంజనీర్, 5 సంవత్సరాల అనుభవం.",  # Pune backend eng, 5 yrs
            "Python మరియు Django తో REST APIలను నిర్మించారు.",  # built REST APIs in Django
            "Redis కాషింగ్ మరియు Docker కంటైనర్లను ఉపయోగించారు.",  # Redis + Docker
            "రోజుకు 2 మిలియన్ అభ్యర్థనలను నిర్వహించే సేవలను అమలు చేశారు.",  # 2M req/day
        ],
    ),
    _c(
        "cand_imran", "Imran Shaikh",
        "Backend Engineer", "Mumbai", "hi", 7,
        ["Go", "gRPC", "Kubernetes", "GCP", "Postgres"],
        [
            "मुंबई में रहने वाला बैकएंड इंजीनियर, 7 साल का अनुभव।",  # Mumbai, 7 yrs
            "Go और gRPC का उपयोग करके सेवाएँ बनाईं।",  # built services in Go + gRPC
            "GCP पर Kubernetes क्लस्टर चलाए।",  # ran k8s on GCP
            "Postgres पर लेन-देन प्रणाली डिज़ाइन की।",  # designed txn system on Postgres
        ],
    ),
    _c(
        "cand_neha", "Neha Joshi",
        "Full-stack Engineer", "Pune", "en", 4,
        ["Node.js", "React", "MongoDB", "TypeScript"],
        [
            "Full-stack engineer in Pune, 4 years of experience.",
            "Built React frontends and Node.js backends for D2C brands.",
            "Used MongoDB and TypeScript across the stack.",
            # Note: claims 10 years of Kubernetes elsewhere but resume never mentions it.
            "Comfortable shipping features end to end on tight timelines.",
        ],
    ),
    _c(
        "cand_vikram", "Vikram Nair",
        "Staff Backend Engineer", "Bangalore", "en", 11,
        ["Go", "Rust", "Kubernetes", "AWS", "distributed-systems", "payments"],
        [
            "Staff Backend Engineer in Bangalore with 11 years of experience.",
            "Designed distributed payment ledgers in Go and Rust.",
            "Ran multi-region Kubernetes on AWS for a fintech unicorn.",
            "Owned reliability for a system processing 50k payments per second.",
        ],
    ),
]


_FIRST = ["Aditya", "Sneha", "Karan", "Priya", "Rahul", "Ananya", "Sanjay", "Meera",
          "Nikhil", "Divya", "Tarun", "Pooja", "Aman", "Ritu", "Vivek", "Kavya"]
_LAST = ["Patil", "Sharma", "Iyer", "Gupta", "Rao", "Mehta", "Kumar", "Bose",
         "Chauhan", "Naidu", "Saxena", "Pillai"]
_LOC = ["Pune", "Pune", "Pune", "Mumbai", "Bangalore", "Remote", "Hyderabad"]
_LANG = ["en", "en", "en", "hi", "mr", "te"]
_STACKS = [
    (["Python", "Django", "PostgreSQL", "REST"], "Backend Engineer"),
    (["Go", "gRPC", "Kubernetes", "AWS"], "Backend Engineer"),
    (["Java", "Spring", "Kafka", "MySQL"], "Backend Engineer"),
    (["Node.js", "Express", "MongoDB", "Redis"], "Backend Engineer"),
]


def _procedural(rng: random.Random, idx: int) -> Candidate:
    first = rng.choice(_FIRST)
    last = rng.choice(_LAST)
    loc = rng.choice(_LOC)
    lang = rng.choice(_LANG)
    skills, title = rng.choice(_STACKS)
    years = rng.choice([3, 4, 5, 6, 7, 8, 9])
    s = ", ".join(skills[:3])
    lines = [
        f"{title} based in {loc} with {years} years of experience.",
        f"Worked primarily with {s}.",
        f"Built and operated backend services using {skills[0]}.",
        f"Familiar with {skills[-1]} in production.",
    ]
    return _c(f"cand_p{idx}", f"{first} {last}", title, loc, lang, years, skills, lines)


def build_candidates(seed: int = 7, n_extra: int = 26) -> list[Candidate]:
    rng = random.Random(seed)
    pool = list(HERO_CANDIDATES)
    for i in range(n_extra):
        pool.append(_procedural(rng, i))
    return pool


def build_jobs() -> list[Job]:
    return [
        Job(
            id="job_be_pune",
            title="Backend Engineer",
            location="Pune",
            headcount=2,
            must_have=["Python", "Kubernetes"],
            nice_to_have=["Go", "payments", "PostgreSQL"],
            seniority="senior",
            pool="talent",
        )
    ]


# ---- sales prospects: same shape as candidates, different pool ----


def _p(
    pid: str, contact: str, headline: str, location: str, language: str,
    signals: list[str], lines: list[str],
) -> Candidate:
    return Candidate(
        id=pid, name=contact, headline=headline, location=location, language=Language(language),
        years_experience=0, skills=signals, pool="prospects",
        resume=[ResumeLine(n=i + 1, text=t) for i, t in enumerate(lines)],
    )


HERO_PROSPECTS: list[Candidate] = [
    _p("pr_rapidpay", "Priya Sharma", "VP Engineering, RapidPay", "Bengaluru", "en",
       ["fintech", "payments", "AWS", "hiring", "Series B"],
       [
           "RapidPay is a fintech company headquartered in Bengaluru.",
           "Series B funded with about 140 employees.",
           "Runs payments and settlement infrastructure on AWS.",
           "Currently hiring backend and platform engineers.",
       ]),
    _p("pr_shopnest", "Karan Mehta", "CTO, ShopNest", "Pune", "mr",
       ["ecommerce", "SaaS", "GCP", "hiring", "Series A"],
       [
           "ShopNest ही पुण्यातील एक ecommerce SaaS कंपनी आहे.",  # ecommerce SaaS in Pune
           "Series A funded, सुमारे 60 कर्मचारी.",  # Series A, ~60 staff
           "त्यांचे प्लॅटफॉर्म GCP वर चालते.",  # platform runs on GCP
           "सध्या engineering team साठी hiring सुरू आहे.",  # hiring for engineering
       ]),
    _p("pr_medint", "Lakshmi Rao", "Head of Tech, MedIntel", "Hyderabad", "te",
       ["healthtech", "AI", "AWS", "Series B"],
       [
           "MedIntel ఒక healthtech కంపెనీ, హైదరాబాద్‌లో ఉంది.",  # healthtech in Hyderabad
           "AI ఆధారిత డయాగ్నొస్టిక్స్‌ను నిర్మిస్తోంది.",  # builds AI diagnostics
           "AWS క్లౌడ్‌లో deploy చేస్తారు.",  # deploys on AWS
           "Series B దశలో ఉంది.",  # Series B
       ]),
    _p("pr_logix", "Aditya Nair", "Founder, Logix", "Mumbai", "hi",
       ["logistics", "SaaS", "Azure", "Series A", "hiring"],
       [
           "Logix मुंबई की एक logistics SaaS कंपनी है।",  # logistics SaaS Mumbai
           "Series A में funded, लगभग 45 लोग।",  # Series A, ~45
           "इनका stack Azure पर चलता है।",  # runs on Azure
           "अभी backend engineers के लिए hiring कर रहे हैं।",  # hiring backend
       ]),
    _p("pr_finflow", "Sneha Iyer", "Director Engineering, FinFlow", "Bengaluru", "en",
       ["fintech", "lending", "AWS", "payments", "Series C"],
       [
           "FinFlow is a Series C fintech in Bengaluru focused on lending.",
           "Processes digital payments at scale on AWS.",
           "Around 300 employees across India.",
       ]),
]

_COMPANIES = ["NovaTech", "Brightly", "Quanta", "Zeppl", "Kettle", "Orbit", "Stacker", "Mintly"]
_DOMAINS = [
    (["fintech", "payments", "AWS"], "fintech"),
    (["SaaS", "B2B", "GCP"], "B2B SaaS"),
    (["ecommerce", "retail", "AWS"], "ecommerce"),
    (["healthtech", "AI", "Azure"], "healthtech"),
]
_STAGES = ["Series A", "Series B", "Series C", "bootstrapped"]


def _procedural_prospect(rng: random.Random, idx: int) -> Candidate:
    contact = f"{rng.choice(_FIRST)} {rng.choice(_LAST)}"
    company = rng.choice(_COMPANIES) + rng.choice(["", " Labs", " AI", "Pay"])
    signals, domain = rng.choice(_DOMAINS)
    stage = rng.choice(_STAGES)
    loc = rng.choice(_LOC)
    lang = rng.choice(_LANG)
    hiring = rng.random() < 0.5
    sig = list(signals) + [stage] + (["hiring"] if hiring else [])
    lines = [
        f"{company} is a {domain} company based in {loc}.",
        f"{stage} stage, primarily on {signals[-1]}.",
        f"Works in {domain} with a focus on {signals[0]}.",
    ]
    if hiring:
        lines.append("Currently hiring engineers.")
    return _p(f"pr_g{idx}", contact, f"Engineering lead, {company}", loc, lang, sig, lines)


def build_prospects(seed: int = 11, n_extra: int = 18) -> list[Candidate]:
    rng = random.Random(seed)
    pool = list(HERO_PROSPECTS)
    for i in range(n_extra):
        pool.append(_procedural_prospect(rng, i))
    return pool


def build_campaigns() -> list[Job]:
    return [
        Job(
            id="icp_fintech", title="Fintech engineering leaders", location="Bengaluru",
            headcount=2, must_have=["fintech", "hiring"], nice_to_have=["AWS", "payments", "Series B"],
            seniority="decision-maker", pool="prospects",
        )
    ]


def dump() -> None:
    cands = build_candidates()
    jobs = build_jobs()
    (DATA_DIR / "candidates.json").write_text(
        json.dumps([c.model_dump() for c in cands], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (DATA_DIR / "jobs.json").write_text(
        json.dumps([j.model_dump() for j in jobs], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"wrote {len(cands)} candidates, {len(jobs)} jobs to {DATA_DIR}")


if __name__ == "__main__":
    dump()
