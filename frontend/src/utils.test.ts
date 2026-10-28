import { describe, expect, it } from 'vitest';
import { money, normalizeStatus, paymentBalance } from './utils';

describe('utilities de ComandaPro', () => {
  it('normaliza estados en español para clases de interfaz', () => {
    expect(normalizeStatus('EN_COCINA')).toBe('en-cocina');
    expect(normalizeStatus('PAGADA')).toBe('pagada');
    expect(normalizeStatus('STOCK_BAJO')).toBe('stock-bajo');
  });

  it('calcula pagos divididos y cierra solo cuando cubren el total', () => {
    expect(paymentBalance(250, [100, 75])).toEqual({ paid: 175, remaining: 75, closed: false });
    expect(paymentBalance(250, [100, 75, 75])).toEqual({ paid: 250, remaining: 0, closed: true });
  });

  it('formatea importes en moneda mexicana', () => {
    expect(money(125)).toContain('125.00');
    expect(money(undefined)).toContain('0.00');
  });
});
