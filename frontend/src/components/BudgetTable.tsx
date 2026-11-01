import { rupees } from "../lib/format";
import type { BudgetLine } from "../types";

const METER_MAX_PERCENT = 40;

interface BudgetTableProps {
  lines: BudgetLine[];
  total: number;
}

export default function BudgetTable({ lines, total }: BudgetTableProps) {
  return (
    <section className="card" aria-labelledby="h-budget">
      <h2 id="h-budget">Budget split</h2>
      <div className="table-scroll" role="region" aria-label="Budget table, scrollable" tabIndex={0}>
        <table>
          <caption className="sr">Budget by category</caption>
          <thead>
            <tr>
              <th scope="col">Category</th>
              <th scope="col">Share</th>
              <th scope="col" className="num">
                Amount (Rs)
              </th>
            </tr>
          </thead>
          <tbody>
            {lines.map(({ category, pct, amount }) => (
              <tr key={category}>
                <th scope="row">{category}</th>
                <td>
                  <meter min={0} max={METER_MAX_PERCENT} value={pct} aria-label={`${category} ${pct} percent`} /> {pct}%
                </td>
                <td className="num">{rupees(amount)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <th scope="row" colSpan={2}>
                Total
              </th>
              <td className="num">{rupees(total)}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </section>
  );
}
