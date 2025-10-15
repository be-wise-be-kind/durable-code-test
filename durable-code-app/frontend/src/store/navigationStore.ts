import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export type TabName =
  | 'Repository'
  | 'Planning'
  | 'Building'
  | 'Quality Assurance'
  | 'Maintenance'
  | 'Demo'
  | 'Journey';

interface NavigationState {
  activeTab: TabName;
  activeSubTab: string | null;
  tabHistory: TabName[];
  isNavigating: boolean;
  setActiveTab: (tab: TabName) => void;
  setActiveSubTab: (subTabId: string | null) => void;
  navigateBack: () => void;
}

// Conditionally apply devtools middleware only in development
export const useNavigationStore = import.meta.env.DEV
  ? create<NavigationState>()(
      devtools(
        (set, get) => ({
          activeTab: 'Repository',
          activeSubTab: null,
          tabHistory: [],
          isNavigating: false,
          setActiveTab: (tab: TabName) => {
            const state = get();

            // Prevent duplicate navigation and race conditions
            if (state.activeTab === tab || state.isNavigating) {
              return;
            }

            // Atomic update with navigation lock
            set({
              activeTab: tab,
              activeSubTab: null,
              tabHistory: [...state.tabHistory, tab],
              isNavigating: true,
            });

            // Update browser history after state
            window.history.pushState(null, '', `#${tab}`);

            // Release navigation lock after microtask
            Promise.resolve().then(() => {
              set({ isNavigating: false });
            });
          },
          setActiveSubTab: (subTabId: string | null) => {
            const state = get();

            // Prevent race conditions
            if (state.isNavigating) {
              return;
            }

            set({
              activeSubTab: subTabId,
              isNavigating: true,
            });

            // Update browser history with sub-tab
            const hash = subTabId
              ? `#${state.activeTab}/${subTabId}`
              : `#${state.activeTab}`;
            window.history.pushState(null, '', hash);

            // Release navigation lock after microtask
            Promise.resolve().then(() => {
              set({ isNavigating: false });
            });
          },
          navigateBack: () => {
            const state = get();

            // Prevent navigation during active navigation
            if (state.isNavigating || state.tabHistory.length <= 1) {
              return;
            }

            const newHistory = [...state.tabHistory];
            newHistory.pop();
            const previousTab = newHistory[newHistory.length - 1] || 'Repository';

            // Atomic update with navigation lock
            set({
              activeTab: previousTab,
              tabHistory: newHistory,
              isNavigating: true,
            });

            // Update browser history after state
            window.history.pushState(null, '', `#${previousTab}`);

            // Release navigation lock after microtask
            Promise.resolve().then(() => {
              set({ isNavigating: false });
            });
          },
        }),
        { name: 'navigation-store' },
      ),
    )
  : create<NavigationState>()((set, get) => ({
      activeTab: 'Repository',
      activeSubTab: null,
      tabHistory: [],
      isNavigating: false,
      setActiveTab: (tab: TabName) => {
        const state = get();

        // Prevent duplicate navigation and race conditions
        if (state.activeTab === tab || state.isNavigating) {
          return;
        }

        // Atomic update with navigation lock
        set({
          activeTab: tab,
          activeSubTab: null,
          tabHistory: [...state.tabHistory, tab],
          isNavigating: true,
        });

        // Update browser history after state
        window.history.pushState(null, '', `#${tab}`);

        // Release navigation lock after microtask
        Promise.resolve().then(() => {
          set({ isNavigating: false });
        });
      },
      setActiveSubTab: (subTabId: string | null) => {
        const state = get();

        // Prevent race conditions
        if (state.isNavigating) {
          return;
        }

        set({
          activeSubTab: subTabId,
          isNavigating: true,
        });

        // Update browser history with sub-tab
        const hash = subTabId
          ? `#${state.activeTab}/${subTabId}`
          : `#${state.activeTab}`;
        window.history.pushState(null, '', hash);

        // Release navigation lock after microtask
        Promise.resolve().then(() => {
          set({ isNavigating: false });
        });
      },
      navigateBack: () => {
        const state = get();

        // Prevent navigation during active navigation
        if (state.isNavigating || state.tabHistory.length <= 1) {
          return;
        }

        const newHistory = [...state.tabHistory];
        newHistory.pop();
        const previousTab = newHistory[newHistory.length - 1] || 'Repository';

        // Atomic update with navigation lock
        set({
          activeTab: previousTab,
          tabHistory: newHistory,
          isNavigating: true,
        });

        // Update browser history after state
        window.history.pushState(null, '', `#${previousTab}`);

        // Release navigation lock after microtask
        Promise.resolve().then(() => {
          set({ isNavigating: false });
        });
      },
    }));
