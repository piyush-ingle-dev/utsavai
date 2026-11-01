import { dayMonthYear } from "../lib/format";
import type { ChecklistKey, TimelineItem, VendorItem } from "../types";
import ChecklistItem from "./ChecklistItem";

interface SectionProps<T> {
  items: T[];
  canEdit: boolean;
  onToggle: (list: ChecklistKey, id: string) => void;
}

export function TimelineSection({ items, canEdit, onToggle }: SectionProps<TimelineItem>) {
  return (
    <section className="card" aria-labelledby="h-timeline">
      <h2 id="h-timeline">Timeline</h2>
      <ul className="checklist">
        {items.map((item) => (
          <ChecklistItem key={item.id} checked={item.done} disabled={!canEdit} onToggle={() => onToggle("timeline", item.id)}>
            <strong>{dayMonthYear(item.due)}</strong> {item.task} <em className="chip">{item.category}</em>
            {item.late && <em className="chip warn">compressed</em>}
          </ChecklistItem>
        ))}
      </ul>
    </section>
  );
}

export function VendorSection({ items, canEdit, onToggle, tips }: SectionProps<VendorItem> & { tips: string[] }) {
  return (
    <section className="card" aria-labelledby="h-vendors">
      <h2 id="h-vendors">Vendor checklist</h2>
      <ul className="checklist">
        {items.map((item) => (
          <ChecklistItem key={item.id} checked={item.done} disabled={!canEdit} onToggle={() => onToggle("vendors", item.id)}>
            <strong>{item.vendor}</strong>
            <br />
            <span className="muted">Ask about: {item.ask}</span>
          </ChecklistItem>
        ))}
      </ul>
      {tips.length > 0 && (
        <>
          <h3>Tips</h3>
          <ul>
            {tips.map((tip) => (
              <li key={tip}>{tip}</li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
