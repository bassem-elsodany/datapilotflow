import { Link } from 'react-router-dom';
import { Group } from '@mantine/core';
import { ColorSchemeToggler } from '@/components/color-scheme-toggler';
import { Logo } from '@/components/logo';
import { StickyHeader } from '@/components/sticky-header';
import { SidebarButton } from './sidebar-button';
import classes from './header.module.css';

export function Header() {
  return (
    <StickyHeader className={classes.root}>
      <div className={classes.rightContent}>
        <SidebarButton />
        <Link to="/" className={classes.logo}>
          <Logo 
            height="1.25rem" 
            style={{
              filter: 'drop-shadow(0 1px 2px rgba(0, 0, 0, 0.1))',
            }}
          />
        </Link>
      </div>

      <Group>
        <ColorSchemeToggler />
      </Group>
    </StickyHeader>
  );
}
