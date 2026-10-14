import { formatDecimalAmount } from '../utils.js';

/**
 * CategoryBreakdown — F5.
 *
 * Renders a two-column table of category totals aggregated by the backend.
 * Positive totals (income) are styled in green; negative (expense) in red.
 * Reuses existing `.tx-table` / `.tx-row` CSS classes for visual consistency
 * with TransactionList.
 *
 * @prop {Array<{category: string, total: string}>} categoryTotals
 *   Pre-sorted array from GET /summary/categories (descending by total).
 */
export default function CategoryBreakdown({ categoryTotals }) {
  return (
    <table className="tx-table">
      <thead>
        <tr>
          <th>Category</th>
          <th className="tx-table__amount-col">Total</th>
        </tr>
      </thead>
      <tbody>
        {categoryTotals.length === 0 ? (
          <tr>
            <td colSpan={2} style={{ color: 'var(--color-muted)', textAlign: 'center', padding: '1rem 0' }}>
              No categories yet
            </td>
          </tr>
        ) : (
          categoryTotals.map(({ category, total }) => {
            const isExpense = parseFloat(total) < 0;
            return (
              <tr key={category} className={`tx-row tx-row--${isExpense ? 'expense' : 'income'}`}>
                <td>
                  <span className="tx-row__category">{category}</span>
                </td>
                <td className={`tx-row__amount tx-row__amount--${isExpense ? 'expense' : 'income'}`}>
                  {formatDecimalAmount(total)}
                </td>
              </tr>
            );
          })
        )}
      </tbody>
    </table>
  );
}
