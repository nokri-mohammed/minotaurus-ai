import type { ReactNode } from "react";
import { Cell, Column, Row, Table, TableBody, TableHeader } from "react-aria-components";

export type Col<T> = {
  id: string;
  header: string;
  render: (row: T) => ReactNode;
  align?: "right";
  /** hidden on a phone, so rows stay short */
  secondary?: boolean;
  primary?: boolean;
};

type Props<T> = { label: string; columns: Col<T>[]; rows: T[]; rowId: (row: T) => string; empty: string };

/** Rules and alignment: grey sentence-case headers, 1px row rules, numbers right-aligned. */
export function DataTable<T extends object>({ label, columns, rows, rowId, empty }: Props<T>) {
  const cls = (c: Col<T>) => [c.align === "right" ? "num" : "", c.secondary ? "hide-sm" : ""].join(" ").trim();
  return (
    <Table aria-label={label} className="table">
      <TableHeader columns={columns}>
        {(c) => (
          <Column id={c.id} isRowHeader={c.primary} className={cls(c)}>
            {c.header}
          </Column>
        )}
      </TableHeader>
      <TableBody items={rows} renderEmptyState={() => <p className="empty">{empty}</p>}>
        {(row) => (
          <Row id={rowId(row)} columns={columns}>
            {(c) => <Cell className={cls(c)}>{c.render(row)}</Cell>}
          </Row>
        )}
      </TableBody>
    </Table>
  );
}
