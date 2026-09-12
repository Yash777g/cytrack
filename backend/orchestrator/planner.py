class Planner:
    """
    Decides which security agents should run
    based on DeepHat's potential vulnerabilities.
    """

    def __init__(self, context: dict):
        self.context = context

    def build_execution_plan(self):

        plan = []
        seen = set()

        findings = self.context.get(
            "potential_vulnerabilities",
            []
        )

        for finding in findings:

            vuln = finding.get(
                "vulnerability",
                ""
            ).lower()

            endpoint = finding.get(
                "endpoint",
                ""
            )

            agent = None

            if "sql" in vuln:
                agent = "sql_agent"

            elif "xss" in vuln:
                agent = "xss_agent"

            elif "password" in vuln:
                agent = "password_policy_agent"

            elif "nosql" in vuln or "no sql" in vuln:
                agent = "nosql_agent"

            elif "missing authorization" in vuln:
                agent = "authz_agent"

            elif "sast" in vuln:
                agent = "sast_agent"

            if agent:

                key = (agent, endpoint)

                if key not in seen:

                    plan.append({
                        "agent": agent,
                        "endpoint": endpoint
                    })

                    seen.add(key)

        return plan