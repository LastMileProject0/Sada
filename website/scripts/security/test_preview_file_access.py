"""Preview containment regression: never read protected response bodies.

Run: python scripts/security/test_preview_file_access.py
Optionally set SADA_SECURITY_BASE_URL to the development Preview origin.
"""
import http.client
import os
from pathlib import Path
from urllib.parse import quote, urljoin, urlsplit


def main():
    origin = os.getenv("SADA_SECURITY_BASE_URL", "http://localhost:80")
    parsed = urlsplit(origin)
    connection_type = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    workspace = Path(__file__).resolve().parents[2].as_posix()
    protected = [
        "backend/sada_bridge/api.py",
        "backend/lastmile_ai/pipeline.py",
        "backend/data/reference/LastMile_AI_Step1_Master_Dataset.xlsx",
        "backend/.sada_api/evaluations.sqlite3",
        "backend/.sada_api/evaluations.sqlite3-wal",
        "backend/lastmile_ai/knowledge/evidence_chunks.json",
        "SADA_Backend_For_Replit_Test.zip",
        ".agents/memory/MEMORY.md",
        "attached_assets/Pasted-Continue-integrating-the-existing-SADA-React-website-wi_1793822111309.txt",
    ]
    results = {}

    def probe(url, expected, method="HEAD"):
        # A raw HTTP client preserves encoded separators and traversal for testing.
        for _ in range(4):
            conn = connection_type(parsed.hostname, parsed.port, timeout=20)
            conn.request(method, url)
            response = conn.getresponse()
            status = response.status
            location = response.getheader("Location")
            conn.close()  # Do not read or print response contents.
            if status not in {301, 302, 307, 308}:
                break
            # The external Preview proxy canonicalizes repeated slashes.
            target = urlsplit(urljoin(origin + url, location or ""))
            assert target.netloc == parsed.netloc, "Unexpected cross-origin redirect"
            results[status] = results.get(status, 0) + 1
            url = target.path + ("?" + target.query if target.query else "")
        assert status in expected, f"{url}: unexpected HTTP {status}"
        results[status] = results.get(status, 0) + 1

    for prefix in ("", "/__mockup"):
        for resource in protected:
            absolute = workspace + "/" + resource
            variants = [
                absolute,
                quote(absolute, safe=""),
                quote(quote(absolute, safe=""), safe=""),
                absolute.replace("backend", "%62ackend"),
                absolute.replace("/", "%2f"),
                absolute.replace("/", "%5c"),
                workspace + "/artifacts/sada/../../" + resource,
            ]
            for variant in variants:
                for query in ("", "?raw", "?url&import"):
                    probe(prefix + "/@fs/" + variant, {403})
            probe(prefix + "/@fs" + quote(absolute, safe=""), {403})
            probe(prefix + "/%40fs/" + absolute, {403})
            probe(prefix + "/@%66s/" + absolute, {403})
            # GET uses the same boundary; close without reading its response body.
            probe(prefix + "/@fs/" + absolute, {403}, "GET")
            if resource.startswith("backend/"):
                probe(prefix + "/" + resource, {403})
        probe(prefix + "/@fs/%00", {403})
        # The shared proxy may reject malformed escapes before Vite sees them.
        probe(prefix + "/@fs/%ZZ", {400, 403})
        probe(prefix + "/@fs/" + workspace + "/.replit", {403})

    # Confirm pages, JavaScript, image assets and API routing still work.
    for url in ("/", "/planning", "/simulation", "/results", "/src/main.tsx",
                "/riyadh-dusk.jpg", "/__mockup/", "/__mockup/src/main.tsx"):
        probe(url, {200})
    probe("/api/health", {200}, "GET")
    print("PASS — no response contents read:", ", ".join(
        f"HTTP {status}: {count}" for status, count in sorted(results.items())
    ))


if __name__ == "__main__":
    main()
