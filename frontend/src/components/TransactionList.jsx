/**
 * TransactionList — F2 (list newest first), F3 (delete), F7 (category filter).
 *
 * @prop {Array<{id: number, amount: string, description: string, category: string, date: string}>} transactions
 *   Full unfiltered transaction array (already sorted newest first by the API).
 * @prop {function(id: number): Promise<void>} onDelete
 *   Called when the user clicks Delete on a row.
 * @prop {string} filterCategory
 *   Currently selected category filter; empty string means "show all".
 * @prop {function(category: string): void} onFilterChange
 *   Called when the user changes the category filter dropdown.
 */
export default function TransactionList({ transactions, onDelete, filterCategory, onFilterChange }) {
  // Derive unique category list from the full (unfiltered) transactions
  const categories = Array.from(new Set(transactions.map((t) => t.category))).sort();

  const visible =
    filterCategory === ''
      ? transactions
      : transactions.filter((t) => t.category === filterCategory);

  /**
   * Format a Decimal string amount as a signed currency string to 2 dp.
   * Uses integer-cent arithmetic to avoid float drift.
   *
   * @param {string} amountStr  e.g. "12.50" or "-5.00"
   * @returns {string}          e.g. "+$12.50" or "-$5.00"
   */
  function formatAmount(amountStr) {
    const negative = amountStr.startsWith('-');
    const abs = negative ? amountStr.slice(1) : amountStr;
    const [intPart, fracPart = ''] = abs.split('.');
    const cents = parseInt(intPart, 10) * 100 + parseInt(fracPart.padEnd(2, '0').slice(0, 2), 10);
    const dollars = Math.floor(cents / 100);
    const centsRemainder = cents % 100;
    const formatted = `$${dollars}.${String(centsRemainder).padStart(2, '0')}`;
    return negative ? `-${formatted}` : `+${formatted}`;
  }

  return (
    <div className="tx-list">
      <div className="tx-list__filter">
        <label htmlFor="category-filter" className="field__label">
          Filter by category:
        </label>
        <select
          id="category-filter"
          className="field__input"
          value={filterCategory}
          onChange={(e) => onFilterChange(e.target.value)}
        >
          <option value="">All</option>
          {categories.map((cat) => (
            <option key={cat} value={cat}>
              {cat}
            </option>
          ))}
        </select>
      </div>

      {visible.length === 0 ? (
        <p className="tx-list__empty">No transactions found.</p>
      ) : (
        <table className="tx-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Description</th>
              <th>Category</th>
              <th className="tx-table__amount">Amount</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {visible.map((tx) => {
              const negative = tx.amount.startsWith('-');
              return (
                <tr key={tx.id} className={`tx-row tx-row--${negative ? 'expense' : 'income'}`}>
                  <td className="tx-row__date">{tx.date}</td>
                  <td>{tx.description}</td>
                  <td>
                    <span className="tx-row__category">{tx.category}</span>
                  </td>
                  <td className={`tx-table__amount tx-row__amount--${negative ? 'negative' : 'positive'}`}>
                    {formatAmount(tx.amount)}
                  </td>
                  <td>
                    <button
                      className="btn btn--danger btn--sm"
                      onClick={() => onDelete(tx.id)}
                      aria-label={`Delete transaction: ${tx.description}`}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
