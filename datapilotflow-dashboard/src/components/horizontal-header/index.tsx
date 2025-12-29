import { Logo } from '@/components/logo';
import { useSidebar } from '@/contexts/sidebar-context';
import classes from './horizontal-header.module.css';

export function HorizontalHeader() {
  const { isCollapsed } = useSidebar();

  if (!isCollapsed) return null;

  return (
    <div className={classes.horizontalHeader}>
      <div className={classes.content}>
        <Logo
          height="4rem"
          className={classes.logo}
          style={{
            imageRendering: 'auto',
            filter: 'none',
            maxWidth: '300px',
            width: 'auto',
            height: '4rem',
          }}
        />
      </div>
    </div>
  );
}
