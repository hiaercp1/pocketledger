/**
 * formatDecimalAmount — convert a Decimal string to a display currency string.
 *
 * Uses integer-cent arithmetic (no parseFloat/toFixed in the result path) to
 * avoid IEEE 754 rounding artefacts.
 *
 * @param {string} totalStr  Decimal string, e.g. "5000.00" or "-150.50"
 * @returns {string}         e.g. "$5000.00" or "–$150.50" (en-dash for negatives)
 */
export function formatDecimalAmount(totalStr) {
  const negative = totalStr.startsWith('-');
  const abs = negative ? totalStr.slice(1) : totalStr;
  const [intPart, fracPart = ''] = abs.split('.');
  const cents = parseInt(intPart, 10) * 100 + parseInt(fracPart.padEnd(2, '0').slice(0, 2), 10);
  const dollars = Math.floor(cents / 100);
  const centsRemainder = cents % 100;
  const formatted = `$${dollars}.${String(centsRemainder).padStart(2, '0')}`;
  return negative ? `\u2013${formatted}` : formatted;
}
