from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

app = FastAPI(
    title="BhoomiSetu API",
    description="Multi-Agent Legal Tech Backend for Indian Property & Contract Law",
    version="0.1.0"
)

# CORS — allow any frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ───────────────────────────────
# ENUMS & SHARED MODELS
# ───────────────────────────────

class PartyRole(str, Enum):
    BUYER = "buyer"
    TENANT = "tenant"
    SELLER = "seller"
    LANDLORD = "landlord"

class DocumentType(str, Enum):
    RENT_AGREEMENT = "Rent Agreement"
    SALE_DEED = "Sale Deed"
    GIFT_DEED = "Gift Deed"
    LEAVE_LICENSE = "Leave & License"

class Language(str, Enum):
    ENGLISH = "English"
    HINDI = "Hindi"
    PUNJABI = "Punjabi"
    KANNADA = "Kannada"
    MARATHI = "Marathi"

class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

class EligibilityStatus(str, Enum):
    PERMITTED = "PERMITTED"
    CONDITIONAL = "CONDITIONAL"
    BLOCKED = "BLOCKED"

# ───────────────────────────────
# REQUEST MODELS
# ───────────────────────────────

class EligibilityRequest(BaseModel):
    buyer_home_state: str
    property_state: str
    property_type: str  # e.g. "Agricultural", "Residential", "Commercial"
    buyer_type: str     # e.g. "Indian Resident", "NRI"
    buyer_gender: str   # e.g. "Male", "Female"
    transaction_type: DocumentType
    property_value: float
    area_category: str  # e.g. "Rural", "Urban", "Mumbai Municipal Corp"
    party_role: PartyRole = PartyRole.BUYER
    language: Language = Language.ENGLISH

class AnalyzeContractRequest(BaseModel):
    contract_text: str
    property_state: str
    document_type: DocumentType
    party_role: PartyRole
    language: Language = Language.ENGLISH

class AnalyzeClauseRequest(BaseModel):
    clause_text: str
    property_state: str
    document_type: DocumentType
    party_role: PartyRole
    language: Language = Language.ENGLISH

class TranslateRequest(BaseModel):
    text: str
    target_language: Language
    party_role: Optional[PartyRole] = None
    context: Optional[str] = None  # e.g. "legal translation" or "plain explanation"

# ───────────────────────────────
# RESPONSE MODELS
# ───────────────────────────────

class RestrictionItem(BaseModel):
    severity: Severity
    law: str
    description: str
    impact_on_user: str
    action_required: str

class EligibilityResponse(BaseModel):
    eligibility: EligibilityStatus
    risk_level: Severity
    restrictions: List[RestrictionItem]
    stamp_duty_estimate: Dict[str, Any]
    required_documents: List[str]
    registration_process: List[str]
    key_advice: List[str]
    disclaimer: str

class RiskyClause(BaseModel):
    clause_number: Optional[int]
    original_text: str
    severity: Severity
    risk: str
    law: str
    party_impact: str
    suggested_replacement: str
    translation: Optional[Dict[str, str]] = None

class MissingClause(BaseModel):
    clause_name: str
    severity: Severity
    reason: str
    suggested_text: Optional[str] = None

class StampDutyVerification(BaseModel):
    stated_in_contract: Optional[str]
    correct_rate: float
    correct_amount: float
    discrepancy: Optional[str]

class AnalyzeContractResponse(BaseModel):
    overall_risk: Severity
    summary: str
    critical_issues: List[str]
    risky_clauses: List[RiskyClause]
    missing_clauses: List[MissingClause]
    cross_state_traps: List[str]
    stamp_duty_verification: StampDutyVerification
    redlined_suggestions: List[Dict[str, str]]
    what_is_done_right: List[str]
    disclaimer: str

class AnalyzeClauseResponse(BaseModel):
    clause_text: str
    severity: Severity
    risk_summary: str
    law_reference: str
    party_impact: str
    suggested_replacement: str
    translation_legal: Optional[str] = None
    translation_plain: Optional[str] = None

class TranslateResponse(BaseModel):
    original_text: str
    legal_translation: str
    plain_explanation: str
    risks_flagged: Optional[str] = None
    your_rights: Optional[str] = None

class PincodeResponse(BaseModel):
    pincode: str
    district: str
    state: str
    taluka: Optional[str] = None
    area_category: str

# ───────────────────────────────
# DUMMY ENDPOINTS
# ───────────────────────────────

@app.post("/api/eligibility", response_model=EligibilityResponse)
async def eligibility_check(req: EligibilityRequest):
    """
    Check if a cross-state property transaction is legally permissible.
    """
    return EligibilityResponse(
        eligibility=EligibilityStatus.CONDITIONAL,
        risk_level=Severity.HIGH,
        restrictions=[
            RestrictionItem(
                severity=Severity.HIGH,
                law="HP Tenancy & Land Reforms Act 1972, Section 118",
                description="Non-agriculturists cannot buy agricultural land without State Govt permission",
                impact_on_user=f"As a {req.party_role.value} from {req.buyer_home_state}, you may face residency-based restrictions.",
                action_required="Apply to the Deputy Commissioner for permission under Section 118 BEFORE signing any agreement"
            )
        ],
        stamp_duty_estimate={
            "stamp_duty_rate": 6.0,
            "stamp_duty_amount": req.property_value * 0.06,
            "registration_fee_rate": 2.0,
            "registration_fee_amount": req.property_value * 0.02,
            "total": req.property_value * 0.08
        },
        required_documents=["Sale deed draft", "Encumbrance Certificate", "Khata Extract", "NOC from Tehsildar"],
        registration_process=[
            "Step 1: Obtain Section 118 permission (if HP agricultural land)",
            "Step 2: Pay stamp duty via e-Stamp or physical stamp paper",
            "Step 3: Book appointment on state registration portal",
            "Step 4: Execute deed before Sub-Registrar with 2 witnesses"
        ],
        key_advice=[
            "Verify seller title for minimum 30 years",
            "Check for any pending litigation on the property",
            "Ensure all dues (property tax, water) are cleared before registration"
        ],
        disclaimer="This analysis is based on laws as of June 2026. Always consult a registered advocate before proceeding."
    )


@app.post("/api/analyze-contract", response_model=AnalyzeContractResponse)
async def analyze_contract(req: AnalyzeContractRequest):
    """
    Analyze a pasted/uploaded contract for risks, missing clauses, cross-state errors, and suggest improvements.
    """
    return AnalyzeContractResponse(
        overall_risk=Severity.HIGH,
        summary=f"This {req.document_type.value} has 2 critical issues and 3 high-risk clauses from the perspective of a {req.party_role.value}.",
        critical_issues=[
            "Wrong state law referenced in jurisdiction clause",
            "Stamp duty amount does not match current rates for the property state"
        ],
        risky_clauses=[
            RiskyClause(
                clause_number=4,
                original_text="This agreement shall be governed by Delhi Rent Control Act 1958",
                severity=Severity.CRITICAL,
                risk="Wrong state law referenced",
                law=f"{req.property_state} Rent Act applies, not Delhi RCA 1958",
                party_impact=f"As the {req.party_role.value}, you have NO legal protection under Delhi RCA in {req.property_state}.",
                suggested_replacement=f"This agreement shall be governed by the {req.property_state} Rent Act",
                translation={"legal": "[Translation placeholder]", "plain": "[Plain explanation placeholder]"}
            ),
            RiskyClause(
                clause_number=7,
                original_text="Security deposit: Rs. 2,50,000 (10 months rent)",
                severity=Severity.HIGH,
                risk="Excessive security deposit",
                law="Model Tenancy Act 2021 caps residential deposits at 2 months rent",
                party_impact=f"As the {req.party_role.value}, you are overpaying by a significant amount. Negotiate to 2 months rent.",
                suggested_replacement="Security deposit shall not exceed two months' rent as per Model Tenancy Act 2021"
            )
        ],
        missing_clauses=[
            MissingClause(
                clause_name="Registration Clause",
                severity=Severity.CRITICAL,
                reason="Unregistered rent agreements beyond 11 months are not admissible as evidence",
                suggested_text="This agreement shall be registered with the Sub-Registrar within 4 months of execution."
            ),
            MissingClause(
                clause_name="Notice Period for Rent Increase",
                severity=Severity.MEDIUM,
                reason="Required under most state rent acts to protect tenant from arbitrary increases"
            )
        ],
        cross_state_traps=[
            f"Contract references Delhi Rent Control Act but property is in {req.property_state}",
            "Stamp duty clause cites Punjab rates instead of property state rates"
        ],
        stamp_duty_verification=StampDutyVerification(
            stated_in_contract="5%",
            correct_rate=6.0,
            correct_amount=450000.0,
            discrepancy="Contract states 5% but correct rate is 6% for this state and category"
        ),
        redlined_suggestions=[
            {
                "original": "The First Party may enter the premises at any time without prior notice",
                "suggested": "The First Party may inspect the premises upon giving not less than 24 hours written notice",
                "reason": "Protects tenant\'s right to quiet enjoyment"
            }
        ],
        what_is_done_right=[
            "Parties are correctly identified with full names and addresses",
            "Property description includes survey number and extent",
            "Witness clause is present with space for 2 witnesses"
        ],
        disclaimer="This analysis is generated by AI and does not constitute legal advice. Consult a registered advocate."
    )


@app.post("/api/analyze-clause", response_model=AnalyzeClauseResponse)
async def analyze_clause(req: AnalyzeClauseRequest):
    """
    Analyze a single clause for risks and suggest party-aware improvements.
    """
    return AnalyzeClauseResponse(
        clause_text=req.clause_text,
        severity=Severity.MEDIUM,
        risk_summary="This clause contains ambiguous language that could be interpreted against your interests.",
        law_reference=f"{req.property_state} Contract Act and relevant state-specific tenancy laws",
        party_impact=f"As the {req.party_role.value}, this clause exposes you to unilateral changes without adequate notice or recourse.",
        suggested_replacement="[Suggested replacement text will be generated based on party role and state law]",
        translation_legal="[Legal translation placeholder]",
        translation_plain="[Plain explanation placeholder]"
    )


@app.post("/api/translate", response_model=TranslateResponse)
async def translate_text(req: TranslateRequest):
    """
    Two-layer translation: legal translation + plain-language explanation.
    """
    return TranslateResponse(
        original_text=req.text,
        legal_translation=f"[Legal translation in {req.target_language.value}] {req.text}",
        plain_explanation=f"[Plain explanation in {req.target_language.value}] This means that...",
        risks_flagged=f"[Risks flagged in {req.target_language.value}]",
        your_rights=f"[Your rights explained in {req.target_language.value}]"
    )


@app.get("/api/stamp-duty")
async def stamp_duty(
    property_state: str,
    area_category: str,
    transaction_type: DocumentType,
    gender: str,
    property_value: float,
    buyer_residency: Optional[str] = "resident"
):
    """
    Calculate stamp duty, registration fees, and cess. Pure calculation — no LLM.
    """
    # Dummy deterministic calculation
    base_rate = 5.0 if gender.lower() == "female" else 6.0
    registration_rate = 1.0 if gender.lower() == "female" else 2.0

    # State-specific adjustments (dummy)
    if property_state.lower() == "maharashtra" and "mumbai" in area_category.lower():
        base_rate += 1.0

    stamp_duty_amount = property_value * (base_rate / 100)
    registration_fee = property_value * (registration_rate / 100)
    cess = property_value * 0.01  # 1% cess dummy
    total = stamp_duty_amount + registration_fee + cess

    return {
        "property_state": property_state,
        "area_category": area_category,
        "transaction_type": transaction_type.value,
        "buyer_gender": gender,
        "buyer_residency": buyer_residency,
        "stamp_duty": {"rate": base_rate, "amount": round(stamp_duty_amount, 2)},
        "registration_fee": {"rate": registration_rate, "amount": round(registration_fee, 2)},
        "cess": {"rate": 1.0, "amount": round(cess, 2)},
        "total": round(total, 2),
        "total_percentage": round((total / property_value) * 100, 2),
        "notes": f"Stamp duty for {property_state} {area_category}. Non-residents may pay additional surcharge in some states."
    }


@app.get("/api/pincode/{pincode}", response_model=PincodeResponse)
async def pincode_lookup(pincode: str):
    """
    Lookup district, state, and area category by pincode.
    """
    # Dummy lookup — in production, query a pincode database
    dummy_db = {
        "110001": {"district": "New Delhi", "state": "Delhi", "taluka": "Connaught Place", "area_category": "Urban"},
        "400001": {"district": "Mumbai", "state": "Maharashtra", "taluka": "Fort", "area_category": "Mumbai Municipal Corp"},
        "560001": {"district": "Bangalore", "state": "Karnataka", "taluka": "Bangalore North", "area_category": "Urban"},
        "160001": {"district": "Chandigarh", "state": "Punjab", "taluka": "Chandigarh", "area_category": "Urban"},
        "171001": {"district": "Shimla", "state": "Himachal Pradesh", "taluka": "Shimla", "area_category": "Urban"},
    }

    data = dummy_db.get(pincode)
    if not data:
        raise HTTPException(status_code=404, detail=f"Pincode {pincode} not found in database")

    return PincodeResponse(
        pincode=pincode,
        district=data["district"],
        state=data["state"],
        taluka=data.get("taluka"),
        area_category=data["area_category"]
    )


# ───────────────────────────────
# HEALTH CHECK
# ───────────────────────────────

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "bhoomisetu-api", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
