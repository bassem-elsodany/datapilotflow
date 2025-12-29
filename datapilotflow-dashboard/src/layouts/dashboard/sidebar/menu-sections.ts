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

interface MenuItem {
  header: string;
  section: {
    name: string;
    href: string;
    icon: ElementType;
    dropdownItems?: {
      name: string;
      href: string;
      badge?: string;
      dropdownItems?: {
        name: string;
        href: string;
        badge?: string;
      }[];
    }[];
  }[];
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
      },
      {
        name: 'Conversations',
        href: paths.dashboard.apps.conversations,
        icon: PiChatsDuotone,
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
      },
      {
        name: 'Tools',
        icon: PiGearSixDuotone,
        href: paths.dashboard.management.tools.list,
      },
      {
        name: 'Knowledge',
        icon: PiBrainDuotone,
        href: paths.dashboard.management.knowledge.root,
        dropdownItems: [
          {
            name: 'Configuration',
            href: paths.dashboard.management.knowledgeSources.configs,
            dropdownItems: [
              {
                name: 'Crawling Sources',
                href: paths.dashboard.management.knowledgeSources.configs,
              },
              {
                name: 'Jobs',
                href: paths.dashboard.management.knowledgeSources.jobs,
              },
            ],
          },
          {
            name: 'Monitoring',
            href: paths.dashboard.management.knowledge.status,
            dropdownItems: [
              {
                name: 'Job Status',
                href: paths.dashboard.management.knowledge.status,
              },
              {
                name: 'Vector Status',
                href: paths.dashboard.management.knowledge.vectorStatus,
              },
            ],
          },
        ],
      },
      {
        name: 'User Management',
        icon: PiUsersDuotone,
        href: paths.dashboard.management.users.root,
        dropdownItems: [
          {
            name: 'Users',
            href: paths.dashboard.management.users.list,
            badge: 'Admin',
          },
          {
            name: 'Roles',
            href: paths.dashboard.management.users.roles,
            badge: 'Admin',
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
