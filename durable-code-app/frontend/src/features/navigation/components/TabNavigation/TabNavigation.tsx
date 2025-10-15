/**
 * Purpose: Tab navigation component for main application
 * Scope: React component for rendering navigation tabs
 * Overview: Reusable navigation component with tab switching
 * Dependencies: React, common components
 * Exports: TabNavigation component
 * Props/Interfaces: NavigationProps - activeTab, onTabChange, tabs
 * Implementation: Renders tab navigation with active state management
 */

import type { ReactElement } from 'react';
import { Tab } from '../../../../components/common/Tab';
import { Icon } from '../../../../components/common/Icon';
import type { NavigationProps, TabName } from '../../types/navigation.types';
import styles from './TabNavigation.module.css';

export function TabNavigation({
  activeTab,
  onTabChange,
  tabs,
}: NavigationProps): ReactElement {
  return (
    <nav className={styles.navigation}>
      {(Object.keys(tabs) as TabName[]).map((tabName) => {
        const tab = tabs[tabName];

        return (
          <Tab
            key={tabName}
            isActive={activeTab === tabName}
            onClick={() => onTabChange(tabName)}
            variant="underline"
          >
            <Icon emoji={tab.icon} label={tab.title} />
            <span className={styles.tabTitle}>{tab.title}</span>
          </Tab>
        );
      })}
    </nav>
  );
}
