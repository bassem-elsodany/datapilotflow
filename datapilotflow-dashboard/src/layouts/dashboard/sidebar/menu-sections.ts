import { paths } from '@/routes/paths';
import { ElementType } from 'react';
import {
  PiBrainDuotone,
  PiChatsDuotone,
  PiCpuDuotone,
  PiGearSixDuotone,
  PiStarDuotone,
  PiUsersDuotone
} from 'react-icons/pi';

interface NestedDropdownItem {
  name: string;
  href: string;
  badge?: string;
  permission?: string;
}

interface DropdownItem {
  name: string;
  href: string;
  badge?: string;
  permission?: string;
  dropdownItems?: NestedDropdownItem[];
}

interface SectionItem {
  name: string;
  href: string;
  icon: ElementType;
  permission?: string;
  dropdownItems?: DropdownItem[];
}

interface MenuItem {
  header: string;
  section: SectionItem[];
}

export const menu: MenuItem[] = [
  {
    header: 'Overview',
    section: [
      {
        name: 'Welcome',
        href: paths.dashboard.home,
        icon: PiStarDuotone,
      },
    ],
  },

  {
    header: 'Apps',
    section: [
      {
        name: 'Agents',
        href: paths.dashboard.apps.agents,
        icon: PiBrainDuotone,
        permission: 'conversation:read',
      },
      {
        name: 'Conversations',
        href: paths.dashboard.apps.conversations,
        icon: PiChatsDuotone,
        permission: 'conversation:read',
      },
    ],
  },

  {
    header: 'Management',
    section: [
      {
        name: 'Model Providers',
        icon: PiCpuDuotone,
        href: paths.dashboard.management.modelProviders.list,
        permission: 'models:read',
      },
      {
        name: 'Tools',
        icon: PiGearSixDuotone,
        href: paths.dashboard.management.tools.list,
        permission: 'tools:read',
      },
      {
        name: 'Knowledge',
        icon: PiBrainDuotone,
        href: paths.dashboard.management.knowledge.root,
        permission: 'knowledge:read',
        dropdownItems: [
          {
            name: 'Configuration',
            href: paths.dashboard.management.knowledgeSources.configs,
            permission: 'knowledge:read',
            dropdownItems: [
              {
                name: 'Crawling Sources',
                href: paths.dashboard.management.knowledgeSources.configs,
                permission: 'knowledge:read',
              },
              {
                name: 'Jobs',
                href: paths.dashboard.management.knowledgeSources.jobs,
                permission: 'knowledge:read',
              },
            ],
          },
          {
            name: 'Monitoring',
            href: paths.dashboard.management.knowledge.status,
            permission: 'knowledge:read',
            dropdownItems: [
              {
                name: 'Job Status',
                href: paths.dashboard.management.knowledge.status,
                permission: 'knowledge:read',
              },
              {
                name: 'Vector Status',
                href: paths.dashboard.management.knowledge.vectorStatus,
                permission: 'knowledge:read',
              },
            ],
          },
        ],
      },
      {
        name: 'User Management',
        icon: PiUsersDuotone,
        href: paths.dashboard.management.users.root,
        permission: 'user:manage',
        dropdownItems: [
          {
            name: 'Users',
            href: paths.dashboard.management.users.list,
            badge: 'Admin',
            permission: 'user:manage',
          },
          {
            name: 'Roles',
            href: paths.dashboard.management.users.roles,
            badge: 'Admin',
            permission: 'user:manage',
          },
          {
            name: 'My Profile',
            href: paths.dashboard.management.users.profile,
          },
        ],
      },
    ],
  },


];
