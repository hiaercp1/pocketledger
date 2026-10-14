/**
 * BalanceDisplay — F4 live signed balance display.
 *
 * Computes display value via integer-cent arithmetic to avoid float drift.
 *
 * @prop {string} balance  Decimal string returned by GET /summary/balance (e.g. "123.45" or "-5.00").
 */
export default function BalanceDisplay({ balance }) {
  const negative = String(balance).startsWith('-');
  const abs = negative ? String(balance).slice(1) : String(balance);
  const [intPart, fracPart = ''] = abs.split('.');

  // Build exact cents from string parts — no parseFloat involved
  const centsInt = parseInt(intPart || '0', 10) * 100 + parseInt(fracPart.padEnd(2, '0').slice(0, 2), 10);
  const dollars = Math.floor(centsInt / 100);
  const cents = centsInt % 100;
  const formatted = `${negative ? '-' : ''}$${dollars}.${String(cents).padStart(2, '0')}`;

  return (
    <div className={`balance-display balance-display--${negative ? 'negative' : 'positive'}`}>
      <span className="balance-display__label">Balance</span>
      <span className="balance-display__value">{formatted}</span>
    </div>
  );
}
