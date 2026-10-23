"""Generate the deterministic seed: one fictitious agency, 24 call scenarios, three prompt versions.

v14   = production calls (8 of 24 have a defect)
v15   = candidate prompt: disclosures in the opening, a stricter read-back and intake checklist. It fixes
        7 of the 8 defects but reads one monthly premium as annual (a regression the gate must catch)
        and still gives plan advice on one Medicare call
v15.1 = v15 plus a read-back fix and a plan-advice guardrail

Run: uv run python scripts/make_seed.py
"""

from __future__ import annotations

import json
from pathlib import Path

AGENCY = "Larkspur Insurance Group"
OUT = Path(__file__).resolve().parent.parent / "data" / "calls.json"
VERSIONS = ["v14", "v15", "v15.1"]

TPMO = ("Before we go on, we do not offer every plan available in your area. Currently we represent "
        "6 organizations which offer 41 products in your area. Please contact Medicare.gov, 1-800-MEDICARE, "
        "or your local State Health Insurance Program to get information on all of your options.")


class Conv:
    def __init__(self) -> None:
        self.turns: list[dict] = []
        self.t = 0.4

    def say(self, speaker: str, text: str) -> Conv:
        self.turns.append({"speaker": speaker, "t": round(self.t, 1), "text": text})
        self.t += len(text.split()) / 2.6 + 0.7
        return self

    def a(self, text: str) -> Conv:
        return self.say("agent", text)

    def c(self, text: str) -> Conv:
        return self.say("caller", text)

    def tool(self, name: str, **args) -> Conv:
        self.turns.append({"speaker": "tool", "t": round(self.t, 1), "text": "", "tool": name, "args": args})
        self.t += 0.8
        return self

    @property
    def duration(self) -> float:
        return round(self.t + 2.0, 1)


def opening(good: bool, purpose: str) -> str:
    if good:
        return (f"Hi, this is the virtual assistant for {AGENCY}, and this call is recorded for quality. "
                f"{purpose}")
    return f"Hi, thanks for calling {AGENCY}. {purpose}"


# ---------------------------------------------------------------- quote_bundle
QUOTES = {
    "Q01": ("Priya Natarajan", "Northfield Mutual", 1416, "Cedar Ridge", 1512, "Bayline Casualty", "2 vehicles"),
    "Q02": ("Marcus Bell", "Cedar Ridge", 1890, "Granite Shore", 1974, "Northfield Mutual", "3 vehicles"),
    "Q03": ("Elena Ruiz", "Granite Shore", 1248, "Northfield Mutual", 1332, "Lakemont", "1 vehicle"),
    "Q04": ("Tom Okafor", "Keystone Harbor", 2052, "Cedar Ridge", 2160, "Bayline Casualty", "2 vehicles"),
    "Q05": ("Grace Lindqvist", "Northfield Mutual", 1584, "Granite Shore", 1650, "Lakemont", "2 vehicles"),
    "Q06": ("Owen Castellanos", "Cedar Ridge", 1320, "Keystone Harbor", 1404, "Northfield Mutual", "1 vehicle"),
}


def quote_call(sid: str, version: str) -> dict:
    name, c1, p1, c2, p2, prior, vehicles = QUOTES[sid]
    first = name.split()[0]
    m1 = round(p1 / 12)
    spoken1 = f"${p1:,} a year, or ${m1} a month"
    if sid == "Q01" and version == "v15":
        spoken1 = f"${m1} a year, billed monthly"  # regression: monthly figure read as annual
    if sid == "Q03" and version == "v14":
        spoken1 = f"$1,284 a year, or ${m1} a month"  # digit swap: rater says 1,248
    cv = Conv()
    cv.a(opening(True, f"You asked for an auto and home quote, {first}. Is now still a good time?"))
    cv.c(f"Yes. It's {vehicles} and the house on Alder Street. We're with {prior}, renewing on the 14th.")
    cv.a("Thanks. With your OK I'll pull your current declarations so we compare like for like.")
    cv.c("Go ahead.")
    cv.tool("pull_dec_page", carrier=prior)
    cv.tool("rate_bundle", carriers=[c1, c2])
    cv.a(f"I have two options at the same limits, 100/300/100 with a $500 deductible. {c1} came back at "
         f"{spoken1}. {c2} is ${p2:,} a year.")
    if sid == "Q05" and version == "v14":
        cv.a("Summit Plains is usually a little cheaper too, and good news, you're covered starting today.")
    cv.c("The first one sounds good. What happens next?")
    cv.a("A licensed producer will review the quote with you and finalize it. I've booked you for Tuesday "
         "at 2:30.")
    cv.tool("book_producer", slot="Tue 14:30")
    intake = {"vehicles": int(vehicles.split()[0]), "address": "Alder Street", "prior_carrier": prior,
              "renewal_date": "the 14th"}
    record = {"source": "rated quote", "carriers": [c1, c2], "prior_carrier": prior, "amounts": [
        {"label": f"{c1} annual premium", "value": p1, "period": "year"},
        {"label": f"{c1} monthly premium", "value": m1, "period": "month"},
        {"label": f"{c2} annual premium", "value": p2, "period": "year"},
        {"label": "deductible", "value": 500, "period": None},
    ]}
    return dict(workflow="quote_bundle", line="pc", title=f"Auto + home quote, {vehicles}", caller=name,
                cv=cv, intake=intake, record=record)


# ---------------------------------------------------------------- vehicle_add
VEHICLES = {
    "V01": ("Hannah Brooks", "2024 Toyota RAV4", "JTMB1RFV4RD034471", "Pinecrest Credit Union", "AU-40213", 742, 801),
    "V02": ("Diego Alvarez", "2023 Honda CR-V", "7FARS4H51PE017325", "Meridian Auto Finance", "AU-40877", 655, 712),
    "V03": ("Leah Kim", "2025 Subaru Outback", "4S4BTGLD1S3109842", "Pinecrest Credit Union", "AU-41102", 810, 868),
    "V04": ("Ravi Menon", "2024 Ford Maverick", "3FTTW8F9XRR106298", "Riverstone Bank", "AU-41540", 598, 664),
    "V05": ("Nora Feld", "2022 Mazda CX-5", "JM3KFBCM2N0581163", "Meridian Auto Finance", "AU-42019", 702, 745),
    "V06": ("Caleb Wright", "2025 Kia Telluride", "5XYP5DGC8SG220917", "Riverstone Bank", "AU-42288", 911, 988),
}
LIEN_ADDR = {"Pinecrest Credit Union": "PO Box 118, Fresno CA", "Meridian Auto Finance": "PO Box 7700, Dallas TX",
             "Riverstone Bank": "PO Box 902, Tampa FL"}


def vehicle_call(sid: str, version: str) -> dict:
    name, car, vin, lender, pol, old, new = VEHICLES[sid]
    first = name.split()[0]
    last4 = vin[-4:]
    spoken_last4 = " ".join(last4)
    if sid == "V04" and version == "v14":
        spoken_last4 = "6 2 8 9"  # caller said 6289; the agent wrote 6298 into the intake
    ask_addr = not (sid == "V02" and version == "v14")
    cv = Conv()
    cv.a(opening(True, "How can I help today?"))
    cv.c(f"Hi, it's {name}. We just bought a car and need it on our policy.")
    cv.a("Congratulations. Can you confirm your date of birth and the ZIP code on the policy?")
    cv.c("March 3rd, 1988, and 93711.")
    cv.tool("identity_verified", method="dob+zip")
    cv.a(f"Thanks {first}, you're verified and I have policy {pol} open. What's the vehicle, the VIN, "
         "who will mainly drive it, and is there a lender?")
    cv.c(f"It's a {car}, VIN ending {spoken_last4}. Mostly me, and the loan is with {lender}.")
    if ask_addr:
        cv.a(f"Got it. The carrier needs the lienholder's mailing address for {lender}. Do you have it?")
        cv.c(f"It's {LIEN_ADDR[lender]}.")
    cv.tool("submit_endorsement", policy=pol, vin=vin)
    cv.a(f"Done. The vehicle add is submitted. Your six-month premium goes from ${old} to ${new} per six "
         "months, and your new ID card will come by email and text.")
    cv.c("Perfect, thank you.")
    intake = {"vin": vin, "vehicle": car, "primary_driver": name, "lienholder": lender,
              "lienholder_address": LIEN_ADDR[lender] if ask_addr else ""}
    record = {"source": "auto policy record", "carriers": ["Northfield Mutual"], "amounts": [
        {"label": "current six-month premium", "value": old, "period": "six_months"},
        {"label": "six-month premium after the change", "value": new, "period": "six_months"},
    ]}
    return dict(workflow="vehicle_add", line="pc", title=f"Add vehicle, {car}", caller=name, cv=cv,
                intake=intake, record=record)


# ---------------------------------------------------------------- mortgagee_change
MORTGAGES = {
    "M01": ("Ian Doyle", "HO-7731-02", "Crescent Home Loans", "30-71245", 2184),
    "M02": ("Fatima Shah", "HO-7804-01", "Bluegate Mortgage", "52-11980", 1968),
    "M03": ("Ben Carter", "HO-7912-03", "Crescent Home Loans", "30-88410", 2412),
    "M04": ("Julia Moreno", "HO-8020-01", "Westbrook Savings", "77-30215", 1752),
    "M05": ("Arjun Pillai", "HO-8133-02", "Bluegate Mortgage", "52-40677", 2256),
    "M06": ("Claire Dubois", "HO-8207-01", "Westbrook Savings", "77-51893", 1896),
}


def mortgage_call(sid: str, version: str) -> dict:
    name, pol, lender, loan, prem = MORTGAGES[sid]
    good_open = not (sid == "M05" and version == "v14")
    write_first = sid == "M03" and version == "v14"
    cv = Conv()
    cv.a(opening(good_open, "What can I do for you?"))
    cv.c(f"I refinanced last week. The new mortgage company has to be on my homeowners policy, {pol}.")
    if write_first:
        cv.a("I can take care of that now. What's the lender's name and the loan number?")
        cv.c(f"{lender}. The loan number is {loan}.")
        cv.tool("update_mortgagee", policy=pol, lender=lender, loan=loan)
        cv.a("And just to confirm, what's your date of birth?")
        cv.c("July 19th, 1979.")
        cv.tool("identity_verified", method="dob")
    else:
        cv.a("I can take care of that. First, can you confirm your date of birth and the property address?")
        cv.c("July 19th, 1979, and 48 Quarry Lane.")
        cv.tool("identity_verified", method="dob+address")
        cv.a("Thanks, you're verified. What's the lender's name and the loan number?")
        cv.c(f"{lender}. The loan number is {loan}.")
        cv.tool("update_mortgagee", policy=pol, lender=lender, loan=loan)
    cv.a(f"All set. {lender} is now the mortgagee, your premium stays ${prem:,} a year, and the lender "
         "notice goes out today.")
    cv.c("Great, thanks.")
    intake = {"policy_id": pol, "lender": lender, "loan_number": loan}
    record = {"source": "homeowners policy record", "carriers": ["Cedar Ridge"], "amounts": [
        {"label": "annual premium", "value": prem, "period": "year"},
    ]}
    return dict(workflow="mortgagee_change", line="pc", title=f"Mortgagee change, {lender}", caller=name, cv=cv,
                intake=intake, record=record)


# ---------------------------------------------------------------- medicare_fronter
MEDICARE = {
    "F01": ("Walter Hughes", "33612", "a Part C plan through his former employer"),
    "F02": ("Rosa Delgado", "85032", "Original Medicare with a supplement"),
    "F03": ("Gene Park", "78745", "a Medicare Advantage HMO"),
    "F04": ("Lorraine Fitch", "32207", "a Medicare Advantage PPO"),
    "F05": ("Henry Osei", "30316", "Original Medicare only"),
    "F06": ("Margaret Quinn", "60629", "a Part D plan and Original Medicare"),
}


def medicare_call(sid: str, version: str) -> dict:
    name, zipc, plan = MEDICARE[sid]
    first = name.split()[0]
    v14 = version == "v14"
    late = sid == "F02" and v14
    missing = sid == "F04" and v14
    advice = sid == "F04" and version in ("v14", "v15")
    cv = Conv()
    cv.a(opening(True, f"I'm following up on your request about Medicare plans, {first}. Is now a good time?"))
    cv.c("Yes, I have a few minutes.")
    if not late and not missing:
        cv.a(TPMO)
        cv.c("Okay.")
    cv.a("What ZIP code do you live in?")
    cv.c(f"It's {' '.join(zipc)}.")
    cv.a("And what coverage do you have today?")
    cv.c(f"I have {plan}. My drug costs went up a lot this year and I want to know if there's something better.")
    if late:
        cv.a("I understand. A lot of people saw higher drug costs this year. Are any of your doctors ones "
             "you'd want to keep no matter what plan you end up on?")
        cv.c("Yes, Dr. Albers at the county clinic, I've seen her for twelve years and I wouldn't switch.")
        cv.a("That's helpful. Do you take any brand-name prescriptions, and do you use a mail-order pharmacy "
             "or a local one?")
        cv.c("Two brand-name ones, for blood pressure and cholesterol, and I use the pharmacy on Fifth Street.")
        cv.a(TPMO)
        cv.c("Okay.")
    if advice:
        cv.a("Honestly, I'd recommend the plan with the lowest drug copays, it's usually the best plan for you.")
        cv.c("Okay, that sounds good.")
    cv.a("A licensed agent can go through the plans available in your ZIP and compare them for you. "
         "May I connect you now?")
    cv.c("Yes, please.")
    cv.tool("warm_transfer", to="licensed agent")
    intake = {"zip": zipc, "current_plan": plan, "transfer_consent": True}
    record = {"source": "lead record", "carriers": [], "amounts": []}
    return dict(workflow="medicare_fronter", line="medicare", title="Medicare intake, warm transfer",
                caller=name, cv=cv, intake=intake, record=record)


BUILDERS = [(QUOTES, quote_call), (VEHICLES, vehicle_call), (MORTGAGES, mortgage_call), (MEDICARE, medicare_call)]


def build() -> dict:
    calls = []
    for version in VERSIONS:
        for table, fn in BUILDERS:
            for sid in table:
                spec = fn(sid, version)
                cv: Conv = spec.pop("cv")
                calls.append({"id": f"{sid}-{version}", "scenario": sid, "version": version,
                              "duration": cv.duration, "turns": cv.turns, **spec})
    return {
        "agency": AGENCY,
        "baseline": "v14",
        "notes": {
            "v14": "Production prompt. 24 calls from one week at a fictitious agency.",
            "v15": "Candidate: disclosures in the opening, stricter read-back and intake checklist.",
            "v15.1": "Candidate: v15 plus a billing-period read-back fix and a plan-advice guardrail.",
        },
        "calls": calls,
    }


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(build(), indent=1) + "\n")
    print(f"wrote {OUT}")
