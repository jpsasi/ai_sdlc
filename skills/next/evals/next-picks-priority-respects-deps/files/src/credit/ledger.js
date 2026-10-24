const entries = [];

export function addEntry(customerId, amountCents, date = new Date()) {
  entries.push({ customerId, amountCents, date });
}

export function entriesOf(customerId) {
  return entries.filter((e) => e.customerId === customerId);
}

export function reset() {
  entries.length = 0;
}
