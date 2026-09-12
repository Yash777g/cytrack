import json
import subprocess


class DeepHat:

    def __init__(self):
        self.model = "hf.co/mradermacher/DeepHat-V1-7B-GGUF:Q4_K_M"

    def analyze(self, prompt: str):

        print(f"\nPrompt Size: {len(prompt)} characters\n")

        process = subprocess.run(
            [
                "ollama",
                "run",
                self.model,
                "--format",
                "json"
            ],
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        print("Return Code:", process.returncode)

        if process.stderr:
            print("STDERR:")
            print(process.stderr)

        if process.returncode != 0:
            raise RuntimeError(
                f"DeepHat failed with return code "
                f"{process.returncode}"
            )

        raw_output = process.stdout.strip()

        if not raw_output:
            raise ValueError(
                "DeepHat returned an empty response."
            )

        # Ollama may still surround the object with a harmless JSON fence.
        cleaned_output = raw_output.strip()

        if cleaned_output.startswith("```") and cleaned_output.endswith("```"):
            first_line_end = cleaned_output.find("\n")

            if first_line_end == -1:
                cleaned_output = cleaned_output[3:-3].strip()
            else:
                cleaned_output = cleaned_output[first_line_end + 1:-3].strip()

        # Locate the outermost JSON object without interpreting braces inside
        # JSON strings as structural braces.
        start = cleaned_output.find("{")

        if start == -1:
            raise ValueError(
                "DeepHat must return exactly one JSON object.\n\n"
                f"Raw output:\n{raw_output}"
            )

        depth = 0
        inside_string = False
        escaped = False
        end = None

        for index in range(start, len(cleaned_output)):
            char = cleaned_output[index]

            if escaped:
                escaped = False
                continue

            if char == "\\" and inside_string:
                escaped = True
                continue

            if char == '"':
                inside_string = not inside_string
                continue

            if inside_string:
                continue

            if char == "{":
                depth += 1

            elif char == "}":
                depth -= 1

                if depth == 0:
                    end = index
                    break

        if end is None or depth != 0:
            raise ValueError(
                "DeepHat must return exactly one JSON object.\n\n"
                f"Raw output:\n{raw_output}"
            )

        json_text = cleaned_output[start:end + 1]

        # ----------------------------------------------------
        # Repair raw control characters inside JSON strings
        # ----------------------------------------------------

        repaired_chars = []
        inside_string = False
        escaped = False

        for char in json_text:

            if escaped:
                repaired_chars.append(char)
                escaped = False
                continue

            if char == "\\":
                repaired_chars.append(char)
                escaped = True
                continue

            if char == '"':
                repaired_chars.append(char)
                inside_string = not inside_string
                continue

            if inside_string:

                if char == "\n":
                    repaired_chars.append("\\n")

                elif char == "\r":
                    repaired_chars.append("\\r")

                elif char == "\t":
                    repaired_chars.append("\\t")

                elif ord(char) < 32:
                    repaired_chars.append(" ")

                else:
                    repaired_chars.append(char)

            else:
                repaired_chars.append(char)

        repaired_json = "".join(repaired_chars)

        # ----------------------------------------------------
        # Parse JSON
        # ----------------------------------------------------

        try:

            result = json.loads(repaired_json)

        except json.JSONDecodeError as exc:

            print(
                "\n========== RAW DEEPHAT OUTPUT ==========\n"
            )
            print(raw_output)

            print(
                "\n========== CLEANED JSON ==========\n"
            )
            print(repaired_json)

            raise ValueError(
                "DeepHat returned invalid JSON.\n"
                f"JSON Error: {exc}"
            ) from exc

        # ----------------------------------------------------
        # Basic validation
        # ----------------------------------------------------

        if not isinstance(result, dict):
            raise ValueError(
                "DeepHat response must be a JSON object."
            )

        required_fields = {
            "executive_summary",
            "overall_risk",
            "confirmed_findings",
            "potential_vulnerabilities",
            "not_observed",
            "security_recommendations",
            "final_conclusion"
        }

        missing_fields = required_fields.difference(result)

        if missing_fields:
            raise ValueError(
                "DeepHat JSON is missing required fields: "
                + ", ".join(sorted(missing_fields))
            )

        # ----------------------------------------------------
        # Ensure Planner field exists
        # ----------------------------------------------------

        if not isinstance(
            result["potential_vulnerabilities"],
            list
        ):
            raise ValueError(
                "'potential_vulnerabilities' must be a list."
            )

        # ----------------------------------------------------
        # Normalize potential vulnerability findings
        # ----------------------------------------------------

        normalized_findings = []

        for finding in result["potential_vulnerabilities"]:

            if not isinstance(finding, dict):
                continue

            normalized_findings.append(finding)

        result["potential_vulnerabilities"] = (
            normalized_findings
        )

        # ----------------------------------------------------
        # Success
        # ----------------------------------------------------

        print(
            "\nDeepHat JSON parsed successfully."
        )

        print(
            "Potential vulnerabilities:",
            len(result["potential_vulnerabilities"])
        )

        return result