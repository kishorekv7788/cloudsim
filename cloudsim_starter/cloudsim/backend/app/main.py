import json
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi import Response

from .engine import network
from .quiz import score_quiz
from .engine.models import Network, Subnet
from .engine import routing, firewall, iam, compute, validator
from .engine import topology

app = FastAPI(title="CloudSim API")
ROOT = Path(__file__).resolve().parents[2]      # repo root
LABS_DIR = ROOT / "labs"
CONTENT_DIR = ROOT / "content"


@app.exception_handler(network.ValidationError)
def on_validation_error(request, exc):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


class CidrPair(BaseModel):
    cidr1: str
    cidr2: str


class SubnetIn(BaseModel):
    name: str
    cidr: str


class NetworkIn(BaseModel):
    name: str
    provider: str
    address_space: str
    subnets: list[SubnetIn] = []


def to_network(n: NetworkIn) -> Network:
    return Network(n.name, n.provider, n.address_space,
                   [Subnet(s.name, s.cidr) for s in n.subnets])


def safe_slug(value: str) -> str:
    """Only letters, digits and dashes: blocks path tricks such as '../..'."""
    if not re.fullmatch(r"[A-Za-z0-9-]+", value):
        raise HTTPException(status_code=400, detail="Invalid name")
    return value.lower()


def read_json(path: Path):
    if not path.exists():
        raise HTTPException(status_code=404, detail="Not found")
    return json.loads(path.read_text())


def load_lab(lab_id: str) -> dict:
    for path in LABS_DIR.glob("*.json"):
        lab = json.loads(path.read_text())
        if lab["id"] == lab_id:
            return lab
    raise HTTPException(status_code=404, detail="Lab not found")


@app.post("/api/sim/network/check-cidr")
def check_cidr(p: CidrPair):
    return {"overlap": network.check_cidr_overlap(p.cidr1, p.cidr2)}


@app.get("/api/labs")
def list_labs():
    keys = ("id", "module", "provider", "title", "difficulty")
    labs = (json.loads(p.read_text()) for p in sorted(LABS_DIR.glob("*.json")))
    return [{k: lab[k] for k in keys} for lab in labs]


@app.post("/api/labs/{lab_id}/validate")
def validate_lab(lab_id: str, topology: NetworkIn):
    lab = load_lab(lab_id)
    net = to_network(topology)
    issues = network.find_issues(net)
    goal = lab["goal_spec"]
    passed = (len(issues) <= goal["max_issues"]
              and len(net.subnets) >= goal.get("min_subnets", 0))
    return {"passed": passed, "issues": issues}


@app.get("/api/modules")
def list_modules():
    return read_json(CONTENT_DIR / "modules.json")


@app.get("/api/modules/{code}/lessons")
def list_lessons(code: str):
    return read_json(CONTENT_DIR / safe_slug(code) / "lessons.json")


class QuizAnswers(BaseModel):
    answers: list[int]


@app.post("/api/quizzes/{quiz_id}/submit")
def submit_quiz(quiz_id: str, body: QuizAnswers):
    quiz = read_json(CONTENT_DIR / "quizzes" / f"{safe_slug(quiz_id)}.json")
    try:
        return score_quiz(quiz, body.answers)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class RouteIn(BaseModel):
    destination: str
    next_hop: str


class RuleIn(BaseModel):
    name: str
    priority: int
    direction: str
    protocol: str
    port: int | None = None
    source: str = "*"
    action: str


class StatementIn(BaseModel):
    effect: str
    actions: list[str]
    resources: list[str]


def to_routes(items): return [routing.Route(r.destination, r.next_hop) for r in items]
def to_rules(items): return [firewall.Rule(r.name, r.priority, r.direction, r.protocol,
                                           r.port, r.source, r.action) for r in items]
def to_statements(items): return [iam.Statement(s.effect, s.actions, s.resources) for s in items]


class RouteQuery(BaseModel):
    routes: list[RouteIn]
    dest_ip: str


@app.post("/api/sim/network/route")
def route(q: RouteQuery):
    found = routing.lookup(to_routes(q.routes), q.dest_ip)
    return {"route": None if found is None
            else {"destination": found.destination, "next_hop": found.next_hop}}


class FirewallQuery(BaseModel):
    rules: list[RuleIn]
    direction: str
    protocol: str
    port: int
    src_ip: str
    default: str = "deny"


@app.post("/api/sim/firewall/evaluate")
def firewall_evaluate(q: FirewallQuery):
    action, rule_name = firewall.evaluate(to_rules(q.rules), q.direction, q.protocol,
                                          q.port, q.src_ip, q.default)
    return {"action": action, "rule": rule_name}


class IamQuery(BaseModel):
    statements: list[StatementIn]
    action: str
    resource: str


@app.post("/api/sim/iam/evaluate")
def iam_evaluate(q: IamQuery):
    d = iam.evaluate(to_statements(q.statements), q.action, q.resource)
    return {"allowed": d.allowed, "reason": d.reason}


class InstanceIn(BaseModel):
    name: str
    subnet: str
    state: str = "running"


class LabState(BaseModel):
    network: NetworkIn
    routes: list[RouteIn] = []
    rules: list[RuleIn] = []
    statements: list[StatementIn] = []
    instances: list[InstanceIn] = []


@app.post("/api/labs/{lab_id}/check")          # used by labs that define "goal_checks"
def check_lab(lab_id: str, s: LabState):
    lab = load_lab(lab_id)
    state = {"network": to_network(s.network), "routes": to_routes(s.routes),
             "rules": to_rules(s.rules), "statements": to_statements(s.statements),
             "instances": [compute.Instance(i.name, i.subnet, i.state) for i in s.instances]}
    failures = validator.run_checks(state, lab["goal_checks"])
    return {"passed": not failures, "issues": failures}


class LabIn(BaseModel):
    networks: list[NetworkIn]


class ImportIn(BaseModel):
    text: str
    format: str = "json"


@app.post("/api/lab-configs/export")
def export_lab(lab: LabIn, format: str = "json"):
    text = topology.export_lab([to_network(n) for n in lab.networks], format)
    media = "application/json" if format == "json" else "application/x-yaml"
    return Response(content=text, media_type=media)


@app.post("/api/lab-configs/import")
def import_lab(body: ImportIn):
    try:
        nets = topology.import_lab(body.text, body.format)
    except (ValueError, KeyError, TypeError) as e:
        raise HTTPException(status_code=400, detail=f"Bad lab file: {e}")
    return topology.to_dict(nets)
