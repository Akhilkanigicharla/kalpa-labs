// Types for the shared JobCard core in 02-jobcard/lib (plain JS, also used by the WhatsApp bot).
declare module '@core/parse.mjs' {
  export type Part = { desc: string; qty: number; rate: number | null };
  export type Card = {
    customer: { name?: string; phone?: string; area?: string };
    appliance: string | null;
    brand: string | null;
    capacity_tons?: number;
    issues: string[];
    parts: Part[];
    total: number | null;
    total_check: string;
    next_service: string | null;
    notes: string;
    missing: string[];
  };
  export function parseTranscript(raw: string, opts?: { now?: Date }): Card;
}
declare module '@core/invoice.mjs' {
  export type Kind = 'unregistered' | 'composition' | 'regular';
  export type Totals = {
    kind: Kind;
    rows: Array<{ desc: string; sac?: string; qty: number; ratePaise: number; amountPaise: number }>;
    taxable: number;
    cgst: number;
    sgst: number;
    igst: number;
    total: number;
    roundOff: number;
    payable: number;
    interState: boolean;
    placeOfSupply: string;
    placeCode: string;
  };
  export type Party = { name: string; address?: string; phone?: string; gstin?: string; udyam?: string };
  export type InvoiceMeta = { number: string; date: string; supplier: Party; customer: Party; footer?: string };
  export const SAC: { home: string; commercial: string; install: string };
  export function computeInvoice(o: { kind?: Kind; lines: Array<{ desc: string; sac?: string; qty?: number; rate: number }>; supplierState?: string; placeOfSupply?: string }): Totals;
  export function invoiceNo(seq: number, date?: Date | string, prefix?: string): string;
  export function invoiceHTML(inv: InvoiceMeta, t: Totals, o?: { qrSvg?: string }): string;
  export function upiLink(o: { vpa: string; name: string; amountPaise: number; invoice: string }): string;
  export const fmt: (paise: number) => string;
}
