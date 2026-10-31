"""
Contract-Driven Mock API Server for Design Reference Catalog.
Runs autonomously from spec/openapi.json or spec/openapi.yaml without server production logic.
Provides realistic HTTP mocking for both Positive and Negative contract scenarios.
Compliant with RFC 7807 Problem Details and OpenAPI 3.0.3 specification.
"""
import sys
import json
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from pathlib import Path


def load_spec():
    root = Path(__file__).resolve().parent.parent
    json_path = root / "spec" / "openapi.json"
    yaml_path = root / "spec" / "openapi.yaml"
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    elif yaml_path.exists():
        import yaml
        with open(yaml_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    raise FileNotFoundError("OpenAPI specification file not found in spec/")


SPEC = load_spec()


class MockState:
    """In-memory state for contract mock verification."""
    def __init__(self):
        self.reset()

    def reset(self):
        self.categories = [
            {"name": "General", "is_default": True},
            {"name": "UI/UX", "is_default": False},
            {"name": "Branding", "is_default": False},
            {"name": "3D", "is_default": False},
            {"name": "Typography", "is_default": False},
            {"name": "Motion", "is_default": False}
        ]
        self.references = {
            "ref-001": {
                "id": "ref-001",
                "title": "Minimalist Landing Page Design",
                "url": "https://example.com/inspiration-1",
                "image_url": "https://example.com/preview-1.png",
                "category": "UI/UX",
                "tags": ["minimalism", "landing", "style:clean"],
                "notes": "Good hero typography inspiration",
                "created_at": "2026-10-15T10:30:00Z"
            },
            "ref-002": {
                "id": "ref-002",
                "title": "Brutalism Identity Guidelines",
                "url": "https://example.com/branding-guidelines",
                "image_url": "https://example.com/preview-2.png",
                "category": "Branding",
                "tags": ["branding", "style:brutalism", "identity"],
                "notes": "High contrast Swiss typography layout",
                "created_at": "2026-10-16T14:20:00Z"
            },
            "ref-003": {
                "id": "ref-003",
                "title": "SaaS Dashboard Dark Mode",
                "url": "https://example.com/saas-dashboard",
                "image_url": None,
                "category": "UI/UX",
                "tags": ["dashboard", "saas", "dark-mode"],
                "notes": "Interactive financial charts mockup",
                "created_at": "2026-10-18T09:15:00Z"
            }
        }
        self.collections = {
            "col-01": {
                "id": "col-01",
                "name": "E-Commerce Client Pitch",
                "description": "Visual references for initial client workshop",
                "reference_ids": ["ref-001", "ref-003"]
            }
        }


STATE = MockState()


class MockAPIRequestHandler(BaseHTTPRequestHandler):
    server_version = "MockOpenAPIServer/1.0"

    def log_message(self, format, *args):
        # Clean custom logger
        sys.stdout.write(f"[MockAPI] [{self.log_date_time_string()}] {format % args}\n")

    def _send_problem(self, status: int, title: str, code: str, detail: str, invalid_params=None):
        payload = {
            "type": f"https://api.design-refs.local/errors/{code.lower().replace('_', '-')}",
            "title": title,
            "status": status,
            "code": code,
            "detail": detail,
            "instance": self.path,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        if invalid_params:
            payload["invalid_params"] = invalid_params

        body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/problem+json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Mock-Engine", "OpenAPI-Contract-Mock")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, data: any):
        body = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Mock-Engine", "OpenAPI-Contract-Mock")
        self.end_headers()
        self.wfile.write(body)

    def _parse_body(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return None
        raw_body = self.rfile.read(content_length).decode("utf-8")
        try:
            return json.loads(raw_body)
        except Exception:
            raise ValueError("Malformed JSON in request body")

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        query = parse_qs(parsed.query)

        # Health
        if path == "/api/v1/health":
            self._send_json(200, {
                "status": "healthy",
                "version": SPEC["info"]["version"],
                "service": "design-reference-catalog-api",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "latency_target_ms": 50
            })
            return

        # List references (filtering & search)
        if path == "/api/v1/references":
            items = list(STATE.references.values())

            # Category filter
            if "category" in query:
                cat = query["category"][0]
                items = [r for r in items if r["category"].lower() == cat.lower()]

            # Conjunctive Tag Filtering (AND)
            if "tags" in query:
                req_tags = [t.strip().lower() for t in query["tags"][0].split(",") if t.strip()]
                items = [
                    r for r in items
                    if set(req_tags).issubset({t.lower() for t in r["tags"]})
                ]

            # Full-text search
            if "q" in query:
                q_str = query["q"][0].strip().lower()
                items = [
                    r for r in items
                    if (q_str in r["title"].lower() or
                        q_str in (r.get("notes") or "").lower() or
                        any(q_str in t.lower() for t in r["tags"]))
                ]

            limit = int(query.get("limit", [50])[0])
            offset = int(query.get("offset", [0])[0])
            paginated = items[offset:offset + limit]

            self._send_json(200, {
                "items": paginated,
                "total": len(items),
                "limit": limit,
                "offset": offset
            })
            return

        # Single reference
        match_ref = re.match(r"^/api/v1/references/([^/]+)$", path)
        if match_ref:
            ref_id = match_ref.group(1)
            ref = STATE.references.get(ref_id)
            if not ref:
                self._send_problem(404, "Resource Not Found", "RESOURCE_NOT_FOUND",
                                   f"Reference with ID '{ref_id}' was not found in catalog.")
                return
            self._send_json(200, ref)
            return

        # List collections
        if path == "/api/v1/collections":
            resp = [
                {
                    "id": c["id"],
                    "name": c["name"],
                    "description": c.get("description"),
                    "reference_count": len(c["reference_ids"])
                }
                for c in STATE.collections.values()
            ]
            self._send_json(200, resp)
            return

        # Single collection with items
        match_col = re.match(r"^/api/v1/collections/([^/]+)$", path)
        if match_col:
            col_id = match_col.group(1)
            col = STATE.collections.get(col_id)
            if not col:
                self._send_problem(404, "Resource Not Found", "RESOURCE_NOT_FOUND",
                                   f"Collection with ID '{col_id}' was not found.")
                return
            self._send_json(200, col)
            return

        # List categories
        if path == "/api/v1/categories":
            self._send_json(200, STATE.categories)
            return

        self._send_problem(404, "Not Found", "ROUTE_NOT_FOUND", f"Route '{path}' does not exist.")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        try:
            body = self._parse_body()
        except ValueError as e:
            self._send_problem(400, "Bad Request", "MALFORMED_JSON", str(e))
            return

        # Create reference
        if path == "/api/v1/references":
            if not body or not isinstance(body, dict):
                self._send_problem(400, "Bad Request", "MALFORMED_REQUEST", "Request body must be a JSON object.")
                return

            invalid_params = []
            title = body.get("title")
            url = body.get("url")

            if not title or not str(title).strip():
                invalid_params.append({"name": "title", "reason": "Title is required and cannot be empty."})

            if not url or not str(url).strip():
                invalid_params.append({"name": "url", "reason": "URL is required and cannot be empty."})

            if invalid_params:
                self._send_problem(400, "Bad Request", "VALIDATION_FAILED",
                                   "Required fields validation failed.", invalid_params)
                return

            # REQ-NF-004 Security check: protocols http:// and https:// only
            url_str = str(url).strip()
            if not (url_str.startswith("http://") or url_str.startswith("https://")):
                self._send_problem(422, "Security Violation", "UNSAFE_URL_PROTOCOL",
                                   f"Invalid URL scheme in '{url_str}'. Only 'http://' and 'https://' are permitted.",
                                   [{"name": "url", "reason": "Unsafe protocol rejected by REQ-NF-004."}])
                return

            img_url = body.get("image_url")
            if img_url and not (str(img_url).startswith("http://") or str(img_url).startswith("https://")):
                self._send_problem(422, "Security Violation", "UNSAFE_URL_PROTOCOL",
                                   "Invalid image_url scheme. Only 'http://' and 'https://' are permitted.",
                                   [{"name": "image_url", "reason": "Unsafe image protocol."}])
                return

            new_id = f"ref-{len(STATE.references) + 101}"
            new_ref = {
                "id": new_id,
                "title": title.strip(),
                "url": url_str,
                "image_url": img_url,
                "category": body.get("category", "General"),
                "tags": [t.strip().lower() for t in body.get("tags", []) if t.strip()],
                "notes": body.get("notes", ""),
                "created_at": datetime.utcnow().isoformat() + "Z"
            }
            STATE.references[new_id] = new_ref
            self._send_json(201, new_ref)
            return

        # Create collection
        if path == "/api/v1/collections":
            if not body or not body.get("name"):
                self._send_problem(400, "Bad Request", "VALIDATION_FAILED", "Collection name is required.",
                                   [{"name": "name", "reason": "Field is required."}])
                return
            new_col_id = f"col-{len(STATE.collections) + 1:02d}"
            new_col = {
                "id": new_col_id,
                "name": body["name"].strip(),
                "description": body.get("description"),
                "reference_ids": []
            }
            STATE.collections[new_col_id] = new_col
            self._send_json(201, {
                "id": new_col["id"],
                "name": new_col["name"],
                "description": new_col["description"],
                "reference_count": 0
            })
            return

        # Add reference to collection
        match_add = re.match(r"^/api/v1/collections/([^/]+)/references/([^/]+)$", path)
        if match_add:
            col_id = match_add.group(1)
            ref_id = match_add.group(2)
            col = STATE.collections.get(col_id)
            if not col:
                self._send_problem(404, "Not Found", "COLLECTION_NOT_FOUND", f"Collection '{col_id}' not found.")
                return
            if ref_id not in STATE.references:
                self._send_problem(404, "Not Found", "REFERENCE_NOT_FOUND", f"Reference '{ref_id}' not found.")
                return
            if ref_id not in col["reference_ids"]:
                col["reference_ids"].append(ref_id)
            self._send_json(200, col)
            return

        # Create category
        if path == "/api/v1/categories":
            if not body or not body.get("name"):
                self._send_problem(400, "Bad Request", "VALIDATION_FAILED", "Category name is required.")
                return
            cat_name = body["name"].strip()
            if any(c["name"].lower() == cat_name.lower() for c in STATE.categories):
                self._send_problem(400, "Bad Request", "CATEGORY_EXISTS", f"Category '{cat_name}' already exists.")
                return
            new_cat = {"name": cat_name, "is_default": False}
            STATE.categories.append(new_cat)
            self._send_json(201, new_cat)
            return

        self._send_problem(404, "Not Found", "ROUTE_NOT_FOUND", f"Route '{path}' does not exist.")

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        try:
            body = self._parse_body()
        except ValueError as e:
            self._send_problem(400, "Bad Request", "MALFORMED_JSON", str(e))
            return

        match_ref = re.match(r"^/api/v1/references/([^/]+)$", path)
        if match_ref:
            ref_id = match_ref.group(1)
            ref = STATE.references.get(ref_id)
            if not ref:
                self._send_problem(404, "Not Found", "RESOURCE_NOT_FOUND", f"Reference '{ref_id}' not found.")
                return
            if not body or not isinstance(body, dict):
                self._send_problem(400, "Bad Request", "MALFORMED_REQUEST", "Expected JSON object.")
                return

            if "title" in body:
                if not body["title"] or not str(body["title"]).strip():
                    self._send_problem(400, "Bad Request", "VALIDATION_FAILED", "Title cannot be empty.",
                                       [{"name": "title", "reason": "Cannot be empty."}])
                    return
                ref["title"] = body["title"].strip()

            if "category" in body:
                ref["category"] = body["category"]

            if "tags" in body:
                ref["tags"] = [t.strip().lower() for t in body["tags"] if t.strip()]

            if "notes" in body:
                ref["notes"] = body["notes"]

            if "image_url" in body:
                img = body["image_url"]
                if img and not (str(img).startswith("http://") or str(img).startswith("https://")):
                    self._send_problem(422, "Security Violation", "UNSAFE_URL_PROTOCOL",
                                       "Invalid image_url scheme.")
                    return
                ref["image_url"] = img

            self._send_json(200, ref)
            return

        self._send_problem(404, "Not Found", "ROUTE_NOT_FOUND", f"Route '{path}' does not exist.")

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        # Delete reference
        match_ref = re.match(r"^/api/v1/references/([^/]+)$", path)
        if match_ref:
            ref_id = match_ref.group(1)
            if ref_id not in STATE.references:
                self._send_problem(404, "Not Found", "RESOURCE_NOT_FOUND", f"Reference '{ref_id}' not found.")
                return
            del STATE.references[ref_id]
            # Dissociate from collections
            for col in STATE.collections.values():
                if ref_id in col["reference_ids"]:
                    col["reference_ids"].remove(ref_id)
            self.send_response(204)
            self.send_header("X-Mock-Engine", "OpenAPI-Contract-Mock")
            self.end_headers()
            return

        # Delete collection
        match_col = re.match(r"^/api/v1/collections/([^/]+)$", path)
        if match_col:
            col_id = match_col.group(1)
            if col_id not in STATE.collections:
                self._send_problem(404, "Not Found", "RESOURCE_NOT_FOUND", f"Collection '{col_id}' not found.")
                return
            del STATE.collections[col_id]
            self.send_response(204)
            self.send_header("X-Mock-Engine", "OpenAPI-Contract-Mock")
            self.end_headers()
            return

        # Remove reference from collection
        match_rem = re.match(r"^/api/v1/collections/([^/]+)/references/([^/]+)$", path)
        if match_rem:
            col_id = match_rem.group(1)
            ref_id = match_rem.group(2)
            col = STATE.collections.get(col_id)
            if not col:
                self._send_problem(404, "Not Found", "COLLECTION_NOT_FOUND", f"Collection '{col_id}' not found.")
                return
            if ref_id in col["reference_ids"]:
                col["reference_ids"].remove(ref_id)
            self.send_response(204)
            self.send_header("X-Mock-Engine", "OpenAPI-Contract-Mock")
            self.end_headers()
            return

        # Delete category (with REQ-NF-003 fallback to 'General')
        match_cat = re.match(r"^/api/v1/categories/([^/]+)$", path)
        if match_cat:
            cat_name = match_cat.group(1)
            # Cannot delete default 'General'
            if cat_name.lower() == "general":
                self._send_problem(400, "Bad Request", "PROTECTED_RESOURCE",
                                   "System category 'General' cannot be deleted.")
                return

            target = next((c for c in STATE.categories if c["name"].lower() == cat_name.lower()), None)
            if not target:
                self._send_problem(404, "Not Found", "CATEGORY_NOT_FOUND", f"Category '{cat_name}' not found.")
                return

            STATE.categories.remove(target)
            # Reassign all references to 'General' (0% data loss)
            migrated_count = 0
            for ref in STATE.references.values():
                if ref["category"].lower() == cat_name.lower():
                    ref["category"] = "General"
                    migrated_count += 1

            self._send_json(200, {
                "message": f"Category '{cat_name}' removed successfully.",
                "reassigned_to": "General",
                "affected_references_count": migrated_count
            })
            return

        self._send_problem(404, "Not Found", "ROUTE_NOT_FOUND", f"Route '{path}' does not exist.")


def run_server(host="127.0.0.1", port=8000):
    server_address = (host, port)
    httpd = HTTPServer(server_address, MockAPIRequestHandler)
    print(f"============================================================")
    print(f"Design Reference Catalog Mock API Server Started")
    print(f"Listening on: http://{host}:{port}/api/v1")
    print(f"Contract: spec/openapi.yaml / spec/openapi.json")
    print(f"Press Ctrl+C to terminate.")
    print(f"============================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Shutting down Mock API server...")
        httpd.server_close()


if __name__ == "__main__":
    p = 8000
    if len(sys.argv) > 1:
        p = int(sys.argv[1])
    run_server(port=p)
