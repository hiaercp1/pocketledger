/**
 * ExportCsvButton — triggers a CSV download of all transactions.
 *
 * Fetches GET /transactions/export with the bearer token, then creates a
 * temporary anchor element to download the response as a file.  Uses the
 * same token and base path as {@link apiFetch} but handles the response as
 * a Blob instead of JSON.
 *
 * @prop {function(string): void} [onError]
 *   Optional callback invoked with an error message string if the download
 *   request fails (e.g. network error or non-OK HTTP status).
 */
export default function ExportCsvButton({ onError }) {
  async function handleExport() {
    try {
      const token = import.meta.env.VITE_API_TOKEN ?? '';
      const res = await fetch('/api/transactions/export', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'transactions.csv';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      if (onError) onError(`Export failed: ${e.message}`);
    }
  }

  return (
    <button className="btn btn--secondary" onClick={handleExport}>
      Export CSV
    </button>
  );
}
