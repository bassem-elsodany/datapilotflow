import { NavLink as RouterLink, useLocation } from 'react-router-dom';
import { NavLink, Stack, Title, Divider } from '@mantine/core';
import { ApiStatus } from '@/components/api-status';
import { useApiHealth } from '@/hooks/use-api-health';
import { menu } from './menu-sections';
import classes from './sidebar.module.css';

export function Sidebar() {
  const { pathname } = useLocation();
  const { features } = useApiHealth();

  const isFeatureEnabledForPath = (href: string): boolean => {
    if (!href || typeof href !== 'string') return true;
    if (!Array.isArray(features)) return true;
    // Find matching feature by menu path
    const matched = features.find((f) => {
      const m = (f as any).menu as { path?: string; wildcard?: boolean } | undefined;
      if (!m || !m.path) return false;
      if (m.wildcard) {
        // Simple wildcard: treat '*' as any suffix
        const raw = m.path as string;
        const prefix = raw.endsWith('*') ? raw.slice(0, -1) : raw;
        return typeof prefix === 'string' && href.startsWith(prefix);
      }
      return href === m.path;
    });
    return matched ? Boolean((matched as any).enabled) : true;
  };

  return (
    <Stack gap="xl" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ flex: 1 }}>
        {menu.map((item, index) => (
          <div key={item.header}>
            {/* Add divider before each section except the first one */}
            {index > 0 && (
              <Divider 
                my="md" 
                mx="md" 
                color="gray.2" 
                style={{ opacity: 0.3 }}
              />
            )}
            
            <Title order={6} className={classes.sectionTitle}>
              {item.header}
            </Title>

            {item.section.map((subItem) => (
              !isFeatureEnabledForPath(subItem.href) ? null : (
              subItem.dropdownItems ? (
                <NavLink
                  variant="subtle"
                  key={subItem.name}
                  label={subItem.name}
                  childrenOffset={0}
                  className={classes.sectionLink}
                  active={pathname.includes(subItem.href)}
                  leftSection={subItem.icon && <subItem.icon />}
                >
                  {subItem.dropdownItems
                    ?.filter((dropdownItem) => isFeatureEnabledForPath(dropdownItem.href))
                    .map((dropdownItem) => (
                      dropdownItem.dropdownItems ? (
                        <NavLink
                          variant="subtle"
                          key={dropdownItem.name}
                          label={dropdownItem.name}
                          childrenOffset={0}
                          className={classes.sectionDropdownItemLink}
                          active={pathname.includes(dropdownItem.href)}
                          leftSection={<span className="dot" />}
                        >
                          {dropdownItem.dropdownItems
                            ?.filter((nestedItem) => isFeatureEnabledForPath(nestedItem.href))
                            .map((nestedItem) => (
                              <NavLink
                                variant="subtle"
                                component={RouterLink}
                                to={nestedItem.href}
                                key={nestedItem.name}
                                label={nestedItem.name}
                                active={pathname.includes(nestedItem.href)}
                                className={classes.nestedDropdownItemLink}
                                leftSection={<span className="dot" />}
                              />
                            ))}
                        </NavLink>
                      ) : (
                        <NavLink
                          variant="subtle"
                          component={RouterLink}
                          to={dropdownItem.href}
                          key={dropdownItem.name}
                          label={dropdownItem.name}
                          active={pathname.includes(dropdownItem.href)}
                          className={classes.sectionDropdownItemLink}
                          leftSection={<span className="dot" />}
                        />
                      )
                    ))}
                </NavLink>
              ) : (
                <NavLink
                  variant="subtle"
                  component={RouterLink}
                  to={subItem.href}
                  key={subItem.name}
                  label={subItem.name}
                  className={classes.sectionLink}
                  leftSection={subItem.icon && <subItem.icon />}
                />
              )
              )
            ))}
          </div>
        ))}
      </div>
      
      {/* API Status at bottom of sidebar */}
      <div style={{ marginTop: 'auto', paddingTop: '1rem' }}>
        <Divider mb="md" />
        <ApiStatus />
      </div>
    </Stack>
  );
}
