import type { ReactNode } from "react";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";
import { InfoTip } from "./InfoTip";

export type Col<T> = {
  id: string;
  header: string;
  render: (row: T) => ReactNode;
  align?: "right";
  /** hidden on a phone, so rows stay short */
  secondary?: boolean;
  primary?: boolean;
};

type Props<T> = {
  label: string;
  columns: Col<T>[];
  rows: T[];
  rowId: (row: T) => string;
  empty: string;
  /** makes each row a button: click or Enter opens it */
  onRowClick?: (row: T) => void;
};

function cellClass<T>(column: Col<T>): string {
  return cn(column.align === "right" && "text-right", column.secondary && "max-[720px]:hidden");
}

/** A shadcn table: grey headers, row rules, numbers right-aligned. */
export function DataTable<T extends object>({ label, columns, rows, rowId, empty, onRowClick }: Props<T>) {
  if (rows.length === 0) {
    return <p className="empty">{empty}</p>;
  }
  const headers = [];
  for (const column of columns) {
    headers.push(
      <TableHead key={column.id} className={cellClass(column)}>
        <span className="inline-flex items-center gap-1">
          {column.header}
          <InfoTip label={column.header} />
        </span>
      </TableHead>,
    );
  }
  const body = [];
  for (const row of rows) {
    const cells = [];
    for (const column of columns) {
      cells.push(
        <TableCell key={column.id} className={cn(cellClass(column), column.primary && "font-medium")}>
          {column.render(row)}
        </TableCell>,
      );
    }
    if (onRowClick) {
      body.push(
        <TableRow
          key={rowId(row)}
          tabIndex={0}
          className="cursor-pointer"
          onClick={() => onRowClick(row)}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              onRowClick(row);
            }
          }}
        >
          {cells}
        </TableRow>,
      );
    } else {
      body.push(<TableRow key={rowId(row)}>{cells}</TableRow>);
    }
  }
  return (
    <Table aria-label={label}>
      <TableHeader>
        <TableRow className="hover:bg-transparent">{headers}</TableRow>
      </TableHeader>
      <TableBody>{body}</TableBody>
    </Table>
  );
}
