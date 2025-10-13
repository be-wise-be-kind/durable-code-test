/**
 * Purpose: Reusable feature card component for all tabs
 * Scope: Common component for displaying feature items with icon, title, description, and links
 * Overview: Standardized card component with theme-aware styling and badge variants
 * Dependencies: React, CSS Modules
 * Exports: FeatureCard component
 * Props/Interfaces: icon, title, description, linkText, linkHref, badge, onClick, className
 * Implementation: Shared component with consistent layout and badge system
 */

import type { ReactElement } from 'react';
import styles from './FeatureCard.module.css';
import { logger } from '../../../utils/logger';

export interface FeatureCardProps {
  icon: ReactElement;
  title: string;
  description: string;
  linkText: string;
  linkHref?: string;
  onClick?: () => void;
  className?: string;
}

/**
 * Validates that a URL is safe to navigate to
 * Only allows http: and https: protocols to prevent XSS attacks
 */
const isValidUrl = (url: string): boolean => {
  try {
    const parsed = new URL(url, window.location.origin);
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      return false;
    }
    return true;
  } catch {
    return false;
  }
};

export function FeatureCard({
  icon,
  title,
  description,
  linkText,
  linkHref,
  onClick,
  className = '',
}: FeatureCardProps): ReactElement {
  const handleClick = () => {
    if (onClick) {
      onClick();
    } else if (linkHref) {
      if (isValidUrl(linkHref)) {
        window.location.href = linkHref;
      } else {
        logger.error('Invalid or unsafe URL prevented:', linkHref);
      }
    }
  };

  return (
    <div
      className={`${styles.card} ${className}`}
      onClick={onClick ? handleClick : undefined}
    >
      <span className={styles.cardIcon}>{icon}</span>
      <h4 className="light-title-on-dark">{title}</h4>
      <p className="light-text-on-dark">{description}</p>
      {linkHref ? (
        <a href={linkHref} className={styles.cardLink}>
          {linkText} →
        </a>
      ) : (
        <button className={styles.cardLink} onClick={handleClick} type="button">
          {linkText} →
        </button>
      )}
    </div>
  );
}
