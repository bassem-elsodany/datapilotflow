import { ApiStatus } from '@/components/api-status';
import { ColorSchemeToggler } from '@/components/color-scheme-toggler';
import { Logo } from '@/components/logo';
import { SidebarToggleButton } from '@/components/sidebar-toggle-button';
import { StickyHeader } from '@/components/sticky-header';
import { Group, Stack, Text } from '@mantine/core';
import { Link } from 'react-router-dom';
import { CurrentUser } from './current-user';
import classes from './header.module.css';
import { Notifications } from './notifications';
import { SidebarButton } from './sidebar-button';

export function Header() {
  return (
    <StickyHeader className={classes.root}>
      <div className={classes.rightContent}>
        <div className={classes.sidebarButton}>
          <SidebarButton />
        </div>
        <SidebarToggleButton />
        <Stack gap={2} align="center" className={classes.logoContainer}>
          <Link to="/" className={classes.logo}>
            <Logo
              height="2.5rem"
              style={{
                imageRendering: 'auto',
                filter: 'none',
              }}
            />
          </Link>
          <Text size="xs" c="dimmed" className={classes.brandText}>
            dataPilotFlow
          </Text>
        </Stack>
      </div>

      <Group>
        <ApiStatus />
        <Notifications />
        <ColorSchemeToggler />
        <CurrentUser />
      </Group>
    </StickyHeader>
  );
}
