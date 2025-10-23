import { ApiHealthBanner } from '@/components/api-health-banner';
import { HorizontalHeader } from '@/components/horizontal-header';
import { Logo } from '@/components/logo';
import { useSidebar } from '@/contexts/sidebar-context';
import { Paper, ScrollArea, Stack } from '@mantine/core';
import { Outlet } from 'react-router-dom';
import { Header } from '../header';
import { Sidebar } from '../sidebar';
import classes from './root.module.css';

export function DashboardLayout() {
  const { isCollapsed } = useSidebar();

  return (
    <div className={classes.root}>
      <HorizontalHeader />

      <Paper
        className={`${classes.sidebarWrapper} ${isCollapsed ? classes.collapsed : ''}`}
        withBorder
      >
        <div className={classes.logoWrapper}>
          <Stack gap={4} align="flex-start">
            <Logo
              height="3.5rem"
              style={{
                imageRendering: 'auto',
                filter: 'none',
              }}
            />
          </Stack>
        </div>
        <ScrollArea flex="1" px="md">
          <Sidebar />
        </ScrollArea>
      </Paper>

      <div className={`${classes.content} ${isCollapsed ? classes.expanded : ''}`}>
        <Header />
        <main className={classes.main}>
          <ApiHealthBanner />
          <Outlet />
        </main>
      </div>
    </div>
  );
}
