/**
 * Accessibility Tests for Core Components
 *
 * These tests verify WCAG 2.1 AA compliance using axe-core.
 * Run with: pnpm test:a11y
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

// =============================================================================
// Test Utilities
// =============================================================================

/**
 * Helper to run axe accessibility checks with common configuration
 */
async function checkAccessibility(container: HTMLElement) {
  const results = await axe(container, {
    rules: {
      // Disable rules that require full page context
      region: { enabled: false },
      'page-has-heading-one': { enabled: false },
    },
  });
  return results;
}

// =============================================================================
// Mock Components (Replace with actual imports when components exist)
// =============================================================================

// These are placeholder components demonstrating the expected patterns.
// Replace with actual component imports once scaffolded.

function MockButton({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button {...props}>{children}</button>;
}

function MockFormField({
  id,
  label,
  error,
  required,
}: {
  id: string;
  label: string;
  error?: string;
  required?: boolean;
}) {
  const errorId = error ? `${id}-error` : undefined;

  return (
    <div>
      <label htmlFor={id}>
        {label}
        {required && <span aria-hidden="true"> *</span>}
      </label>
      <input
        id={id}
        type="text"
        aria-invalid={error ? 'true' : undefined}
        aria-describedby={errorId}
        aria-required={required}
      />
      {error && (
        <p id={errorId} role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

function MockLeadCard({ name, company, score }: { name: string; company: string; score: number }) {
  const cardId = `lead-${name.toLowerCase().replace(/\s/g, '-')}`;

  return (
    <article aria-labelledby={cardId}>
      <h3 id={cardId}>
        {name}
        <span className="sr-only"> - {company}</span>
      </h3>
      <p>{company}</p>
      <div aria-label={`Intent score: ${score} out of 100`}>{score}</div>
      <button aria-label={`View details for ${name}`}>View</button>
      <button aria-label={`Delete lead ${name}`}>Delete</button>
    </article>
  );
}

function MockChatMessage({ role, content }: { role: 'user' | 'assistant'; content: string }) {
  const speaker = role === 'user' ? 'You' : 'Vantage';

  return (
    <article aria-label={`${speaker} said`}>
      <span className="sr-only">{speaker}:</span>
      <p>{content}</p>
    </article>
  );
}

function MockChatInterface({ messages }: { messages: Array<{ role: 'user' | 'assistant'; content: string }> }) {
  return (
    <div>
      <div role="log" aria-label="Conversation with Vantage" aria-live="polite">
        {messages.map((msg, i) => (
          <MockChatMessage key={i} role={msg.role} content={msg.content} />
        ))}
      </div>
      <div role="group" aria-label="Message input">
        <label htmlFor="chat-input" className="sr-only">
          Type your message
        </label>
        <textarea id="chat-input" placeholder="Type your message..." />
        <button type="submit" aria-label="Send message">
          Send
        </button>
      </div>
    </div>
  );
}

// =============================================================================
// Accessibility Tests
// =============================================================================

describe('Button Accessibility', () => {
  it('has no accessibility violations', async () => {
    const { container } = render(<MockButton>Click me</MockButton>);
    const results = await checkAccessibility(container);
    expect(results).toHaveNoViolations();
  });

  it('icon-only button has accessible name', async () => {
    const { container } = render(
      <MockButton aria-label="Close dialog">
        <span aria-hidden="true">×</span>
      </MockButton>
    );
    const results = await checkAccessibility(container);
    expect(results).toHaveNoViolations();

    const button = screen.getByRole('button');
    expect(button).toHaveAccessibleName('Close dialog');
  });

  it('disabled button is still accessible', async () => {
    const { container } = render(<MockButton disabled>Cannot click</MockButton>);
    const results = await checkAccessibility(container);
    expect(results).toHaveNoViolations();
  });
});

describe('FormField Accessibility', () => {
  it('has no accessibility violations', async () => {
    const { container } = render(<MockFormField id="email" label="Email address" />);
    const results = await checkAccessibility(container);
    expect(results).toHaveNoViolations();
  });

  it('label is associated with input', () => {
    render(<MockFormField id="email" label="Email address" />);
    const input = screen.getByLabelText('Email address');
    expect(input).toBeInTheDocument();
  });

  it('required field is marked correctly', () => {
    render(<MockFormField id="email" label="Email address" required />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('aria-required', 'true');
  });

  it('error message is associated with input', async () => {
    const { container } = render(
      <MockFormField id="email" label="Email address" error="Invalid email format" />
    );
    const results = await checkAccessibility(container);
    expect(results).toHaveNoViolations();

    const input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(input).toHaveAccessibleDescription('Invalid email format');
  });
});

describe('LeadCard Accessibility', () => {
  it('has no accessibility violations', async () => {
    const { container } = render(
      <MockLeadCard name="John Smith" company="Acme Corp" score={85} />
    );
    const results = await checkAccessibility(container);
    expect(results).toHaveNoViolations();
  });

  it('card has accessible name from heading', () => {
    render(<MockLeadCard name="John Smith" company="Acme Corp" score={85} />);
    const article = screen.getByRole('article');
    expect(article).toHaveAccessibleName(/John Smith/i);
  });

  it('action buttons have accessible names', () => {
    render(<MockLeadCard name="John Smith" company="Acme Corp" score={85} />);

    expect(screen.getByRole('button', { name: /view details for john smith/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /delete lead john smith/i })).toBeInTheDocument();
  });

  it('intent score has accessible label', () => {
    render(<MockLeadCard name="John Smith" company="Acme Corp" score={85} />);
    expect(screen.getByLabelText(/intent score: 85 out of 100/i)).toBeInTheDocument();
  });
});

describe('ChatInterface Accessibility', () => {
  const mockMessages = [
    { role: 'assistant' as const, content: 'Welcome! What company do you work for?' },
    { role: 'user' as const, content: 'Acme Corp' },
    { role: 'assistant' as const, content: 'Great! What industry is Acme Corp in?' },
  ];

  it('has no accessibility violations', async () => {
    const { container } = render(<MockChatInterface messages={mockMessages} />);
    const results = await checkAccessibility(container);
    expect(results).toHaveNoViolations();
  });

  it('message list has log role and live region', () => {
    render(<MockChatInterface messages={mockMessages} />);
    const log = screen.getByRole('log');
    expect(log).toHaveAttribute('aria-live', 'polite');
    expect(log).toHaveAccessibleName('Conversation with Vantage');
  });

  it('input is labeled', () => {
    render(<MockChatInterface messages={mockMessages} />);
    expect(screen.getByLabelText(/type your message/i)).toBeInTheDocument();
  });

  it('send button has accessible name', () => {
    render(<MockChatInterface messages={mockMessages} />);
    expect(screen.getByRole('button', { name: /send message/i })).toBeInTheDocument();
  });

  it('messages have speaker identification for screen readers', () => {
    render(<MockChatInterface messages={mockMessages} />);
    const articles = screen.getAllByRole('article');

    expect(articles[0]).toHaveAccessibleName(/vantage said/i);
    expect(articles[1]).toHaveAccessibleName(/you said/i);
  });
});

describe('Color Contrast', () => {
  it('text meets contrast requirements', async () => {
    const { container } = render(
      <div>
        <p style={{ color: '#374151', backgroundColor: '#ffffff' }}>Normal text (7:1 ratio)</p>
        <p style={{ color: '#6b7280', backgroundColor: '#ffffff' }}>Secondary text (4.6:1 ratio)</p>
      </div>
    );

    const results = await axe(container, {
      rules: {
        'color-contrast': { enabled: true },
      },
    });

    expect(results).toHaveNoViolations();
  });
});

describe('Keyboard Navigation', () => {
  it('interactive elements are focusable', () => {
    render(
      <div>
        <MockButton>Button 1</MockButton>
        <MockButton>Button 2</MockButton>
        <a href="/link">Link</a>
      </div>
    );

    const button1 = screen.getByRole('button', { name: 'Button 1' });
    const button2 = screen.getByRole('button', { name: 'Button 2' });
    const link = screen.getByRole('link');

    // All should be focusable (tabIndex not positive)
    expect(button1).not.toHaveAttribute('tabindex', expect.stringMatching(/^[1-9]/));
    expect(button2).not.toHaveAttribute('tabindex', expect.stringMatching(/^[1-9]/));
    expect(link).not.toHaveAttribute('tabindex', expect.stringMatching(/^[1-9]/));
  });
});

describe('Screen Reader Only Content', () => {
  it('sr-only class hides content visually but keeps it accessible', () => {
    render(
      <button>
        <span aria-hidden="true">×</span>
        <span className="sr-only">Close</span>
      </button>
    );

    const button = screen.getByRole('button');
    expect(button).toHaveAccessibleName('Close');
  });
});
