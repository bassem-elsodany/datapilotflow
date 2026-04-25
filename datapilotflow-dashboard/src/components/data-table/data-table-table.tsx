import { DataTable, DataTableProps } from 'mantine-datatable';

/**
 * Thin wrapper around mantine-datatable's DataTable.
 * Automatically marks every column as resizable so users can drag column
 * borders left/right to adjust widths across the whole app.
 */
export function DataTableTable<T>({ columns, ...rest }: DataTableProps<T>) {
  const resizableColumns = columns?.map((col) => ({
    resizable: true,
    ...col,
  }));

  return <DataTable<T> columns={resizableColumns} {...rest} />;
}
