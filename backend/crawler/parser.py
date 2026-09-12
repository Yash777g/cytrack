import json
from pathlib import Path


class CrawlParser:

    def __init__(self, json_file: Path):
        self.json_file = json_file
        self.data = {}

    def load(self):

        with open(self.json_file, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def build_context(self):

        return {

            # Target Information
            "target": self.data.get("meta", {}).get("target"),

            # Summary
            "summary": self.data.get("summary", {}),

            # URLs
            "endpoints": self.data.get("endpoints", []),

            # Response Headers
            "response_headers": self.data.get("target_response_headers", {}),

            # Missing Security Headers
            "header_audit": self.data.get("header_audit", []),

            # Technologies
            "technologies": self.data.get("tech_stack", []),

            # WAF
            "waf": self.data.get("waf_findings", []),

            # Secrets
            "secrets": self.data.get("secrets", []),

            # GraphQL
            "graphql": self.data.get("graphql", []),

            # OpenAPI
            "openapi": self.data.get("openapi", []),

            # Source Maps
            "sourcemaps": self.data.get("sourcemaps", []),

            # Sensitive Files
            "sensitive_files": self.data.get("sensitive_files", []),

            # JS Libraries
            "javascript_libraries": self.data.get("js_libs", []),

            # DNS
            "dns_findings": self.data.get("dns_findings", []),

            # CORS
            "cors_issues": self.data.get("cors_issues", []),

            # Credentials
            "credentials": self.data.get("credentials", []),

            # Extracted Data
            "extracted_data": self.data.get("extracted_data", []),

            # Comments
            "comments": self.data.get("comments", [])
        }