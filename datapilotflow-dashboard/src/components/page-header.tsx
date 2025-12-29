import { Anchor, Breadcrumbs, ElementProps, Group, GroupProps, Text, Title } from '@mantine/core';
import { ReactNode } from 'react';
import { NavLink } from 'react-router-dom';

interface PageHeaderProps
  extends Omit<GroupProps, 'title'>,
  ElementProps<'header', keyof GroupProps> {
  title: ReactNode;
  breadcrumbs?: { label: string; href?: string }[];
}

export function PageHeader({
  children,
  title,
  breadcrumbs,
  className,
  mb = 'lg',
  ...props
}: PageHeaderProps) {
  return (
    <Group component="header" justify="space-between" className={className} mb={mb} gap="md" {...props}>
      <div>
        <Title component="h2" order={4}>
          {title}
        </Title>

        {breadcrumbs && (
          <Breadcrumbs mt="xs">
            {breadcrumbs.map((breadcrumb) =>
              breadcrumb.href ? (
                <Anchor
                  fz="xs"
                  underline="never"
                  c="inherit"
                  component={NavLink}
                  key={breadcrumb.label}
                  to={breadcrumb.href}
                >
                  {breadcrumb.label}
                </Anchor>
              ) : (
                <Text key={breadcrumb.label} c="dimmed" fz="xs">
                  {breadcrumb.label}
                </Text>
              )
            )}
          </Breadcrumbs>
        )}
      </div>

      {children}
    </Group>
  );
}
