# React Frontend Upgrade - PR Breakdown

## Overview
This document breaks down the React frontend upgrade into manageable, atomic PRs. Each PR is designed to be:
- Self-contained and shippable
- Maintains a working application
- Testable independently
- Revertible if needed

---

## PR1: TypeScript Configuration and Development Tooling

### Context
Before any refactoring, we need proper TypeScript configuration and development tooling. This PR establishes the foundation for type safety and better developer experience without changing any application code.

### Instructions
1. **Update TypeScript Configuration**
   ```json
   // tsconfig.json
   {
     "compilerOptions": {
       "strict": true,
       "noUnusedLocals": true,
       "noUnusedParameters": true,
       "noImplicitReturns": true,
       "noFallthroughCasesInSwitch": true,
       "forceConsistentCasingInFileNames": true,
       "esModuleInterop": true,
       "skipLibCheck": true,
       "paths": {
         "@/*": ["./src/*"],
         "@components/*": ["./src/components/*"],
         "@features/*": ["./src/features/*"],
         "@hooks/*": ["./src/hooks/*"],
         "@services/*": ["./src/services/*"],
         "@utils/*": ["./src/utils/*"],
         "@types/*": ["./src/types/*"]
       }
     }
   }
   ```

2. **Update Vite Configuration for Path Aliases**
   ```typescript
   // vite.config.ts
   import { defineConfig } from 'vite'
   import react from '@vitejs/plugin-react'
   import path from 'path'

   export default defineConfig({
     plugins: [react()],
     resolve: {
       alias: {
         '@': path.resolve(__dirname, './src'),
         '@components': path.resolve(__dirname, './src/components'),
         '@features': path.resolve(__dirname, './src/features'),
         '@hooks': path.resolve(__dirname, './src/hooks'),
         '@services': path.resolve(__dirname, './src/services'),
         '@utils': path.resolve(__dirname, './src/utils'),
         '@types': path.resolve(__dirname, './src/types')
       }
     }
   })
   ```

3. **Fix TypeScript Errors**
   - Add missing type annotations
   - Fix strict mode violations
   - Add proper return types
   - Remove unused variables

4. **Update ESLint Configuration**
   - Add React best practices rules
   - Configure import ordering
   - Add accessibility rules

5. **Add Development Scripts**
   ```json
   // package.json scripts
   {
     "typecheck": "tsc --noEmit",
     "lint:fix": "eslint . --fix",
     "format": "prettier --write .",
     "validate": "npm run typecheck && npm run lint && npm run test:run"
   }
   ```

### Success Criteria
- [ ] TypeScript strict mode enabled with zero errors
- [ ] Path aliases working in both TypeScript and Vite
- [ ] All existing tests still pass
- [ ] Application builds and runs without errors
- [ ] ESLint configured with zero violations
- [ ] New validate script passes

### Files Changed
- `tsconfig.json`
- `tsconfig.app.json`
- `vite.config.ts`
- `eslint.config.js`
- `package.json`
- Various `.tsx` files (type annotations only)

---

## PR2: State Management Foundation (Zustand + React Query)

### Context
Introduce proper state management before refactoring components. This allows us to extract business logic from components in subsequent PRs.

### Instructions
1. **Install Dependencies**
   ```bash
   npm install zustand @tanstack/react-query @tanstack/react-query-devtools
   ```

2. **Create Store Structure**
   ```
   src/store/
   ├── index.ts
   ├── appStore.ts         # Global app state
   ├── navigationStore.ts  # Tab navigation state
   └── demoStore.ts       # Demo/oscilloscope state
   ```

3. **Implement App Store**
   ```typescript
   // src/store/appStore.ts
   import { create } from 'zustand'
   import { devtools } from 'zustand/middleware'

   interface AppState {
     theme: 'light' | 'dark'
     isLoading: boolean
     error: string | null
     setTheme: (theme: 'light' | 'dark') => void
     setLoading: (loading: boolean) => void
     setError: (error: string | null) => void
   }

   export const useAppStore = create<AppState>()(
     devtools(
       (set) => ({
         theme: 'light',
         isLoading: false,
         error: null,
         setTheme: (theme) => set({ theme }),
         setLoading: (isLoading) => set({ isLoading }),
         setError: (error) => set({ error })
       }),
       { name: 'app-store' }
     )
   )
   ```

4. **Implement Navigation Store**
   ```typescript
   // src/store/navigationStore.ts
   export const useNavigationStore = create<NavigationState>()(
     devtools(
       (set, get) => ({
         activeTab: 'Infrastructure',
         tabHistory: [],
         setActiveTab: (tab) => {
           const { tabHistory } = get()
           set({
             activeTab: tab,
             tabHistory: [...tabHistory, tab]
           })
           window.history.pushState(null, '', `#${tab}`)
         }
       })
     )
   )
   ```

5. **Setup React Query**
   ```typescript
   // src/app/AppProviders.tsx
   import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
   import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

   const queryClient = new QueryClient({
     defaultOptions: {
       queries: {
         staleTime: 1000 * 60 * 5, // 5 minutes
         gcTime: 1000 * 60 * 10,   // 10 minutes
         retry: 3,
         refetchOnWindowFocus: false
       }
     }
   })

   export function AppProviders({ children }: { children: React.ReactNode }) {
     return (
       <QueryClientProvider client={queryClient}>
         {children}
         <ReactQueryDevtools initialIsOpen={false} />
       </QueryClientProvider>
     )
   }
   ```

6. **Migrate Tab State to Store**
   - Replace useState in App.tsx with useNavigationStore
   - Keep all existing functionality
   - Ensure URL sync still works

### Success Criteria
- [ ] Zustand stores created and working
- [ ] React Query configured
- [ ] Tab navigation using store instead of local state
- [ ] Browser back/forward still works
- [ ] URL hash sync maintained
- [ ] React Query DevTools visible in development
- [ ] All tests updated and passing

### Files Changed
- `package.json`
- `src/store/` (new directory)
- `src/app/AppProviders.tsx` (new)
- `src/main.tsx` (wrap with providers)
- `src/App.tsx` (use store instead of useState)

---

## PR3: Component Architecture - Common Components Library

### Context
Create a library of reusable components to replace inline JSX and establish consistent patterns.

### Instructions
1. **Create Component Structure Template**
   ```
   src/components/common/Button/
   ├── Button.tsx
   ├── Button.module.css
   ├── Button.test.tsx
   ├── Button.types.ts
   └── index.ts
   ```

2. **Extract Common Components**

   **Button Component:**
   ```typescript
   // src/components/common/Button/Button.tsx
   import React from 'react'
   import styles from './Button.module.css'
   import { ButtonProps } from './Button.types'

   export const Button = React.memo<ButtonProps>(({
     children,
     variant = 'primary',
     size = 'medium',
     disabled = false,
     onClick,
     ...rest
   }) => {
     return (
       <button
         className={`${styles.button} ${styles[variant]} ${styles[size]}`}
         disabled={disabled}
         onClick={onClick}
         {...rest}
       >
         {children}
       </button>
     )
   })

   Button.displayName = 'Button'
   ```

3. **Create These Common Components:**
   - `Button` - Replace all button elements
   - `Card` - For infrastructure cards, principle cards
   - `Tab` - For tab navigation buttons
   - `Section` - For content sections
   - `Icon` - For emoji icons with proper accessibility
   - `Link` - Smart link component (internal/external)
   - `Badge` - For status badges
   - `LoadingSpinner` - Loading states
   - `ErrorMessage` - Error display

4. **Replace Inline Elements**
   - Find all `<button>` tags and replace with `<Button>`
   - Find all card-like divs and replace with `<Card>`
   - Extract inline styles to CSS modules

5. **Add Tests for Each Component**
   ```typescript
   // src/components/common/Button/Button.test.tsx
   import { describe, it, expect, vi } from 'vitest'
   import { render, screen } from '@testing-library/react'
   import userEvent from '@testing-library/user-event'
   import { Button } from './Button'

   describe('Button', () => {
     it('renders children correctly', () => {
       render(<Button>Click me</Button>)
       expect(screen.getByRole('button')).toHaveTextContent('Click me')
     })

     it('handles click events', async () => {
       const handleClick = vi.fn()
       const user = userEvent.setup()
       render(<Button onClick={handleClick}>Click</Button>)
       await user.click(screen.getByRole('button'))
       expect(handleClick).toHaveBeenCalledTimes(1)
     })
   })
   ```

### Success Criteria
- [ ] All common components created with TypeScript
- [ ] CSS Modules implemented for each component
- [ ] 100% test coverage for common components
- [ ] All inline buttons replaced with Button component
- [ ] All inline styles moved to CSS modules
- [ ] No visual regression (app looks the same)
- [ ] Components are properly memoized

### Files Changed
- `src/components/common/` (new directory with ~10 components)
- `src/App.tsx` (use new components)
- `src/components/tabs/*.tsx` (use new components)
- `package.json` (if adding CSS modules support)

---

## PR4: Feature Modularization - Extract Infrastructure Feature

### Context
Begin breaking down the monolithic structure by extracting the first feature module. Infrastructure is a good starting point as it's relatively self-contained.

### Instructions
1. **Create Feature Structure**
   ```
   src/features/infrastructure/
   ├── components/
   │   ├── InfrastructureTab/
   │   │   ├── InfrastructureTab.tsx
   │   │   ├── InfrastructureTab.module.css
   │   │   └── InfrastructureTab.test.tsx
   │   ├── InfrastructureCard/
   │   └── FolderStructure/
   ├── hooks/
   │   └── useInfrastructure.ts
   ├── types/
   │   └── infrastructure.types.ts
   └── index.ts
   ```

2. **Break Down InfrastructureTab**
   - Extract the hero section
   - Extract infrastructure cards grid
   - Extract folder structure display
   - Create proper TypeScript interfaces

3. **Create Dedicated Hook**
   ```typescript
   // src/features/infrastructure/hooks/useInfrastructure.ts
   export function useInfrastructure() {
     const infrastructureItems = [
       {
         id: 'custom-linters',
         icon: '🔧',
         title: 'Custom Linters',
         description: '...',
         badge: 'Critical',
         link: 'https://github.com/...'
       },
       // ... other items
     ]

     return {
       items: infrastructureItems,
       folderStructure: getFolderStructure()
     }
   }
   ```

4. **Implement Lazy Loading**
   ```typescript
   // src/app/App.tsx
   const InfrastructureTab = lazy(() =>
     import('@features/infrastructure').then(m => ({
       default: m.InfrastructureTab
     }))
   )
   ```

### Success Criteria
- [ ] Infrastructure feature fully modularized
- [ ] Component size < 150 lines each
- [ ] Lazy loading implemented
- [ ] All infrastructure tests passing
- [ ] No change in functionality
- [ ] Clear separation of concerns

### Files Changed
- `src/features/infrastructure/` (new directory)
- `src/components/tabs/InfrastructureTab.tsx` (deleted)
- `src/App.tsx` (import from features)
- `src/App.css` (styles moved to modules)

---

## PR5: Feature Modularization - Extract Demo Feature with WebSocket Service

### Context
The Demo tab is the most complex component (707 lines). Extract it properly with separated concerns for WebSocket, canvas rendering, and controls.

### Instructions
1. **Create Feature Structure**
   ```
   src/features/demo/
   ├── components/
   │   ├── DemoTab/
   │   ├── Oscilloscope/
   │   │   ├── OscilloscopeCanvas.tsx
   │   │   ├── OscilloscopeCanvas.module.css
   │   │   └── useCanvas.ts
   │   ├── ControlPanel/
   │   │   ├── ControlPanel.tsx
   │   │   ├── WaveformSelector.tsx
   │   │   └── ParameterControls.tsx
   │   └── StatusPanel/
   ├── hooks/
   │   ├── useWebSocket.ts
   │   ├── useOscilloscope.ts
   │   └── useWaveformData.ts
   ├── services/
   │   └── websocketService.ts
   ├── types/
   │   └── oscilloscope.types.ts
   └── constants/
       └── oscilloscope.constants.ts
   ```

2. **Extract WebSocket Service**
   ```typescript
   // src/features/demo/services/websocketService.ts
   export class WebSocketService {
     private ws: WebSocket | null = null
     private listeners: Map<string, Set<Function>> = new Map()

     connect(url: string): Promise<void> {
       return new Promise((resolve, reject) => {
         this.ws = new WebSocket(url)
         this.ws.onopen = () => resolve()
         this.ws.onerror = reject
         this.ws.onmessage = this.handleMessage.bind(this)
       })
     }

     send(data: any): void {
       if (this.ws?.readyState === WebSocket.OPEN) {
         this.ws.send(JSON.stringify(data))
       }
     }

     on(event: string, callback: Function): void {
       if (!this.listeners.has(event)) {
         this.listeners.set(event, new Set())
       }
       this.listeners.get(event)!.add(callback)
     }

     private handleMessage(event: MessageEvent): void {
       const data = JSON.parse(event.data)
       this.emit('data', data)
     }
   }
   ```

3. **Create Custom Hooks**
   ```typescript
   // src/features/demo/hooks/useWebSocket.ts
   export function useWebSocket(url: string) {
     const [isConnected, setIsConnected] = useState(false)
     const [error, setError] = useState<Error | null>(null)
     const serviceRef = useRef<WebSocketService>()

     useEffect(() => {
       serviceRef.current = new WebSocketService()

       serviceRef.current.connect(url)
         .then(() => setIsConnected(true))
         .catch(setError)

       return () => {
         serviceRef.current?.disconnect()
       }
     }, [url])

     return {
       isConnected,
       error,
       send: serviceRef.current?.send.bind(serviceRef.current),
       on: serviceRef.current?.on.bind(serviceRef.current)
     }
   }
   ```

4. **Separate Canvas Logic**
   ```typescript
   // src/features/demo/components/Oscilloscope/useCanvas.ts
   export function useCanvas(
     drawFunction: (ctx: CanvasRenderingContext2D) => void
   ) {
     const canvasRef = useRef<HTMLCanvasElement>(null)
     const animationIdRef = useRef<number>()

     useEffect(() => {
       const canvas = canvasRef.current
       if (!canvas) return

       const ctx = canvas.getContext('2d')
       if (!ctx) return

       const render = () => {
         drawFunction(ctx)
         animationIdRef.current = requestAnimationFrame(render)
       }

       render()

       return () => {
         if (animationIdRef.current) {
           cancelAnimationFrame(animationIdRef.current)
         }
       }
     }, [drawFunction])

     return canvasRef
   }
   ```

5. **Break Down Components**
   - OscilloscopeCanvas: Just canvas rendering
   - ControlPanel: All controls
   - WaveformSelector: Wave type selection
   - ParameterControls: Sliders and inputs
   - StatusPanel: Connection and data status

### Success Criteria
- [ ] Demo feature fully modularized
- [ ] WebSocket logic completely separated
- [ ] Each component < 150 lines
- [ ] Canvas rendering optimized
- [ ] All controls working as before
- [ ] WebSocket reconnection logic improved
- [ ] Tests for all new components

### Files Changed
- `src/features/demo/` (new directory)
- `src/components/tabs/DemoTab.tsx` (deleted)
- `src/App.tsx` (import from features)

---

## PR6: Feature Modularization - Remaining Tabs

### Context
Complete the feature modularization by extracting Planning, Building, Quality Assurance, and Maintenance tabs.

### Instructions
1. **Create Feature Structures**
   ```
   src/features/
   ├── planning/
   ├── building/
   ├── quality/
   └── maintenance/
   ```

2. **Apply Same Pattern**
   - Break down large components
   - Extract business logic to hooks
   - Move styles to CSS modules
   - Add proper TypeScript types

3. **Share Common Logic**
   ```typescript
   // src/features/shared/hooks/useTabContent.ts
   export function useTabContent(tabName: string) {
     const { data, isLoading } = useQuery({
       queryKey: ['tab-content', tabName],
       queryFn: () => fetchTabContent(tabName)
     })

     return { data, isLoading }
   }
   ```

### Success Criteria
- [ ] All tabs extracted to features
- [ ] No components > 150 lines
- [ ] Shared logic properly abstracted
- [ ] All tests passing
- [ ] Lazy loading for all features

### Files Changed
- `src/features/` (4 new feature directories)
- `src/components/tabs/` (directory removed)
- `src/App.tsx` (updated imports)

---

## PR7: App Shell Refactoring

### Context
Now that features are modularized, refactor the main App.tsx from 409 lines to a clean shell.

### Instructions
1. **Split App.tsx Into:**
   ```
   src/app/
   ├── App.tsx (< 50 lines)
   ├── AppShell.tsx
   ├── AppProviders.tsx
   ├── AppRouter.tsx
   └── AppErrorBoundary.tsx
   ```

2. **Create App Shell**
   ```typescript
   // src/app/AppShell.tsx
   export function AppShell({ children }: { children: ReactNode }) {
     return (
       <div className={styles.app}>
         <ParticleBackground />
         <Header />
         <Navigation />
         <main className={styles.main}>
           <Suspense fallback={<LoadingSpinner />}>
             {children}
           </Suspense>
         </main>
         <Footer />
       </div>
     )
   }
   ```

3. **Extract Components:**
   - HeroSection component
   - PrinciplesSection component
   - Navigation component
   - Footer component

4. **Implement Error Boundary**
   ```typescript
   // src/app/AppErrorBoundary.tsx
   export class AppErrorBoundary extends Component {
     state = { hasError: false, error: null }

     static getDerivedStateFromError(error: Error) {
       return { hasError: true, error }
     }

     render() {
       if (this.state.hasError) {
         return <ErrorFallback error={this.state.error} />
       }
       return this.props.children
     }
   }
   ```

### Success Criteria
- [ ] App.tsx < 50 lines
- [ ] Clean separation of concerns
- [ ] Error boundary implemented
- [ ] Loading states for all async content
- [ ] All functionality preserved

### Files Changed
- `src/App.tsx` (reduced to shell)
- `src/app/` (new components)
- `src/components/layout/` (Header, Footer, Navigation)

---

## PR8: Styling System and Theme

### Context
Replace inline styles and massive CSS files with a proper styling system.

### Instructions
1. **Create Theme System**
   ```
   src/styles/
   ├── theme/
   │   ├── colors.css
   │   ├── typography.css
   │   ├── spacing.css
   │   ├── breakpoints.css
   │   └── index.css
   ├── global.css
   └── reset.css
   ```

2. **Define CSS Variables**
   ```css
   /* src/styles/theme/colors.css */
   :root {
     /* Primary colors */
     --color-primary-50: #f4e8d0;
     --color-primary-100: #e8d5b7;
     --color-primary-200: #ddc7a0;
     --color-primary-300: #d4af37;
     --color-primary-400: #b8860b;
     --color-primary-500: #8b6341;

     /* Semantic colors */
     --color-background: var(--color-primary-50);
     --color-surface: #ffffff;
     --color-text-primary: #3c2414;
     --color-text-secondary: #654321;

     /* Component tokens */
     --button-bg-primary: var(--color-primary-300);
     --button-bg-hover: var(--color-primary-400);
   }
   ```

3. **Migrate Styles**
   - Convert App.css to modules
   - Extract component styles
   - Remove all inline styles
   - Use CSS variables consistently

4. **Implement Dark Mode (Optional)**
   ```css
   [data-theme="dark"] {
     --color-background: #1a1a1a;
     --color-surface: #2a2a2a;
     --color-text-primary: #f4e8d0;
   }
   ```

### Success Criteria
- [ ] All inline styles removed
- [ ] CSS modules for all components
- [ ] Consistent theme variables
- [ ] App.css < 200 lines
- [ ] No style conflicts
- [ ] Responsive design maintained

### Files Changed
- `src/styles/` (new directory)
- `src/App.css` (significantly reduced)
- All component files (inline styles removed)

---

## PR9: Performance Optimization

### Context
Implement performance best practices now that architecture is clean.

### Instructions
1. **Add Memoization**
   ```typescript
   // Wrap components with React.memo
   export const Card = React.memo<CardProps>(({ ... }) => {
     // ...
   })

   // Use useMemo for expensive computations
   const processedData = useMemo(() =>
     expensiveProcessing(data), [data]
   )

   // Use useCallback for event handlers
   const handleClick = useCallback((e) => {
     // ...
   }, [dependency])
   ```

2. **Implement Code Splitting**
   ```typescript
   // Route-based splitting
   const Standards = lazy(() => import('@pages/Standards'))
   const CustomLinters = lazy(() => import('@pages/CustomLinters'))
   ```

3. **Optimize Bundle**
   - Analyze bundle with `vite-bundle-visualizer`
   - Remove unused dependencies
   - Tree-shake properly
   - Use dynamic imports

4. **Add Performance Monitoring**
   ```typescript
   // src/utils/performance.ts
   export function measureComponentPerf(componentName: string) {
     if (process.env.NODE_ENV === 'development') {
       performance.mark(`${componentName}-start`)
       return () => {
         performance.mark(`${componentName}-end`)
         performance.measure(
           componentName,
           `${componentName}-start`,
           `${componentName}-end`
         )
       }
     }
     return () => {}
   }
   ```

### Success Criteria
- [ ] Lighthouse score > 95
- [ ] Bundle size < 200KB gzipped
- [ ] No unnecessary re-renders
- [ ] First Contentful Paint < 1.5s
- [ ] Time to Interactive < 3s
- [ ] All components memoized appropriately

### Files Changed
- All component files (add memoization)
- `src/app/AppRouter.tsx` (lazy loading)
- `vite.config.ts` (optimization settings)
- `package.json` (build scripts)

---

## PR10: Testing Infrastructure

### Context
Establish comprehensive testing practices with proper coverage.

### Instructions
1. **Setup Testing Utils**
   ```typescript
   // src/test/test-utils.tsx
   export function renderWithProviders(
     ui: ReactElement,
     options?: RenderOptions
   ) {
     function Wrapper({ children }: { children: ReactNode }) {
       return (
         <QueryClientProvider client={queryClient}>
           <MemoryRouter>
             {children}
           </MemoryRouter>
         </QueryClientProvider>
       )
     }
     return render(ui, { wrapper: Wrapper, ...options })
   }
   ```

2. **Add Integration Tests**
   ```typescript
   // src/features/demo/DemoTab.integration.test.tsx
   describe('Demo Tab Integration', () => {
     it('connects to WebSocket and displays data', async () => {
       renderWithProviders(<DemoTab />)

       await waitFor(() => {
         expect(screen.getByText(/Connected/)).toBeInTheDocument()
       })

       // Start streaming
       await userEvent.click(screen.getByRole('button', { name: /Start/ }))

       // Verify data appears
       await waitFor(() => {
         expect(screen.getByTestId('oscilloscope-canvas')).toBeInTheDocument()
       })
     })
   })
   ```

3. **Setup E2E Tests with Playwright**
   ```typescript
   // e2e/app.spec.ts
   import { test, expect } from '@playwright/test'

   test('navigates through all tabs', async ({ page }) => {
     await page.goto('/')

     // Check Infrastructure tab
     await expect(page.locator('h3')).toContainText('Infrastructure')

     // Navigate to Planning
     await page.click('button:has-text("Planning")')
     await expect(page.locator('h3')).toContainText('Planning')
   })
   ```

4. **Add Coverage Requirements**
   ```json
   // vite.config.ts
   {
     test: {
       coverage: {
         reporter: ['text', 'lcov', 'html'],
         statements: 80,
         branches: 80,
         functions: 80,
         lines: 80
       }
     }
   }
   ```

### Success Criteria
- [ ] Test coverage > 80%
- [ ] All critical paths have integration tests
- [ ] E2E tests for main user flows
- [ ] Test utils established
- [ ] CI/CD updated with test requirements

### Files Changed
- `src/test/` (new test utilities)
- `e2e/` (new E2E tests)
- All component test files (improved coverage)
- `package.json` (test scripts)
- `.github/workflows/` (CI updates)

---

## PR11: Documentation with Storybook

### Context
Add comprehensive documentation for all components using Storybook.

### Instructions
1. **Install and Configure Storybook**
   ```bash
   npx storybook@latest init
   ```

2. **Create Stories for All Components**
   ```typescript
   // src/components/common/Button/Button.stories.tsx
   import type { Meta, StoryObj } from '@storybook/react'
   import { Button } from './Button'

   const meta = {
     title: 'Common/Button',
     component: Button,
     parameters: {
       layout: 'centered',
     },
     tags: ['autodocs'],
     argTypes: {
       variant: {
         control: 'select',
         options: ['primary', 'secondary', 'danger']
       }
     }
   } satisfies Meta<typeof Button>

   export default meta
   type Story = StoryObj<typeof meta>

   export const Primary: Story = {
     args: {
       variant: 'primary',
       children: 'Click me'
     }
   }

   export const AllVariants: Story = {
     render: () => (
       <div style={{ display: 'flex', gap: '1rem' }}>
         <Button variant="primary">Primary</Button>
         <Button variant="secondary">Secondary</Button>
         <Button variant="danger">Danger</Button>
       </div>
     )
   }
   ```

3. **Document Features**
   - Create stories for each tab
   - Show different states
   - Document props
   - Add usage examples

4. **Setup Chromatic (Optional)**
   - Visual regression testing
   - UI review process

### Success Criteria
- [ ] Storybook running with all components
- [ ] Stories for every component
- [ ] Documentation complete
- [ ] Interactive controls working
- [ ] Deployed to GitHub Pages

### Files Changed
- `.storybook/` (configuration)
- `**/*.stories.tsx` (new story files)
- `package.json` (storybook scripts)

---

## PR12: Developer Experience and Final Polish

### Context
Final PR to add developer tools and ensure excellent DX.

### Instructions
1. **Add Component Generator**
   ```bash
   # Create a plop generator
   npm install --save-dev plop
   ```

   ```javascript
   // plopfile.js
   module.exports = function (plop) {
     plop.setGenerator('component', {
       description: 'Create a new component',
       prompts: [{
         type: 'input',
         name: 'name',
         message: 'Component name?'
       }],
       actions: [
         {
           type: 'add',
           path: 'src/components/{{name}}/{{name}}.tsx',
           templateFile: 'templates/component.tsx.hbs'
         },
         // ... other files
       ]
     })
   }
   ```

2. **Add Pre-commit Hooks**
   ```json
   // .husky/pre-commit
   #!/bin/sh
   npm run validate
   ```

3. **Update Documentation**
   - Complete README.md
   - Add CONTRIBUTING.md
   - Document architecture decisions
   - Create onboarding guide

4. **Performance Audit**
   - Run Lighthouse
   - Check bundle size
   - Verify no regressions
   - Document metrics

5. **Accessibility Audit**
   - Run axe DevTools
   - Fix any issues
   - Add keyboard navigation
   - Test with screen reader

### Success Criteria
- [ ] Component generator working
- [ ] Pre-commit hooks configured
- [ ] All documentation complete
- [ ] Lighthouse score > 95
- [ ] Zero accessibility violations
- [ ] Bundle < 200KB gzipped
- [ ] README updated with new architecture

### Files Changed
- `plopfile.js` (generator config)
- `.husky/` (git hooks)
- `README.md` (updated documentation)
- `CONTRIBUTING.md` (new)
- `docs/` (architecture docs)

---

## Rollback Plan

If any PR causes issues:

1. **Immediate Rollback**
   ```bash
   git revert HEAD
   git push origin main
   ```

2. **Feature Flag Alternative**
   ```typescript
   const useNewArchitecture = process.env.REACT_APP_NEW_ARCH === 'true'

   export const Tab = useNewArchitecture ? NewTab : OldTab
   ```

3. **Gradual Migration**
   - Keep old components during transition
   - Run both in parallel if needed
   - A/B test changes

## Timeline Estimate

- **PR1-2**: 2 hours (Foundation)
- **PR3**: 2 hours (Common components)
- **PR4-6**: 3 hours (Feature extraction)
- **PR7-8**: 2 hours (App shell & styling)
- **PR9**: 1 hour (Performance)
- **PR10**: 2 hours (Testing)
- **PR11**: 1 hour (Storybook)
- **PR12**: 1 hour (Polish)

**Total**: ~14 hours of focused work

## Success Validation

After all PRs are complete:

1. **Technical Debt**: Reduced by 80%
2. **Code Quality**: All components < 200 lines
3. **Performance**: Lighthouse > 95
4. **Testing**: Coverage > 80%
5. **Documentation**: 100% in Storybook
6. **Developer Experience**: 10x improvement
7. **Maintainability**: Feature changes isolated
8. **Type Safety**: 100% TypeScript strict mode

The frontend will be transformed into a professional, maintainable React application that any developer would be proud to work on.
