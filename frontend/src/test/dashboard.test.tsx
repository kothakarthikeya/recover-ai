import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { formatCurrency, formatPercent, formatStrategy } from '../utils/formatters';
import { StatusBadge } from '../components/StatusBadge';
import { PipelineFunnel } from '../components/PipelineFunnel';

describe('RecoverAI Frontend UI & Formatter Unit Tests', () => {
  it('1. formatCurrency converts integer paise to Indian Rupee string correctly', () => {
    expect(formatCurrency(1250000)).toContain('12,500');
    expect(formatCurrency(100000)).toContain('1,000');
    expect(formatCurrency(0)).toContain('0.00');
  });

  it('2. formatPercent formats values to percentage string', () => {
    expect(formatPercent(0.745)).toBe('74.5%');
    expect(formatPercent(0.99)).toBe('99.0%');
  });

  it('3. formatStrategy maps enum values to human readable titles', () => {
    expect(formatStrategy('SMART_RETRY')).toBe('Smart Retry');
    expect(formatStrategy('PAYMENT_LINK')).toBe('Payment Link');
  });

  it('4. StatusBadge renders ALLOW policy decision badge', () => {
    render(<StatusBadge type="policy" value="ALLOW" />);
    expect(screen.getByText('Allowed')).toBeInTheDocument();
  });

  it('5. StatusBadge renders BLOCK policy decision badge', () => {
    render(<StatusBadge type="policy" value="BLOCK" />);
    expect(screen.getByText('Blocked')).toBeInTheDocument();
  });

  it('6. StatusBadge renders ESCALATE policy decision badge', () => {
    render(<StatusBadge type="policy" value="ESCALATE" />);
    expect(screen.getByText('Requires Approval')).toBeInTheDocument();
  });

  it('7. StatusBadge renders NO_ACTION policy decision badge', () => {
    render(<StatusBadge type="policy" value="NO_ACTION" />);
    expect(screen.getByText('No Action')).toBeInTheDocument();
  });

  it('8. StatusBadge renders SUCCESS attempt status badge', () => {
    render(<StatusBadge type="attempt" value="SUCCESS" />);
    expect(screen.getByText('Success')).toBeInTheDocument();
  });

  it('9. StatusBadge renders FAILED attempt status badge', () => {
    render(<StatusBadge type="attempt" value="FAILED" />);
    expect(screen.getByText('Failed')).toBeInTheDocument();
  });

  it('10. StatusBadge renders CRITICAL risk badge', () => {
    render(<StatusBadge type="risk" value="CRITICAL" />);
    expect(screen.getByText('CRITICAL')).toBeInTheDocument();
  });

  it('11. PipelineFunnel renders 7-stage recovery funnel', () => {
    const sampleStages = [
      { stage: 'DETECTED', count: 100, amount_paise: 1000000, amount_formatted: '₹10,000' },
      { stage: 'RISK_ANALYZED', count: 90, amount_paise: 900000, amount_formatted: '₹9,000' },
      { stage: 'AI_RECOMMENDED', count: 85, amount_paise: 850000, amount_formatted: '₹8,500' },
      { stage: 'POLICY_EVALUATED', count: 80, amount_paise: 800000, amount_formatted: '₹8,000' },
      { stage: 'ELIGIBLE', count: 75, amount_paise: 750000, amount_formatted: '₹7,500' },
      { stage: 'ATTEMPTED', count: 50, amount_paise: 500000, amount_formatted: '₹5,000' },
      { stage: 'RECOVERED', count: 30, amount_paise: 300000, amount_formatted: '₹3,000' },
    ];
    render(<PipelineFunnel stages={sampleStages} />);
    expect(screen.getByText('Recovery Pipeline Funnel')).toBeInTheDocument();
    expect(screen.getByText('DETECTED')).toBeInTheDocument();
    expect(screen.getByText('RECOVERED')).toBeInTheDocument();
  });
});
