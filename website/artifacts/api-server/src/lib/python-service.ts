const port = process.env.SADA_PYTHON_PORT || "8000";
if (!/^\d+$/.test(port) || Number(port) < 1 || Number(port) > 65535) {
  throw new Error("Invalid private Python port");
}

/** Port is configurable for isolated smoke tests; the host is never configurable. */
export const pythonUrl = (route: string) => `http://127.0.0.1:${port}/api/${route}`;

export async function pythonReady(): Promise<boolean> {
  try {
    // Hosted schema/grant checks take multiple round trips. Keep this bounded
    // and below the supervisor's 10-second HTTP deadline.
    const response = await fetch(pythonUrl("health"), { signal: AbortSignal.timeout(8_000) });
    if (!response.ok) return false;
    const body = await response.json();
    return typeof body === "object" && body !== null
      && "status" in body && body.status === "ok"
      && "service" in body && body.service === "sada-evaluation-adapter";
  } catch {
    return false;
  }
}
