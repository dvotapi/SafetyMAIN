from __future__ import annotations

from enum import Enum


class HazardStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class RiskStatus(str, Enum):
    DRAFT = "draft"
    ASSESSED = "assessed"
    ACCEPTED = "accepted"
    MONITORING = "monitoring"
    ARCHIVED = "archived"


class RiskAssessmentStatus(str, Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class AssessedObjectType(str, Enum):
    WORKPLACE = "workplace"
    JOB_POSITION = "job_position"
    WORK_ACTIVITY = "work_activity"
    EQUIPMENT = "equipment"
    VEHICLE = "vehicle"
    PRODUCTION_PROCESS = "production_process"
    LOCATION = "location"
    CONTRACTOR_ACTIVITY = "contractor_activity"
    CHEMICAL = "chemical"
    EMERGENCY_SCENARIO = "emergency_scenario"


class AssessmentProfileCode(str, Enum):
    SIMPLE_3X3 = "simple_3x3"
    SIMPLE_5X5 = "simple_5x5"
    CORPORATE_CUSTOM = "corporate_custom"
    RUSSIAN_OCCUPATIONAL_RISK = "russian_occupational_risk"
    INDUSTRIAL_SAFETY = "industrial_safety"
    FIRE_SAFETY = "fire_safety"
    ENVIRONMENTAL_RISK = "environmental_risk"
    TRANSPORT_RISK = "transport_risk"
    ADR_RISK = "adr_risk"


class RiskFactorCode(str, Enum):
    PROBABILITY = "probability"
    SEVERITY = "severity"
    EXPOSURE = "exposure"
    FREQUENCY = "frequency"
    DETECTABILITY = "detectability"
    ENVIRONMENTAL_IMPACT = "environmental_impact"
    FIRE_CONSEQUENCE = "fire_consequence"
    BUSINESS_IMPACT = "business_impact"


class RiskAcceptanceDecision(str, Enum):
    ACCEPTED = "accepted"
    CONDITIONALLY_ACCEPTED = "conditionally_accepted"
    NOT_ACCEPTED = "not_accepted"
    REQUIRES_ESCALATION = "requires_escalation"


class ReviewTrigger(str, Enum):
    INCIDENT = "incident"
    PROCESS_CHANGE = "process_change"
    LEGISLATION_CHANGE = "legislation_change"
    EQUIPMENT_REPLACEMENT = "equipment_replacement"
    PERIODIC_REVIEW = "periodic_review"
    OTHER = "other"


class CompetencyReferenceCode(str, Enum):
    WORKING_AT_HEIGHT = "working_at_height"
    LOTO = "loto"
    CONFINED_SPACE = "confined_space"
    ADR_DRIVER = "adr_driver"
    FIRE_SAFETY = "fire_safety"
    ELECTRICAL_SAFETY = "electrical_safety"
    INDUSTRIAL_SAFETY = "industrial_safety"
    OTHER = "other"


class InspectionStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class IncidentStatus(str, Enum):
    REPORTED = "reported"
    UNDER_INVESTIGATION = "under_investigation"
    ACTIONS_PENDING = "actions_pending"
    CLOSED = "closed"
    ARCHIVED = "archived"


class CorrectiveActionStatus(str, Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VERIFIED = "verified"
    CLOSED = "closed"


class TrainingStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class PermitStatus(str, Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    SUSPENDED = "suspended"
    CLOSED = "closed"
    ARCHIVED = "archived"


class EmergencyPlanStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    UNDER_REVIEW = "under_review"
    ARCHIVED = "archived"


class AssetStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DECOMMISSIONED = "decommissioned"


class Probability(str, Enum):
    RARE = "rare"
    UNLIKELY = "unlikely"
    POSSIBLE = "possible"
    LIKELY = "likely"
    ALMOST_CERTAIN = "almost_certain"


class Severity(str, Enum):
    INSIGNIFICANT = "insignificant"
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CATASTROPHIC = "catastrophic"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class ControlType(str, Enum):
    """Hierarchy of Controls, ordered from most to least preferred."""

    ELIMINATION = "elimination"
    SUBSTITUTION = "substitution"
    ENGINEERING = "engineering"
    ADMINISTRATIVE = "administrative"
    PPE = "ppe"

    @property
    def hierarchy_rank(self) -> int:
        """Lower rank is preferred (Elimination = 1)."""

        return {
            ControlType.ELIMINATION: 1,
            ControlType.SUBSTITUTION: 2,
            ControlType.ENGINEERING: 3,
            ControlType.ADMINISTRATIVE: 4,
            ControlType.PPE: 5,
        }[self]


class ControlNature(str, Enum):
    PREVENTIVE = "preventive"
    DETECTIVE = "detective"
    MITIGATING = "mitigating"
    RECOVERY = "recovery"


class RiskControlStatus(str, Enum):
    DRAFT = "draft"
    PLANNED = "planned"
    IN_IMPLEMENTATION = "in_implementation"
    IMPLEMENTED = "implemented"
    VERIFIED_EFFECTIVE = "verified_effective"
    VERIFIED_INEFFECTIVE = "verified_ineffective"
    SUSPENDED = "suspended"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"
    CANCELLED = "cancelled"


class RiskControlSourceType(str, Enum):
    RISK_ASSESSMENT = "risk_assessment"
    REGULATORY_REQUIREMENT = "regulatory_requirement"
    CORPORATE_STANDARD = "corporate_standard"
    INCIDENT = "incident"
    INSPECTION = "inspection"
    CORRECTIVE_ACTION = "corrective_action"
    MANAGEMENT_DECISION = "management_decision"
    OTHER = "other"


class ControlOwnerType(str, Enum):
    USER = "user"
    EMPLOYEE = "employee"
    ROLE = "role"
    ORGANIZATIONAL_UNIT = "organizational_unit"
    EXTERNAL_PARTY = "external_party"


class ControlScopeType(str, Enum):
    ORGANIZATION = "organization"
    BUSINESS_UNIT = "business_unit"
    DEPARTMENT = "department"
    WORKPLACE = "workplace"
    WORK_ACTIVITY = "work_activity"
    PROCESS = "process"
    ASSET = "asset"
    EQUIPMENT = "equipment"
    LOCATION = "location"
    ROLE = "role"
    JOB_POSITION = "job_position"
    HAZARD = "hazard"
    RISK_ASSESSMENT = "risk_assessment"


class MilestoneStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class EvidenceType(str, Enum):
    DOCUMENT = "document"
    PHOTO = "photo"
    VIDEO = "video"
    INSPECTION_RECORD = "inspection_record"
    TEST_RESULT = "test_result"
    WORK_ORDER = "work_order"
    TRAINING_RECORD = "training_record"
    CERTIFICATE = "certificate"
    MEASUREMENT = "measurement"
    APPROVAL = "approval"
    OTHER = "other"


class VerificationType(str, Enum):
    INITIAL = "initial"
    SCHEDULED_REVIEW = "scheduled_review"
    POST_INCIDENT = "post_incident"
    POST_INSPECTION = "post_inspection"
    POST_CHANGE = "post_change"
    MANAGEMENT_REVIEW = "management_review"
    OTHER = "other"


class EffectivenessResult(str, Enum):
    EFFECTIVE = "effective"
    PARTIALLY_EFFECTIVE = "partially_effective"
    INEFFECTIVE = "ineffective"
    NOT_VERIFIED = "not_verified"
    NOT_APPLICABLE = "not_applicable"


class ReviewBasis(str, Enum):
    FIXED_INTERVAL = "fixed_interval"
    RISK_BASED = "risk_based"
    REGULATORY_REQUIREMENT = "regulatory_requirement"
    MANUFACTURER_REQUIREMENT = "manufacturer_requirement"
    CORPORATE_POLICY = "corporate_policy"
    POST_INCIDENT = "post_incident"
    POST_CHANGE = "post_change"
    MANUAL = "manual"


class ControlCompetencyRequirementType(str, Enum):
    OPERATOR = "operator_competency"
    MAINTAINER = "maintainer_competency"
    SUPERVISOR = "supervisor_competency"
    VERIFIER = "verifier_competency"
    EMERGENCY_RESPONSE = "emergency_response_competency"
    OTHER = "other"


class ControlRelatedEntityType(str, Enum):
    HAZARD = "hazard"
    RISK_ASSESSMENT = "risk_assessment"
    INSPECTION = "inspection"
    FINDING = "finding"
    INCIDENT = "incident"
    CORRECTIVE_ACTION = "corrective_action"
    TRAINING = "training"
    PERMIT = "permit"
    ASSET = "asset"
    INSTRUCTION = "instruction"
    KNOWLEDGE_OBJECT = "knowledge_object"
    REQUIREMENT = "requirement"
    WORK_ORDER = "work_order"


class FindingSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HazardCategory(str, Enum):
    PHYSICAL = "physical"
    MECHANICAL = "mechanical"
    ELECTRICAL = "electrical"
    CHEMICAL = "chemical"
    BIOLOGICAL = "biological"
    ERGONOMIC = "ergonomic"
    PSYCHOSOCIAL = "psychosocial"
    FIRE_AND_EXPLOSION = "fire_and_explosion"
    THERMAL = "thermal"
    RADIATION = "radiation"
    PRESSURE = "pressure"
    WORK_AT_HEIGHT = "work_at_height"
    CONFINED_SPACE = "confined_space"
    TRANSPORT = "transport"
    ENVIRONMENTAL = "environmental"
    DANGEROUS_GOODS = "dangerous_goods"
    PROCESS_SAFETY = "process_safety"
    NATURAL_HAZARD = "natural_hazard"
    ORGANIZATIONAL = "organizational"
    OTHER = "other"


class SafetyDirection(str, Enum):
    """Business safety area classification (not a legal conclusion)."""

    OCCUPATIONAL_SAFETY = "occupational_safety"
    INDUSTRIAL_SAFETY = "industrial_safety"
    FIRE_SAFETY = "fire_safety"
    ENVIRONMENTAL_SAFETY = "environmental_safety"
    TRANSPORT_SAFETY = "transport_safety"
    DANGEROUS_GOODS_TRANSPORT = "dangerous_goods_transport"
    CIVIL_DEFENSE_AND_EMERGENCY = "civil_defense_and_emergency"
    SANITARY_AND_HYGIENIC_SAFETY = "sanitary_and_hygienic_safety"
    ELECTRICAL_SAFETY = "electrical_safety"
    RADIATION_SAFETY = "radiation_safety"


class HazardSource(str, Enum):
    EMPLOYEE_REPORT = "employee_report"
    INSPECTION = "inspection"
    INCIDENT_INVESTIGATION = "incident_investigation"
    NEAR_MISS = "near_miss"
    RISK_ASSESSMENT = "risk_assessment"
    REGULATORY_ASSESSMENT = "regulatory_assessment"
    AUDIT = "audit"
    MANAGEMENT_REVIEW = "management_review"
    CHANGE_MANAGEMENT = "change_management"
    EQUIPMENT_DOCUMENTATION = "equipment_documentation"
    SOUT = "sout"
    PRODUCTION_CONTROL = "production_control"
    ENVIRONMENTAL_MONITORING = "environmental_monitoring"
    TRANSPORT_CONTROL = "transport_control"
    OTHER = "other"


class AffectedSubject(str, Enum):
    EMPLOYEE = "employee"
    CONTRACTOR = "contractor"
    VISITOR = "visitor"
    DRIVER = "driver"
    PASSENGER = "passenger"
    PUBLIC = "public"
    ENVIRONMENT = "environment"
    EQUIPMENT = "equipment"
    BUILDING = "building"
    TRANSPORT_VEHICLE = "transport_vehicle"
    CARGO = "cargo"
    PRODUCTION_PROCESS = "production_process"


class EmergencyLevel(str, Enum):
    LOCAL = "local"
    SITE = "site"
    MAJOR = "major"


class PPECategory(str, Enum):
    HEAD = "head"
    EYE = "eye"
    HEARING = "hearing"
    RESPIRATORY = "respiratory"
    HAND = "hand"
    FOOT = "foot"
    BODY = "body"
    FALL = "fall"
    OTHER = "other"


class ChemicalClassification(str, Enum):
    FLAMMABLE = "flammable"
    TOXIC = "toxic"
    CORROSIVE = "corrosive"
    REACTIVE = "reactive"
    ENVIRONMENTAL = "environmental"
    OTHER = "other"
