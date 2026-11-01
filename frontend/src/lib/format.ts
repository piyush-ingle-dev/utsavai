/** Rupee amounts in Indian digit grouping, e.g. 1000000 -> "10,00,000". */
export const rupees = (amount: number): string => amount.toLocaleString("en-IN");

/** "2026-12-30" -> "30/12/2026". */
export const dayMonthYear = (iso: string): string => `${iso.slice(8, 10)}/${iso.slice(5, 7)}/${iso.slice(0, 4)}`;

/** Local date as YYYY-MM-DD, `daysAhead` days from today. */
export function isoDate(daysAhead: number, from: Date = new Date()): string {
  const date = new Date(from);
  date.setDate(date.getDate() + daysAhead);
  const pad = (n: number): string => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}
