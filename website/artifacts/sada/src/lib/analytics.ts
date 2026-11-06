type AnalyticsData = Record<string, string | number | boolean>;
type AnalyticsPayload = {
  website: string;
  url: string;
  name: string;
  data: AnalyticsData;
};
type ReportExportEvent = 'report_export_requested' | 'report_export_failed';
type ReportExportDimensions = {
  language: 'en' | 'ar';
  provenance: 'demo' | 'backend';
};

declare global {
  interface Window {
    umami?: {
      track(payload: (defaults: { website: string }) => AnalyticsPayload): void | Promise<unknown>;
    };
  }
}

/**
 * Replit's publishing proxy injects window.umami when Publishing analytics is
 * enabled. Do not add a tracker script, website ID, or alternate sender here.
 * The development preview intentionally has no tracker.
 *
 * Best-effort only. Never pass report objects, IDs, errors, or free-form text.
 */
export function trackEvent(name: ReportExportEvent, dimensions: ReportExportDimensions): void {
  if (typeof window === 'undefined') return;

  try {
    // Reconstruct the allowlist so extra properties cannot leak at runtime.
    const data = {
      language: dimensions.language,
      provenance: dimensions.provenance,
    };
    // Default event metadata includes the current URL and referrer. Do not
    // forward those: the results URL can contain an evaluation identifier.
    // Use the documented custom-payload API and retain only the tracker ID.
    void Promise.resolve(window.umami?.track(defaults => ({
      website: defaults.website,
      url: '/results',
      name,
      data,
    }))).catch(() => {
      // Rejected analytics requests must not cause unhandled rejections.
    });
  } catch {
    // An unavailable or broken tracker must never block report downloads.
  }
}
