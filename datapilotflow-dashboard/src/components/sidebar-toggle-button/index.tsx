import { useSidebar } from '@/contexts/sidebar-context';
import { ActionIcon, Tooltip } from '@mantine/core';
import { PiSidebarSimpleDuotone, PiSidebarSimpleFill } from 'react-icons/pi';
import classes from './sidebar-toggle-button.module.css';

export function SidebarToggleButton() {
  const { isCollapsed, toggleSidebar } = useSidebar();

  return (
    <Tooltip label={isCollapsed ? 'Show sidebar' : 'Hide sidebar'}>
      <ActionIcon
        variant="transparent"
        onClick={toggleSidebar}
        className={classes.toggleButton}
        size="lg"
      >
        {isCollapsed ? (
          <PiSidebarSimpleFill size="1.25rem" />
        ) : (
          <PiSidebarSimpleDuotone size="1.25rem" />
        )}
      </ActionIcon>
    </Tooltip>
  );
}
