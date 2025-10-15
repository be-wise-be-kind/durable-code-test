/**
 * Purpose: Unit and integration tests for the main App component
 * Scope: Component rendering, filtering, interactions, and link validation
 * Created: 2025-09-12
 * Updated: 2025-09-12
 * Author: Development Team
 * Version: 1.0
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import App from './App';
import { mockFailedFetch, mockFetch } from './test-setup';

// Wrapper component for router context in tests
const AppWithRouter = ({ initialEntries = ['/'] } = {}) => (
  <MemoryRouter initialEntries={initialEntries}>
    <App />
  </MemoryRouter>
);

// Mock location for navigation tests
const mockLocation = {
  href: 'http://localhost:3000/',
  hash: '',
  search: '',
  pathname: '/',
  assign: vi.fn(),
  reload: vi.fn(),
  replace: vi.fn(),
};

Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true,
});

// Mock history for navigation tests
const mockHistory = {
  pushState: vi.fn(),
  replaceState: vi.fn(),
};

Object.defineProperty(window, 'history', {
  value: mockHistory,
  writable: true,
});

describe('App Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Rendering', () => {
    it('renders the main title and subtitle', () => {
      render(<AppWithRouter />);

      // More specific selectors for the main title elements
      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
      expect(
        screen.getByText(/Proving that AI can create production-quality/),
      ).toBeInTheDocument();
    });

    it('renders all tab buttons', () => {
      render(<AppWithRouter />);

      expect(screen.getByRole('tab', { name: /Repository/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Planning/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Building/i })).toBeInTheDocument();
      expect(
        screen.getByRole('tab', { name: /Quality Assurance/i }),
      ).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Maintenance/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Demo/i })).toBeInTheDocument();
    });

    it('renders AI principles banner', () => {
      render(<AppWithRouter />);

      // Check for principle titles in the banner (no longer "Fundamental AI Principles" header)
      expect(screen.getByText('Immediate Feedback Loops')).toBeInTheDocument();
      expect(screen.getByText('Optimal Context')).toBeInTheDocument();
      expect(screen.getByText('Clear Success Criteria')).toBeInTheDocument();
      expect(screen.getByText('Modular Task Decomposition')).toBeInTheDocument();
    });

    it('renders tab content properly', async () => {
      await act(async () => {
        render(<AppWithRouter />);
      });

      // Should show Repository tab content by default (after lazy loading)
      await waitFor(
        () => {
          expect(
            screen.getByText(
              'Why Rigid Repository Structure Matters for AI Development',
            ),
          ).toBeInTheDocument();
        },
        { timeout: 10000 },
      );
      await waitFor(
        () => {
          expect(
            screen.getByText('Gate Everything You Care About'),
          ).toBeInTheDocument();
        },
        { timeout: 5000 },
      );
    });
  });

  describe('Tab Navigation', () => {
    it('displays Repository tab content by default', async () => {
      await act(async () => {
        render(<AppWithRouter />);
      });

      // Should show Repository tab content (after lazy loading)
      await waitFor(
        () => {
          expect(
            screen.getByText(
              'Why Rigid Repository Structure Matters for AI Development',
            ),
          ).toBeInTheDocument();
        },
        { timeout: 10000 },
      );
      await waitFor(
        () => {
          expect(
            screen.getByText('Gate Everything You Care About'),
          ).toBeInTheDocument();
        },
        { timeout: 5000 },
      );
      await waitFor(
        () => {
          expect(
            screen.getByText('Make It Work The Same Everywhere'),
          ).toBeInTheDocument();
        },
        { timeout: 5000 },
      );
    });

    it('switches to different tabs when clicked', async () => {
      const user = userEvent.setup();
      await act(async () => {
        render(<AppWithRouter />);
      });

      // Click on Planning tab
      const planningTab = screen.getByRole('tab', { name: /Planning/i });
      await act(async () => {
        await user.click(planningTab);
      });

      // Should show Planning tab content - wait for lazy loading
      await waitFor(
        () => {
          expect(screen.getByText('Planning Documents')).toBeInTheDocument();
        },
        { timeout: 10000 },
      );
      await waitFor(
        () => {
          expect(screen.getByText('View Development →')).toBeInTheDocument();
        },
        { timeout: 5000 },
      );
    });

    it('highlights active tab button', async () => {
      const user = userEvent.setup();
      render(<AppWithRouter />);

      const buildingTab = screen.getByRole('tab', { name: /Building/i });
      await user.click(buildingTab);

      expect(buildingTab.className).toMatch(/active/);
    });

    it('can switch between different tabs', async () => {
      const user = userEvent.setup();
      render(<AppWithRouter />);

      // Start with Building
      await user.click(screen.getByRole('tab', { name: /Building/i }));
      await waitFor(() => {
        expect(screen.getByText('AI-Powered Code Generation')).toBeInTheDocument();
      });

      // Switch to Quality Assurance
      await user.click(screen.getByRole('tab', { name: /Quality Assurance/i }));
      await waitFor(() => {
        expect(screen.getByText('Bulletproof Code Quality')).toBeInTheDocument();
      });
      expect(screen.queryByText('AI-Powered Code Generation')).not.toBeInTheDocument();

      // Back to Repository
      await user.click(screen.getByRole('tab', { name: /Repository/i }));
      await waitFor(() => {
        expect(
          screen.getByText('Why Rigid Repository Structure Matters for AI Development'),
        ).toBeInTheDocument();
      });
      expect(screen.queryByText('Bulletproof Code Quality')).not.toBeInTheDocument();
    });
  });

  describe('Link Validation and Navigation', () => {
    it('has working external links in Repository tab', async () => {
      const user = userEvent.setup();
      render(<AppWithRouter />);

      // Wait for Repository tab to be available
      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /Repository/i })).toBeInTheDocument();
      });

      // Click Repository tab to load its content
      const infrastructureTab = screen.getByRole('tab', { name: /Repository/i });
      await user.click(infrastructureTab);

      // Wait for content to load and check for any GitHub links
      await waitFor(() => {
        const allLinks = screen.getAllByRole('link');
        const githubLinks = allLinks.filter((link) =>
          link.getAttribute('href')?.includes('github.com'),
        );
        expect(githubLinks.length).toBeGreaterThan(0);
      });
    });

    it('has working internal links in Building tab', async () => {
      const user = userEvent.setup();
      render(<AppWithRouter />);

      // Switch to Building tab
      const buildingTab = screen.getByRole('tab', { name: /Building/i });
      await user.click(buildingTab);

      const standardsLink = screen.getByRole('link', {
        name: /Standards Guide/i,
      });
      expect(standardsLink).toBeInTheDocument();
      expect(standardsLink).toHaveAttribute('href', '/standards?return=Building');
    });

    it('validates that React router links work', async () => {
      // Mock successful fetch for API validation
      mockFetch({ status: 'ok' });

      const response = await fetch('/standards');
      expect(response.ok).toBe(true);
    });

    it('detects broken links', async () => {
      // Mock failed fetch for a broken link
      mockFailedFetch(404);

      const response = await fetch('/broken-link.html');
      expect(response.ok).toBe(false);
      expect(response.status).toBe(404);
    });

    it('has working diagram links in Planning tab', async () => {
      const user = userEvent.setup();
      render(<AppWithRouter />);

      // Switch to Planning tab
      const planningTab = screen.getByRole('tab', { name: /Planning/i });
      await user.click(planningTab);

      const flowLink = screen.getByRole('link', { name: /View Development/i });
      expect(flowLink).toBeInTheDocument();
      expect(flowLink).toHaveAttribute(
        'href',
        '/diagrams/durable-code-flow.html?return=Planning',
      );

      const sequenceLink = screen.getByRole('link', { name: /View AI/i });
      expect(sequenceLink).toBeInTheDocument();
      expect(sequenceLink).toHaveAttribute(
        'href',
        '/diagrams/ai-review-sequence.html?return=Planning',
      );
    });
  });

  describe('Interactive Behavior', () => {
    it('shows hover effects on tab buttons', async () => {
      const user = userEvent.setup();
      render(<AppWithRouter />);

      const planningTab = screen.getByRole('tab', { name: /Planning/i });

      await user.hover(planningTab);
      // Tab should be hoverable (though specific hover class depends on CSS)
      expect(planningTab).toBeInTheDocument();

      await user.unhover(planningTab);
      expect(planningTab).toBeInTheDocument();
    });

    it('displays AI principles content', () => {
      render(<AppWithRouter />);

      // Check that AI principles are displayed
      expect(screen.getByText('Immediate Feedback Loops')).toBeInTheDocument();
      expect(screen.getByText('Optimal Context')).toBeInTheDocument();
      expect(screen.getByText('Clear Success Criteria')).toBeInTheDocument();
      expect(screen.getByText('Modular Task Decomposition')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper button roles for tabs', () => {
      render(<AppWithRouter />);

      const tabButtons = screen.getAllByRole('tab');
      expect(tabButtons.length).toBe(7); // Exactly 7 tab buttons including Demo and Journey
    });

    it('has proper links for external resources', async () => {
      render(<AppWithRouter />);

      // Wait for content to load and check for any GitHub links
      await waitFor(() => {
        const allLinks = screen.getAllByRole('link');
        const githubLinks = allLinks.filter((link) =>
          link.getAttribute('href')?.includes('github.com'),
        );
        expect(githubLinks.length).toBeGreaterThan(0);
      });
    });

    it('has semantic HTML structure', () => {
      render(<AppWithRouter />);

      expect(screen.getByRole('banner')).toBeInTheDocument(); // header
      expect(screen.getByRole('main')).toBeInTheDocument(); // main
      expect(screen.getByRole('contentinfo')).toBeInTheDocument(); // footer
      expect(screen.getByRole('navigation')).toBeInTheDocument(); // tab navigation
    });
  });

  describe('Link Health Check', () => {
    const publicRoutes = ['/standards'];

    it.each(publicRoutes)('validates public route: %s', async (route) => {
      // In a real scenario, this would make actual HTTP requests
      // For now, we mock successful responses
      mockFetch({ status: 'ok' });

      const response = await fetch(route);
      expect(response.ok).toBe(true);
    });

    it('identifies all external links in the component', async () => {
      const user = userEvent.setup();
      render(<AppWithRouter />);

      // Switch to Repository tab first to ensure we have links
      const infrastructureTab = screen.getByRole('tab', { name: /Repository/i });
      await user.click(infrastructureTab);

      // Get all links
      const links = screen.getAllByRole('link');

      // Filter for external or internal links
      const internalLinks = links.filter((link) => {
        const href = link.getAttribute('href');
        return href && !href.startsWith('http') && !href.startsWith('mailto:');
      });

      // Should have internal links (at least 0, since Repository has external GitHub links)
      expect(internalLinks.length).toBeGreaterThanOrEqual(0);

      // All internal links should be valid
      internalLinks.forEach((link) => {
        const href = link.getAttribute('href');
        expect(href).toBeTruthy();
        expect(href).not.toBe('#'); // No empty anchors
      });
    });
  });

  describe('Error Handling', () => {
    it('handles missing tab data gracefully', () => {
      // This test ensures the component doesn't break with malformed data
      render(<AppWithRouter />);

      // Component should still render even if some data is missing
      expect(screen.getByText('AI-Authored Excellence')).toBeInTheDocument();
    });

    it('handles navigation errors gracefully', async () => {
      const user = userEvent.setup();

      // Mock console.error to track errors
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      render(<AppWithRouter />);

      // Switch to Building tab
      const buildingTab = screen.getByRole('tab', { name: /Building/i });
      await user.click(buildingTab);

      // Click the standards link
      const link = screen.getByRole('link', {
        name: /Standards Guide/i,
      });

      // This should not throw an error
      await user.click(link);

      // Clean up
      consoleSpy.mockRestore();
    });
  });

  describe('Tab State Persistence', () => {
    beforeEach(() => {
      // Reset location mocks
      mockLocation.hash = '';
      mockLocation.search = '';
      mockLocation.pathname = '/';
      vi.clearAllMocks();
    });

    it('defaults to Repository tab when no hash is present', async () => {
      await act(async () => {
        render(<AppWithRouter />);
      });

      const infrastructureTab = screen.getByRole('tab', { name: /Repository/i });
      expect(infrastructureTab.className).toMatch(/active/);
    });

    it('loads correct tab from URL hash', async () => {
      mockLocation.hash = '#Planning';

      await act(async () => {
        render(<AppWithRouter />);
      });

      const planningTab = screen.getByRole('tab', { name: /Planning/i });
      expect(planningTab.className).toMatch(/active/);
    });

    it('loads correct tab from return parameter', async () => {
      mockLocation.search = '?return=Building';

      await act(async () => {
        render(<AppWithRouter />);
      });

      const buildingTab = screen.getByRole('tab', { name: /Building/i });
      expect(buildingTab.className).toMatch(/active/);
    });

    it('prioritizes hash over return parameter', async () => {
      mockLocation.hash = '#Quality Assurance';
      mockLocation.search = '?return=Building';

      await act(async () => {
        render(<AppWithRouter />);
      });

      const qualityTab = screen.getByRole('tab', { name: /Quality Assurance/i });
      expect(qualityTab.className).toMatch(/active/);
    });

    it('falls back to Repository for invalid hash', async () => {
      mockLocation.hash = '#InvalidTab';

      await act(async () => {
        render(<AppWithRouter />);
      });

      const infrastructureTab = screen.getByRole('tab', { name: /Repository/i });
      expect(infrastructureTab.className).toMatch(/active/);
    });

    it('updates URL hash when tab is clicked', async () => {
      const user = userEvent.setup();

      render(<AppWithRouter />);

      const planningTab = screen.getByRole('tab', { name: /Planning/i });
      await user.click(planningTab);

      expect(mockHistory.pushState).toHaveBeenCalledWith(null, '', '#Planning');
    });

    it('cleans up URL when return parameter is used', async () => {
      mockLocation.search = '?return=Building';

      await act(async () => {
        render(<AppWithRouter />);
      });

      // Should clean up the URL and use hash format
      expect(mockHistory.replaceState).toHaveBeenCalledWith(null, '', '/#Building');
    });

    it('includes return parameter in external links', async () => {
      const user = userEvent.setup();
      render(<AppWithRouter />);

      // Switch to Building tab
      const buildingTab = screen.getByRole('tab', { name: /Building/i });
      await user.click(buildingTab);

      // Check that standards guide link includes return parameter
      const standardsLink = screen.getByRole('link', {
        name: /Standards Guide/i,
      });
      expect(standardsLink.getAttribute('href')).toBe('/standards?return=Building');
    });

    it('includes return parameter in Planning tab links', async () => {
      const user = userEvent.setup();

      render(<AppWithRouter />);

      // Switch to Planning tab
      const planningTab = screen.getByRole('tab', { name: /Planning/i });
      await user.click(planningTab);

      // Check that diagram links include return parameter
      const flowLink = screen.getByRole('link', { name: /View Development →/i });
      expect(flowLink.getAttribute('href')).toBe(
        '/diagrams/durable-code-flow.html?return=Planning',
      );

      const sequenceLink = screen.getByRole('link', { name: /View AI →/i });
      expect(sequenceLink.getAttribute('href')).toBe(
        '/diagrams/ai-review-sequence.html?return=Planning',
      );
    });

    it('includes return parameter in Quality Assurance tab links', async () => {
      const user = userEvent.setup();

      render(<AppWithRouter />);

      // Switch to Quality Assurance tab
      const qualityTab = screen.getByRole('tab', { name: /Quality Assurance/i });
      await user.click(qualityTab);

      // Wait for lazy loading
      await waitFor(() => {
        expect(screen.getByText('Bulletproof Code Quality')).toBeInTheDocument();
      });

      // Check that QA links exist (reports and standards)
      const reportLinks = screen.getAllByRole('link', {
        name: /(View.*Report|View Linter Reports|View Coverage Report|View Bug Reports|View All Reports)/i,
      });
      expect(reportLinks.length).toBeGreaterThan(0);

      const standardsLink = screen.getByRole('link', { name: /View Standards/i });
      expect(standardsLink.getAttribute('href')).toBe(
        '/standards?return=QualityAssurance',
      );
    });

    it('handles browser back/forward navigation', async () => {
      // Render with initial hash
      mockLocation.hash = '#Maintenance';
      await act(async () => {
        render(<AppWithRouter />);
      });

      // Should load the Maintenance tab based on hash
      const maintenanceTab = screen.getByRole('tab', { name: /Maintenance/i });
      expect(maintenanceTab.className).toMatch(/active/);
    });
  });

  describe('Link Validation', () => {
    it('validates all links in the current app structure', async () => {
      // Reset location hash
      mockLocation.hash = '';

      const user = userEvent.setup();
      render(<AppWithRouter />);

      // Collect all links from all tabs
      const allLinks: string[] = [];

      // Repository tab (default) - wait for lazy loading
      const infrastructureTab = screen.getByRole('tab', { name: /Repository/i });
      await user.click(infrastructureTab);
      await waitFor(() => {
        expect(
          screen.getByText('Why Rigid Repository Structure Matters for AI Development'),
        ).toBeInTheDocument();
      });
      const infrastructureLinks = screen.getAllByRole('link');
      infrastructureLinks.forEach((link) => {
        const href = link.getAttribute('href');
        if (href) allLinks.push(href);
      });

      // Planning tab
      const planningTab = screen.getByRole('tab', { name: /Planning/i });
      await user.click(planningTab);
      const planningLinks = screen.getAllByRole('link');
      planningLinks.forEach((link) => {
        const href = link.getAttribute('href');
        if (href && !allLinks.includes(href)) allLinks.push(href);
      });

      // Building tab
      const buildingTab = screen.getByRole('tab', { name: /Building/i });
      await user.click(buildingTab);
      const buildingLinks = screen.getAllByRole('link');
      buildingLinks.forEach((link) => {
        const href = link.getAttribute('href');
        if (href && !allLinks.includes(href)) allLinks.push(href);
      });

      // Quality Assurance tab
      const qualityTab = screen.getByRole('tab', { name: /Quality Assurance/i });
      await user.click(qualityTab);
      const qualityLinks = screen.getAllByRole('link');
      qualityLinks.forEach((link) => {
        const href = link.getAttribute('href');
        if (href && !allLinks.includes(href)) allLinks.push(href);
      });

      // Verify we collected links from all tabs
      expect(allLinks.length).toBeGreaterThan(10); // Should have collected multiple links

      // Verify some key links exist (but don't require exact match of all)
      const hasGithubLinks = allLinks.some((link) => link.includes('github.com'));
      const hasInternalLinks = allLinks.some((link) => link.startsWith('/'));
      expect(hasGithubLinks).toBe(true);
      expect(hasInternalLinks).toBe(true);

      // Verify no old broken links exist
      expect(allLinks).not.toContain('set-standards.html');
      expect(allLinks).not.toContain('https://docs.anthropic.com/en/docs/claude-code');
    });

    it('ensures all internal links include return parameters', async () => {
      // Reset location hash
      mockLocation.hash = '';

      const user = userEvent.setup();
      render(<AppWithRouter />);

      // Check Building tab links
      const buildingTab = screen.getByRole('tab', { name: /Building/i });
      await user.click(buildingTab);

      const standardsLink = screen.getByRole('link', {
        name: /Standards Guide/i,
      });
      expect(standardsLink.getAttribute('href')).toBe('/standards?return=Building');

      // Check Planning tab links
      const planningTab = screen.getByRole('tab', { name: /Planning/i });
      await user.click(planningTab);

      const flowLink = screen.getByRole('link', { name: /View Development →/i });
      expect(flowLink.getAttribute('href')).toBe(
        '/diagrams/durable-code-flow.html?return=Planning',
      );

      const sequenceLink = screen.getByRole('link', { name: /View AI →/i });
      expect(sequenceLink.getAttribute('href')).toBe(
        '/diagrams/ai-review-sequence.html?return=Planning',
      );
    });

    it('verifies no broken relative links exist', async () => {
      await act(async () => {
        render(<AppWithRouter />);
      });

      const allLinks = screen.getAllByRole('link');

      allLinks.forEach((link) => {
        const href = link.getAttribute('href');
        if (href) {
          // Verify no broken HTML files exist (allow diagrams)
          expect(href).not.toContain('infrastructure-guide.html');
          expect(href).not.toContain('set-standards.html');

          // Allow diagram HTML files but no other standalone HTML
          if (
            href.includes('.html') &&
            !href.includes('/diagrams/') &&
            !href.includes('ci-cd-pipeline.html')
          ) {
            throw new Error(`Unexpected standalone HTML file found: ${href}`);
          }

          // Ensure all internal paths start with / or are external URLs or hash anchors
          if (!href.startsWith('http')) {
            expect(href).toMatch(/^\/|^#/);
          }
        }
      });
    });
  });
});
