# Accessibility Setup Guide

This document describes how to set up and run accessibility testing for the Vantage frontend.

## Required Dependencies

Add these dev dependencies to `apps/web/package.json`:

```bash
pnpm add -D \
  eslint-plugin-jsx-a11y \
  @axe-core/playwright \
  jest-axe \
  @types/jest-axe \
  @testing-library/jest-dom \
  @testing-library/react \
  @vitejs/plugin-react \
  vitest \
  jsdom
```

## Package.json Scripts

Add these scripts to `apps/web/package.json`:

```json
{
  "scripts": {
    "lint": "eslint . --ext .ts,.tsx --max-warnings 0",
    "lint:a11y": "eslint . --ext .ts,.tsx --rule 'jsx-a11y/alt-text: error' --rule 'jsx-a11y/aria-props: error'",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:a11y": "vitest run --config vitest.a11y.config.ts",
    "test:a11y:watch": "vitest --config vitest.a11y.config.ts"
  }
}
```

## CSS Setup

Import the accessibility utilities in your global CSS or layout:

```tsx
// app/layout.tsx
import '@/styles/accessibility.css';
```

Or in Tailwind CSS config, add the sr-only utilities:

```js
// tailwind.config.ts
module.exports = {
  theme: {
    extend: {},
  },
  plugins: [],
};
```

Note: Tailwind CSS already includes `sr-only` class by default.

## Running Tests

### Lint for Accessibility Issues

```bash
# Run ESLint with accessibility rules
pnpm lint

# Run accessibility-focused lint only
pnpm lint:a11y
```

### Run Accessibility Tests

```bash
# Run all accessibility tests
pnpm test:a11y

# Watch mode for development
pnpm test:a11y:watch
```

### CI/CD

The Lighthouse CI workflow (`.github/workflows/lighthouse.yml`) automatically:
- Builds the frontend
- Runs accessibility audits on key pages
- Fails the build if accessibility score < 90%
- Uploads reports as artifacts

## Writing Accessibility Tests

### Component Test Pattern

```tsx
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

it('has no accessibility violations', async () => {
  const { container } = render(<MyComponent />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

### Testing Accessible Names

```tsx
it('button has accessible name', () => {
  render(<IconButton icon={<TrashIcon />} aria-label="Delete item" />);
  expect(screen.getByRole('button')).toHaveAccessibleName('Delete item');
});
```

### Testing Form Labels

```tsx
it('input is labeled', () => {
  render(<FormField id="email" label="Email address" />);
  expect(screen.getByLabelText('Email address')).toBeInTheDocument();
});
```

## ESLint Rules Enabled

The `.eslintrc.js` enforces these critical accessibility rules:

| Rule | Severity | Description |
|------|----------|-------------|
| `jsx-a11y/alt-text` | Error | Images must have alt text |
| `jsx-a11y/anchor-has-content` | Error | Links must have content |
| `jsx-a11y/aria-props` | Error | ARIA attributes must be valid |
| `jsx-a11y/aria-role` | Error | ARIA roles must be valid |
| `jsx-a11y/click-events-have-key-events` | Error | Click handlers need keyboard events |
| `jsx-a11y/heading-has-content` | Error | Headings must have content |
| `jsx-a11y/html-has-lang` | Error | HTML must have lang attribute |
| `jsx-a11y/interactive-supports-focus` | Error | Interactive elements must be focusable |
| `jsx-a11y/label-has-associated-control` | Error | Labels must be associated with inputs |
| `jsx-a11y/no-static-element-interactions` | Error | Don't add handlers to non-interactive elements |
| `jsx-a11y/role-has-required-aria-props` | Error | Roles must have required ARIA props |
| `jsx-a11y/tabindex-no-positive` | Error | Don't use positive tabindex |

## Lighthouse Thresholds

The `lighthouserc.json` enforces:

| Category | Threshold | Action |
|----------|-----------|--------|
| Accessibility | 90% | Error (fails build) |
| Best Practices | 85% | Warning |
| Performance | 70% | Warning |
| SEO | 80% | Warning |

## Manual Testing Checklist

Before merging PRs with UI changes, verify:

- [ ] All interactive elements are keyboard accessible
- [ ] Focus indicator is visible on all focusable elements
- [ ] Screen reader announces content correctly (test with NVDA or VoiceOver)
- [ ] Color contrast meets 4.5:1 for normal text, 3:1 for large text
- [ ] Form errors are announced and associated with fields
- [ ] Dynamic content changes are announced via live regions

## Resources

- [WCAG 2.1 Quick Reference](https://www.w3.org/WAI/WCAG21/quickref/)
- [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [axe-core Rules](https://dequeuniversity.com/rules/axe/)
- [Testing Library Accessibility](https://testing-library.com/docs/dom-testing-library/api-accessibility/)
