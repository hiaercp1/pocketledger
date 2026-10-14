import { useState, useEffect, useCallback } from 'react';
import { apiFetch } from './api.js';
import AddTransaction from './components/AddTransaction.jsx';
import TransactionList from './components/TransactionList.jsx';
import BalanceDisplay from './components/BalanceDisplay.jsx';
import CategoryBreakdown from './components/CategoryBreakdown.jsx';
import CategoryChart from './components/CategoryChart.jsx';

/**
 * App — root component that owns global state and wires all sub-components.
 *
 * State:
 *   transactions    {Array}  full list fetched from GET /transactions
 *   balance         {string} Decimal string from GET /summary/balance
 *   categoryTotals  {Array}  list of {category, total} from GET /summary/categories
 *   filterCategory  {string} currently selected category filter ("" = all)
 *   error           {string} top-level fetch error message
 */
export default function App() {
  const [transactions, setTransactions] = useState([]);
  const [balance, setBalance] = useState('0');
  const [categoryTotals, setCategoryTotals] = useState([]);
  const [filterCategory, setFilterCategory] = useState('');
  const [error, setError] = useState('');

  const refresh = useCallback(async () => {
    try {
      const [txData, balData, catData] = await Promise.all([
        apiFetch('/transactions'),
        apiFetch('/summary/balance'),
        apiFetch('/summary/categories'),
      ]);
      setTransactions(txData);
      setBalance(balData.balance);
      setCategoryTotals(catData);
      setError('');
    } catch (e) {
      setError(`Failed to load data: ${e.message}`);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleAdd = useCallback(
    async (payload) => {
      await apiFetch('/transactions', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      await refresh();
    },
    [refresh],
  );

  const handleDelete = useCallback(
    async (id) => {
      await apiFetch(`/transactions/${id}`, { method: 'DELETE' });
      await refresh();
    },
    [refresh],
  );

  return (
    <div className="app">
      <header className="app-header">
        <h1>PocketLedger</h1>
        <BalanceDisplay balance={balance} />
      </header>

      {error && <p className="error-banner">{error}</p>}

      <main className="app-main">
        <section className="panel panel--form">
          <h2>Add Transaction</h2>
          <AddTransaction onAdd={handleAdd} />
        </section>

        <section className="panel panel--list">
          <h2>Transactions</h2>
          <TransactionList
            transactions={transactions}
            onDelete={handleDelete}
            filterCategory={filterCategory}
            onFilterChange={setFilterCategory}
          />
        </section>

        <section className="panel panel--summary">
          <h2>By Category</h2>
          <CategoryChart categoryTotals={categoryTotals} />
          <CategoryBreakdown categoryTotals={categoryTotals} />
        </section>
      </main>
    </div>
  );
}
